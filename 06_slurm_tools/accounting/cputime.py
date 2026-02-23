"""
SLURM billing base (Python 3.6) - dict dataset version.
Created by @nobuki on 2026-02-22.
Version 0.1.0 2026-02-22: Initial version.

Key points:
- sacct output is parsed into dict rows: {field: value, ...}
- dataset is also dict-based:
    dataset = {
        "parents": {jobid: parent_row_dict},
        "steps": {jobid: [step_row_dict, ...]},
        "step_sums": {jobid: {"TotalCPU_s":..., "UserCPU_s":..., "SystemCPU_s":...}},
        "final": {jobid: final_row_dict_with_seconds_and_billing_fields}
    }
- CPU aggregation policy:
    if any step rows exist for jobid -> use step sums only
    else -> use parent row CPU fields
- Interactive classification by SubmitLine: contains "--pty" or "salloc"
- Billing mode switchable by config
"""
from abc import ABC, abstractmethod
import re
import math
import logging
import subprocess
import sys
import json
from datetime import datetime, timedelta
import gc


# -----------------------------
# Config
# -----------------------------
class Config(object):
    # DEFAULT_STARTTIME = "2026-01-01"
    DEFAULT_SPAN = 90
    # DEFAULT_SPAN = 0
    SSH_HOST = "192.168.64.2"
    SSH_USER = "root"

    # Classification keywords
    INTERACTIVE_KEYWORDS = ["--pty", "salloc"]
    GPUS_KEYWORD = ["gpu", "gres/gpu"]
    UNKNOWN_AS_CPU_BILLING = True

    # Policy switches (easy to flip later)
    # USE_OCCUPIED_FOR_INTERACTIVE = True
    CLASSIFY_PRIORITY = ["interactive_gpu", "interactive", "gpu", "default"]
    BILL_METRIC_BY_CLASS = {
        "interactive": "elapsed",
        "interactive_gpu": "elapsed",
        "gpu": "elapsed",
        "default": "totalcpu",
    }

    #
    GPU_SM_TABLE = {
        "part2": 132,
    }

    SACCT_PATH = "/usr/bin/sacct"
    # log_level = logging.DEBUG
    log_level = logging.INFO


# -----------------------------
# Logger + trace formatting
# -----------------------------
def setup_logger(level):
    logger = logging.getLogger("slurm_billing")
    logger.setLevel(level)
    if not logger.handlers:
        h = logging.StreamHandler()
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        h.setFormatter(fmt)
        logger.addHandler(h)
    return logger


# -----------------------------
# Utilities
# -----------------------------

class SlurmTime(object):
    @staticmethod
    def to_seconds(t):
        if not t:
            return 0.0
        t = t.strip()
        if t == "Unknown":
            return 0.0
        t = t.replace(",", ".")
        days = 0
        if "-" in t:
            d, t = t.split("-", 1)
            try:
                days = int(d)
            except ValueError:
                days = 0
        parts = t.split(":")
        try:
            if len(parts) == 3:
                h = int(parts[0]); m = int(parts[1]); s = float(parts[2])
            elif len(parts) == 2:
                h = 0; m = int(parts[0]); s = float(parts[1])
            elif len(parts) == 1:
                h = 0; m = 0; s = float(parts[0])
            else:
                return 0.0
        except ValueError:
            return 0.0
        return days * 86400.0 + h * 3600.0 + m * 60.0 + s


# -----------------------------
# sacct access -> dict rows
# -----------------------------
class ISchema(ABC):
    @abstractmethod
    def format_arg(cls):
        pass

    def parse_line(self, line):
        pass


class ISacctClientBase(ABC):
    def __init__(self, sacct_path, logger, schema:ISchema, days_ago=90,
                 ssh_host=None, ssh_user=None):
        self.sacct_path = sacct_path
        self.log = logger
        self.schema = schema
        self.days_ago = int(days_ago)
        self.ssh_host = ssh_host
        self.ssh_user = ssh_user

    @staticmethod
    def _parse_endtime(endtime):
        """
        endtime:
          - "now"
          - None
          - "YYYY-MM-DD"
          - "YYYY-MM-DDTHH:MM"
        """
        if endtime is None or endtime == "now":
            return datetime.now()

        # 日付だけ
        try:
            return datetime.strptime(endtime, "%Y-%m-%d")
        except ValueError:
            pass

        # 日時（分まで）
        try:
            return datetime.strptime(endtime, "%Y-%m-%dT%H:%M")
        except ValueError:
            raise ValueError("Unsupported endtime format: %s" % endtime)

    def calc_range(self, endtime=None):
        """
        return (start_str, end_str) in "YYYY-MM-DDTHH:MM"
        days_ago:
          0 => 指定日の 00:00 - 23:59:59（= 1日分）
          N => 指定日を含めて N+1日分（例: N=1 なら前日+当日の2日分）
        """
        end_dt = self._parse_endtime(endtime)

        # 指定日の範囲に丸める
        day_start = end_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = end_dt.replace(hour=23, minute=59, second=59, microsecond=0)

        if self.days_ago == 0:
            start_dt = day_start
            end_dt2 = day_end
        else:
            # 例: days_ago=1 なら「前日0時」から
            start_dt = day_start - timedelta(days=self.days_ago)
            end_dt2 = day_end

        return (
            start_dt.strftime("%Y-%m-%dT%H:%M"),
            end_dt2.strftime("%Y-%m-%dT%H:%M"),
        )

    @abstractmethod
    def fetch_rows(self, endtime="now"):
        pass


class IDatasetBuilderBase(ABC):
    def __init__(self, logger):
        self.log = logger

    @abstractmethod
    def build(self, rows):
        pass


class SacctCpuSchema(ISchema):
    def __init__(self, fields=None):
        self.FIELDS = fields or [
            "JobID",
            "Elapsed",
            "CPUTime",
            "TotalCPU",
            "UserCPU",
            "SystemCPU",
            "State",
            "SubmitLine",
            "JobName",
            "User",
            "Partition",
            "NCPUS",
            "AllocTRES",
            "NodeList",
            "Start",
            "End",
        ]

    def format_arg(self):
        return ",".join(self.FIELDS)

    def parse_line(self, line):
        cols = line.split("|")
        if len(cols) < len(self.FIELDS):
            cols = cols + [""] * (len(self.FIELDS) - len(cols))
        row = {}
        for i, k in enumerate(self.FIELDS):
            row[k] = cols[i] if i < len(cols) else ""
        return row


class SacctClient(ISacctClientBase):
    def fetch_rows(self, endtime="now"):
        # starttime = self.calc_starttime(endtime)
        starttime, endtime2 = self.calc_range(endtime=endtime)
        self.log.debug({"starttime": starttime, "endtime": endtime2})
        cmd = []
        if self.ssh_host:
            user_at = "{}@{}".format(self.ssh_user, self.ssh_host) if self.ssh_user else self.ssh_host
            cmd += ["ssh", user_at]

        cmd += [
            self.sacct_path,
            "--starttime", starttime,
            "--endtime", endtime2,
            "--format", self.schema.format_arg(),
            "--parsable2",
            "-n",
        ]

        self.log.debug("Running sacct: %s", " ".join(cmd))
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if p.returncode != 0:
            self.log.info("sacct failed rc=%s stderr=%s", p.returncode, p.stderr.strip())
            raise RuntimeError("sacct failed")
        raw_lines = [ln for ln in p.stdout.splitlines() if ln.strip()]

        # debug: raw all
        if self.log.isEnabledFor(logging.DEBUG):
            self.log.debug("Query range: %s -> %s", starttime, endtime)
            self.log.debug("RAW_ALL_BEGIN total=%d", len(raw_lines))
            for ln in raw_lines:
                self.log.debug("RAW|%s", ln)
            self.log.debug("RAW_ALL_END")

        return [self.schema.parse_line(ln) for ln in raw_lines]


class SacctParserEnd(object):
    """sacctのEnd/Startをパースして、指定日の範囲内か判定するユーティリティクラス（必要に応じて拡張）"""
    @staticmethod
    def end_in_range(row, day_start, day_end, log=None):
        def parse_slurm_dt(s):
            # sacct の End/Start: "YYYY-MM-DDTHH:MM:SS"
            return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")

        end_s = (row.get("End") or "").strip()
        if not end_s:
            return False
        try:
            end_dt = parse_slurm_dt(end_s)
        except ValueError:
            if log:
                log.info("Bad End format: End=%r JobID=%r", end_s, row.get("JobID"))
            return False
        return day_start <= end_dt <= day_end


class DatasetCpuBuilder(IDatasetBuilderBase):
    STEP_RE = re.compile(r"^(\d+)\.(.+)$")
    JOB_RE = re.compile(r"^\d+$")

    def build(self, rows):
        ds = {"parents": {}, "steps": {}}
        for r in rows:
            jid = (r.get("JobID") or "").strip()
            if not jid:
                continue
            m = self.STEP_RE.match(jid)
            if m:
                parent = m.group(1)
                ds["steps"].setdefault(parent, []).append(r)
                continue
            if self.JOB_RE.match(jid):
                ds["parents"][jid] = r
                continue
        for jid in ds["parents"]:
            ds["steps"].setdefault(jid, [])

        self.log.debug("Dataset built: parents=%d step_parents=%d", len(ds["parents"]), len(ds["steps"]))
        return ds


# -----------------------------
# Template Method: TimeCalculator
# -----------------------------
class KeywordClassifier(object):
    def __init__(self, keywords):
        self.keywords = [k.lower() for k in keywords]

    def matches(self, text):
        if not text:
            return False
        s = text.lower()
        return any(k in s for k in self.keywords)


class CpuStepSummer(object):
    """単純責務：stepのCPUを合算する（ここを差し替えるのも簡単）"""
    @staticmethod
    def sum_steps(step_rows):
        total = 0.0
        user = 0.0
        sysc = 0.0
        for r in step_rows:
            total += SlurmTime.to_seconds(r.get("TotalCPU", ""))
            user += SlurmTime.to_seconds(r.get("UserCPU", ""))
            sysc += SlurmTime.to_seconds(r.get("SystemCPU", ""))
        return {"TotalCPU_s": total, "UserCPU_s": user, "SystemCPU_s": sysc}


class ICalculatorBase(ABC):
    """
        Template Method:
          calculate(jobid, parent_row, step_rows, ctx) -> (final_row_dict, trace_dict)
          context: TotalCPU policy, Interactive classification, Billing mode, etc.
        """
    NAME = "base"

    def __init__(self, logger):
        self.log = logger

    @abstractmethod
    def calculate(self, jobid, parent_row, step_rows):
        pass

    @abstractmethod
    def select_cpu_source(self, parent_row, step_rows):
        """
        Default: steps exist => sum steps, else parent.
        Return: string: "steps" or "parent", and cpu_sums dict if steps, or parent cpu fields if parent.
        """
        pass

    @abstractmethod
    def compute_raw(self, jobid, parent_row, cpu_sums):
        pass

    @abstractmethod
    def build_final_row(self, parent_row, cpu_sums):
        pass


class TimeCalculator(ICalculatorBase):
    NAME = "execute_time_total"
    def __init__(self, logger):
        super().__init__(logger)
        self.tools = SlurmTime()
        # shared context (inject)
        self.ctx = {
            "interactive_classifier": KeywordClassifier(Config.INTERACTIVE_KEYWORDS),
            "gpu_classifier": KeywordClassifier(Config.GPUS_KEYWORD),
            "cpu_summer": CpuStepSummer(),
        }

    @staticmethod
    def parse_gpu_count(alloc_tres):
        if not alloc_tres:
            return 0
        alloc_tres = alloc_tres.strip().lower()
        gpu_count = 0
        for part in alloc_tres.split(","):
            if part.startswith("gpu=") or part.startswith("gres/gpu="):
                try:
                    gpu_count += int(part.split("=", 1)[1])
                except ValueError:
                    pass
        return gpu_count

    @staticmethod
    def uid_to_user(uid):
        # 例: "1001(jdoe)" -> "jdoe"
        if not uid:
            return ""
        return uid

    def calculate(self, jobid, parent_row, step_rows):
        cpu_source, cpu_sums = self.select_cpu_source(parent_row, step_rows)
        raw_seconds, metric, chosen_class, ngpus, reason = self.compute_raw(jobid, parent_row, cpu_sums)
        final_row = self.build_final_row(
            parent_row=parent_row,
            cpu_sums=cpu_sums,
            raw=raw_seconds,
            bill_mode=metric,
            chosen_class=chosen_class,
            ngpus=ngpus,
            reason=reason,
        )
        return final_row

    def select_cpu_source(self, parent_row, step_rows):
        """
        Default: steps exist => sum steps, else parent.
        """
        if step_rows:
            cpu_sums = self.ctx["cpu_summer"].sum_steps(step_rows)
            return "steps", cpu_sums

        cpu_sums = {
            "TotalCPU_s": self.tools.to_seconds(parent_row.get("TotalCPU", "")),
            "UserCPU_s": self.tools.to_seconds(parent_row.get("UserCPU", "")),
            "SystemCPU_s": self.tools.to_seconds(parent_row.get("SystemCPU", "")),
        }
        return "parent", cpu_sums

    def compute_raw(self, jobid, parent_row, cpu_sums):
        # Classification by SubmitLine and AllocTRES
        submit = (parent_row.get("SubmitLine") or "").strip()
        interactive = bool(self.ctx["interactive_classifier"].matches(submit))

        alloc_tres = (parent_row.get("AllocTRES") or "").strip()
        gpu_job = bool(self.ctx["gpu_classifier"].matches(alloc_tres))

        # debug print
        self.log.debug({"alloc_tres": alloc_tres, "gpu_job": gpu_job, "interactive": interactive})

        # num of CPUs/GPUs to consider for elapsed-based billing (例: 2 GPUsなら実時間の2倍にする)
        elapsed_counter = {
            "ncpus": int(parent_row.get("NCPUS") or 1),
            "ngpus": self.parse_gpu_count(alloc_tres)  # gres/gpu=2 を 2
        }

        # 候補値（秒）
        candidates = {
            "totalcpu": float(cpu_sums.get("TotalCPU_s") or 0.0),  # step優先で作った値
            "elapsed": self.tools.to_seconds(parent_row.get("Elapsed", "")),  # 将来必要なら
        }

        # どのクラスに該当したか
        classes = {
            "interactive": interactive,
            "gpu": gpu_job,
            "default": True,
        }

        # 優先順位に従って最初に該当したクラスを採用
        chosen_class = None
        for c in Config.CLASSIFY_PRIORITY:
            if classes.get(c):
                chosen_class = c
                break

        metric = Config.BILL_METRIC_BY_CLASS.get(
            chosen_class, "totalcpu")

        if metric not in candidates:
            # 設定ミスを早期に検知（課金系はフェイルファスト推奨）
            raise ValueError("Unknown metric '{}' for class '{}'".format(metric, chosen_class))

        raw_seconds = candidates[metric]
        if metric == "elapsed":
            # Elapsedは実時間なので倍率が必要。
            # ポリシー：GPUが割り当てられているジョブは常にGPU数で積算（interactiveでも同じ）
            mult = elapsed_counter["ngpus"] if elapsed_counter["ngpus"] > 0 else elapsed_counter["ncpus"]
            raw_seconds *= max(1, mult)

        # trace 用（ログに出すならここを返す/保存）
        reason = "class={} metric={} interactive={} gpu={}".format(
            chosen_class, metric, interactive, gpu_job
        )

        return raw_seconds, metric, chosen_class, elapsed_counter['ngpus'], reason

    def build_final_row(
            self, parent_row, cpu_sums, raw=None,
            bill_mode=None, chosen_class=None, ngpus=None, reason=None):
        # dict dataset: keep meta + seconds + decision
        final = {}
        fields = [
            "JobID",
            "User",
            "JobName",
            "Partition",
            "NCPUS",
            "NodeList",
            "AllocTRES",
            "Elapsed",
            "CPUTime",
            "TotalCPU",
            "Start",
            "End",
            "State",
            "SubmitLine"]
        for f in fields:
            if f == "User":
                final[f] = self.uid_to_user(parent_row.get(f, ""))
            else:
                final[f] = parent_row.get(f, "")
        final.update(cpu_sums)
        final.update({
            "Elapsed_s": self.tools.to_seconds(parent_row.get("Elapsed", "")),
            "CPUTime_s": self.tools.to_seconds(parent_row.get("CPUTime", "")),
            "NGPUs": ngpus,
            "BillMode": bill_mode,
            "BillSeconds_raw": raw,
            "chosen_class": chosen_class,
            "DecisionNote": reason,
        })
        return final


# -----------------------------
# Orchestrator (pipeline)
# -----------------------------
class BillingEngine(object):
    def __init__(self, logger, calculator:ICalculatorBase):
        self.log = logger
        self.calculator = calculator

    def process(self, dataset):
        final = {}
        for jobid, parent_row in dataset["parents"].items():
            step_rows = dataset["steps"].get(jobid, [])
            final_row = self.calculator.calculate(jobid, parent_row, step_rows)
            final[jobid] = final_row

        # dataset["final"] = final
        return final


# -----------------------------
# Reporter (minimal)
# -----------------------------
class IReporterBase(ABC):
    def __init__(self, logger):
        self.log = logger

    @abstractmethod
    def print_table(self, final_map):
        pass


class BillReporter(IReporterBase):
    def print_table(self, final_map):
        for jid in sorted(final_map.keys(), key=lambda x: int(x)):
            r = final_map[jid]

            partition = r.get("Partition", "")
            nums = int(r.get("NGPUs", ""))
            elapsed = r.get("Elapsed_s", 0.0)
            bill_seconds = r.get("BillSeconds_raw", 0.0)
            sm = int(Config.GPU_SM_TABLE[partition]) if partition in Config.GPU_SM_TABLE else 0

            self.log.debug({"Partition": partition})
            self.log.debug({'NGPUs': nums})
            self.log.debug({"Elapsed": elapsed})
            self.log.debug({'BillSeconds_raw': bill_seconds})
            self.log.debug({"GPU SM": sm})

            if nums == 0:
                # CPU
                nums = r.get("NCPUS") or 0  # NCPUS
                nums = int(nums)
                self.log.debug({'NCPUS': nums})
            else:
                # GPU
                # GPUジョブのプロセス数はSMを積算する（例: 2 GPU x 132 SM = 264 NCPUS相当）
                nums *= sm
                bill_seconds *= sm
                self.log.debug({'GPU processes(GPUs * SM)': nums})# Partに応じたGPUあたりのNCPUS換算
                self.log.debug({'GPU bill seconds(Elapsed * NGPUs * SM)': bill_seconds})

            if bill_seconds > 0:
                etc = 1.0
            else:
                etc = 0.0

            row = [
                partition,  # Part
                (r.get("User", "") or ""),  # User
                r.get("Start", ""),  # Start
                r.get("End", ""),  # End
                str(nums),  # NCPUS or GPU換算NCPUS
                bill_seconds,  # Bill(raw)
                etc,
            ]
            print(",".join(str(x) for x in row))


class DebugReporter(IReporterBase):
    def print_table(self, final_map):
        header = [
            "JobID",
            "User",
            "JobName",
            "Part",
            "NCPUS",
            "NGPUS",
            # "Start",
            "End",
            "Elapsed",
            # "CPUTime",
            "TotalCPU",
            "Elapsed(s)",
            "CPUTime(s)",
            "TotalCPU(s)",
            "BillMode",
            "Type",
            "Bill(raw)",
        ]
        fmt = (
            "{:<6} "  # JobID
            "{:<7} "  # User
            "{:<6} "  # JobName
            "{:<8} "  # Part
            "{:>5} "  # NCPUS
            "{:>5} "  # NGPUS
            # "{:<19} "  # Start
            "{:<19} "  # End
            "{:>10} "  # Elapsed
            # "{:>10} "  # CPUTime
            "{:>10} "  # TotalCPU
            "{:>11} "  # Elapsed(s)
            "{:>11} "  # CPUTime(s)
            "{:>12} "  # TotalCPU(s)
            "{:<10} "  # BillMode
            "{:<11} "  # Type
            "{:>12}"  # Bill(raw)
        )
        print(fmt.format(*header))

        # widths = [8, 10, 12, 8, 6, 6, 19, 19, 10, 10, 10, 11, 11, 12, 10, 12]
        widths = [6, 7, 6, 8, 5, 5, 19, 10, 10, 11, 11, 12, 10, 11, 12]
        sep = 1  # 各列の後ろスペース
        total_width = sum(widths) + sep * (len(widths) - 1)

        print("-" * total_width)

        for jid in sorted(final_map.keys(), key=lambda x: int(x)):
            r = final_map[jid]
            row = [
                str(r.get("JobID", jid)),  # JobID
                (r.get("User", "") or "")[:10],  # User
                (r.get("JobName", "") or "")[:12],  # JobName
                (r.get("Partition", "") or "")[:8],  # Part
                str(r.get("NCPUS", "")),  # NCPUS
                str(r.get("NGPUs", "")),  # NGPUS
                # r.get("Start", ""),  # Start
                r.get("End", ""),  # End
                r.get("Elapsed", ""),  # Elapsed
                # r.get("CPUTime", ""),  # CPUTime
                r.get("TotalCPU", ""),  # TotalCPU
                "{:.1f}".format(r.get("Elapsed_s", 0.0)),  # Elapsed(s)
                "{:.1f}".format(r.get("CPUTime_s", 0.0)),  # CPUTime(s)
                "{:.3f}".format(r.get("TotalCPU_s", 0.0)),  # TotalCPU(s)
                r.get("BillMode", ""),  # BillMode
                r.get("chosen_class", ""), # Type
                "{:.3f}".format(r.get("BillSeconds_raw", 0.0)),  # Bill(raw)
            ]
            print(fmt.format(*row))


class App(object):
    def __init__(self, target_day=None):
        self.rows = None
        self.rows_end = None
        self.dataset = None
        self.bull_datasets = None
        self.logger = setup_logger(Config.log_level)
        self.target_day = target_day

    def run(self):
        day_start = datetime.strptime(self.target_day, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = datetime.strptime(self.target_day, "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=0)

        cpu_schema = SacctCpuSchema()
        client = SacctClient(
            sacct_path=Config.SACCT_PATH,
            logger=self.logger,
            schema=cpu_schema,
            days_ago=Config.DEFAULT_SPAN,
            ssh_host=Config.SSH_HOST,
            ssh_user=Config.SSH_USER,)
        calculator = TimeCalculator(logger=self.logger)
        engine = BillingEngine(logger=self.logger, calculator=calculator)

        self.rows = client.fetch_rows(endtime=self.target_day)
        # まず全件で dataset を作る（親とstepを確保）
        ds_all = DatasetCpuBuilder(logger=self.logger).build(self.rows)

        # 親だけ End でフィルタして課金対象の JobID を決める
        target_ids = []
        for jid, parent_row in ds_all["parents"].items():
            if SacctParserEnd.end_in_range(parent_row, day_start, day_end, log=self.logger):
                target_ids.append(jid)

        # 対象 JobID の親＋stepだけ残した dataset を作る
        ds = {"parents": {}, "steps": {}}
        for jid in target_ids:
            if jid in ds_all["parents"]:
                ds["parents"][jid] = ds_all["parents"][jid]
            # stepは End を見ずに丸ごと同梱（無ければ空配列）
            ds["steps"][jid] = ds_all["steps"].get(jid, [])

        self.dataset = ds

        # デバッグ表示（対象ジョブだけ）
        self.logger.debug(json.dumps(self.dataset, indent=2, ensure_ascii=False))

        self.bull_datasets = engine.process(self.dataset)

    def debug_print(self):
        print('')
        self.logger.debug(json.dumps(self.bull_datasets, indent=2, ensure_ascii=False))
        reporter = DebugReporter(logger=self.logger)
        reporter.print_table(self.bull_datasets)

    def print(self):
        reporter = BillReporter(logger=self.logger)
        reporter.print_table(self.bull_datasets)


# -----------------------------
# CLI / main
# -----------------------------
def parse_args(argv):
    # today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    target = yesterday
    log_level = logging.WARNING
    debug = False
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--debug":
            log_level = logging.DEBUG
            debug = True
            i += 1
            continue
        if a == "--info":
            log_level = logging.INFO
            i += 1
            continue
        target = a
        i += 1
    return target, log_level, debug


def main(argv=None):
    target, log_level, debug = parse_args(argv)
    Config.log_level = log_level
    app = App(target)
    app.run()
    if debug:
        app.debug_print()
    #results
    app.print()

if __name__ == "__main__":
    main(sys.argv)

    gc.collect()


