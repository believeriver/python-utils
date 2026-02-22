import re
import math
import logging
import subprocess
import sys


# -----------------------------
# Config
# -----------------------------
class Config(object):
    DEFAULT_STARTTIME = "2026-01-01"

    INTERACTIVE_KEYWORDS = ["--pty", "salloc"]
    UNKNOWN_AS_CPU_BILLING = True

    # Policy switches (easy to flip later)
    USE_OCCUPIED_FOR_INTERACTIVE = True

    # Rounding
    ROUND_UNIT_SECONDS = 60
    ROUND_MODE = "ceil"
    MIN_BILLABLE_SECONDS = 0

    SACCT_PATH = "sacct"


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


class TracePrinter(object):
    """
    “見づらい”問題は、loggerに全文を垂れ流すのではなく、
    trace(dict)を人間が追える形に整形して出すのがコツです。
    """
    @staticmethod
    def one_line(trace):
        # 必要なキーだけを抜いて短く表示（あとからいくらでも変えられる）
        parts = []
        parts.append("jobid={}".format(trace.get("jobid")))
        parts.append("calc={}".format(trace.get("calculator")))
        parts.append("cpu_source={}".format(trace.get("cpu_source")))
        parts.append("bill_mode={}".format(trace.get("bill_mode")))
        parts.append("raw={:.3f}".format(trace.get("raw_seconds", 0.0)))
        parts.append("rounded={:.3f}".format(trace.get("rounded_seconds", 0.0)))
        parts.append("interactive={}".format(trace.get("interactive")))
        parts.append("reason={}".format(trace.get("reason")))
        return "TRACE " + " ".join(parts)


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


class RoundingPolicy(object):
    def __init__(self, unit_seconds, mode, min_seconds=0):
        self.unit = float(unit_seconds) if unit_seconds and unit_seconds > 0 else 0.0
        self.mode = (mode or "none").lower()
        self.min_seconds = float(min_seconds) if min_seconds and min_seconds > 0 else 0.0

    def apply(self, seconds):
        if seconds < 0:
            seconds = 0.0
        if self.min_seconds > 0 and 0 < seconds < self.min_seconds:
            seconds = self.min_seconds
        if self.mode == "none" or self.unit == 0.0:
            return seconds

        q = seconds / self.unit
        if self.mode == "ceil":
            return math.ceil(q) * self.unit
        if self.mode == "floor":
            return math.floor(q) * self.unit
        if self.mode == "round":
            return math.floor(q + 0.5) * self.unit
        return seconds


# -----------------------------
# sacct access -> dict rows
# -----------------------------
class SacctSchema(object):
    FIELDS = [
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
        "End",
    ]

    @classmethod
    def format_arg(cls):
        return ",".join(cls.FIELDS)

    @classmethod
    def parse_line(cls, line):
        cols = line.split("|")
        if len(cols) < len(cls.FIELDS):
            cols = cols + [""] * (len(cls.FIELDS) - len(cols))
        row = {}
        for i, k in enumerate(cls.FIELDS):
            row[k] = cols[i] if i < len(cols) else ""
        return row


class SacctClient(object):
    def __init__(self, sacct_path, logger):
        self.sacct_path = sacct_path
        self.log = logger

    def fetch_rows(self, starttime, endtime="now"):
        cmd = [
            "ssh",
            "root@192.168.64.2",
            self.sacct_path,
            "--starttime", starttime,
            "--endtime", endtime,
            "--format", SacctSchema.format_arg(),
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
            self.log.debug("RAW_ALL_BEGIN total=%d", len(raw_lines))
            for ln in raw_lines:
                self.log.debug("RAW|%s", ln)
            self.log.debug("RAW_ALL_END")
        return [SacctSchema.parse_line(ln) for ln in raw_lines]


class DatasetBuilder(object):
    STEP_RE = re.compile(r"^(\d+)\.(.+)$")
    JOB_RE = re.compile(r"^\d+$")

    def __init__(self, logger):
        self.log = logger

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
        self.log.debug("Dataset built: parents=%d step_parents=%d", len(ds["parents"]), len(ds["steps"]))
        return ds


# -----------------------------
# Template Method: Calculator
# -----------------------------
class CalculatorBase(object):
    """
    Template Method:
      calculate(jobid, parent_row, step_rows, ctx) -> (final_row_dict, trace_dict)
    """
    NAME = "base"

    def __init__(self, rounding_policy, cfg):
        self.rounding = rounding_policy
        self.cfg = cfg

    def calculate(self, jobid, parent_row, step_rows, ctx):
        cpu_source, cpu_sums = self.select_cpu_source(jobid, parent_row, step_rows, ctx)
        raw_seconds, bill_mode, reason, interactive = self.compute_raw(jobid, parent_row, cpu_sums, ctx)
        rounded = self.rounding.apply(raw_seconds)

        final = self.build_final_row(jobid, parent_row, cpu_sums, raw_seconds, rounded, bill_mode, interactive, reason)

        trace = {
            "jobid": jobid,
            "calculator": self.NAME,
            "cpu_source": cpu_source,
            "bill_mode": bill_mode,
            "raw_seconds": raw_seconds,
            "rounded_seconds": rounded,
            "interactive": interactive,
            "reason": reason,

            # raw strings for audit / conversion check
            "elapsed_raw": parent_row.get("Elapsed", ""),
            "cputime_raw": parent_row.get("CPUTime", ""),
            "totalcpu_raw_parent": parent_row.get("TotalCPU", ""),
            "submitline": (parent_row.get("SubmitLine") or "")[:200],
        }

        return final, trace

    # ---- overridable hooks ----
    def select_cpu_source(self, jobid, parent_row, step_rows, ctx):
        """
        Default: steps exist => sum steps, else parent.
        """
        if step_rows:
            cpu_sums = ctx["cpu_summer"].sum_steps(step_rows)
            return "steps", cpu_sums

        cpu_sums = {
            "TotalCPU_s": SlurmTime.to_seconds(parent_row.get("TotalCPU", "")),
            "UserCPU_s": SlurmTime.to_seconds(parent_row.get("UserCPU", "")),
            "SystemCPU_s": SlurmTime.to_seconds(parent_row.get("SystemCPU", "")),
        }
        return "parent", cpu_sums

    def compute_raw(self, jobid, parent_row, cpu_sums, ctx):
        raise NotImplementedError

    def build_final_row(self, jobid, parent_row, cpu_sums, raw, rounded, bill_mode, interactive, reason):
        # dict dataset: keep meta + seconds + decision
        final = {}
        for k in ["JobID", "User", "JobName", "Partition", "NCPUS", "NodeList", "AllocTRES", "End", "State", "SubmitLine"]:
            final[k] = parent_row.get(k, "")
        final.update(cpu_sums)
        final.update({
            "Elapsed_s": SlurmTime.to_seconds(parent_row.get("Elapsed", "")),
            "CPUTime_s": SlurmTime.to_seconds(parent_row.get("CPUTime", "")),
            "BillMode": bill_mode,
            "BillSeconds_raw": raw,
            "BillSeconds_rounded": rounded,
            "Interactive": interactive,
            "DecisionNote": reason,
        })
        return final


class CpuStepSummer(object):
    """単純責務：stepのCPUを合算する（ここを差し替えるのも簡単）"""
    def sum_steps(self, step_rows):
        total = 0.0
        user = 0.0
        sysc = 0.0
        for r in step_rows:
            total += SlurmTime.to_seconds(r.get("TotalCPU", ""))
            user += SlurmTime.to_seconds(r.get("UserCPU", ""))
            sysc += SlurmTime.to_seconds(r.get("SystemCPU", ""))
        return {"TotalCPU_s": total, "UserCPU_s": user, "SystemCPU_s": sysc}


class CpuCalculator(CalculatorBase):
    """
    CPU課金の基本実装。
    - interactive判定（SubmitLine）を行い、方針により occupied(=CPUTime) または cpu(=TotalCPU) を選ぶ
    """
    NAME = "cpu"

    def compute_raw(self, jobid, parent_row, cpu_sums, ctx):
        submit = (parent_row.get("SubmitLine") or "").strip()
        interactive = ctx["classifier"].is_interactive(submit)

        totalcpu_s = cpu_sums["TotalCPU_s"]
        cputime_s = SlurmTime.to_seconds(parent_row.get("CPUTime", ""))

        if interactive is True and self.cfg.USE_OCCUPIED_FOR_INTERACTIVE:
            return cputime_s, "occupied", "interactive -> CPUTime", True
        if interactive is True and not self.cfg.USE_OCCUPIED_FOR_INTERACTIVE:
            return totalcpu_s, "cpu", "interactive -> TotalCPU", True
        if interactive is False:
            return totalcpu_s, "cpu", "batch -> TotalCPU", False

        # unknown
        if self.cfg.UNKNOWN_AS_CPU_BILLING:
            return totalcpu_s, "cpu", "SubmitLine missing -> safe TotalCPU", None
        return cputime_s, "occupied", "SubmitLine missing -> occupied", None


class InteractiveClassifier(object):
    def __init__(self, keywords):
        self.keywords = [k.lower() for k in keywords]

    def is_interactive(self, submitline):
        if not submitline:
            return None
        s = submitline.lower()
        for k in self.keywords:
            if k in s:
                return True
        return False


# -----------------------------
# Abstract Factory: choose calculator
# -----------------------------
class CalculatorFactory(object):
    """
    将来：
      - GPUあり -> GpuCalculator
      - GPUなし -> CpuCalculator
      - 特定Partition -> SpecialCalculator
    等へ拡張しやすい。
    """
    def __init__(self, cfg, rounding_policy):
        self.cfg = cfg
        self.rounding = rounding_policy

    def create(self, parent_row):
        # 現時点はCPUのみ。GPU対応時にここが伸びる。
        return CpuCalculator(self.rounding, self.cfg)


# -----------------------------
# Orchestrator (pipeline)
# -----------------------------
class BillingEngine(object):
    def __init__(self, cfg, logger):
        self.cfg = cfg
        self.log = logger
        self.rounding = RoundingPolicy(cfg.ROUND_UNIT_SECONDS, cfg.ROUND_MODE, cfg.MIN_BILLABLE_SECONDS)
        self.factory = CalculatorFactory(cfg, self.rounding)

        # shared context (inject)
        self.ctx = {
            "classifier": InteractiveClassifier(cfg.INTERACTIVE_KEYWORDS),
            "cpu_summer": CpuStepSummer(),
        }

    def run(self, dataset):
        final = {}
        traces = {}

        parents = dataset.get("parents", {})
        steps = dataset.get("steps", {})

        for jobid, parent_row in parents.items():
            step_rows = steps.get(jobid, [])

            calc = self.factory.create(parent_row)
            out_row, trace = calc.calculate(jobid, parent_row, step_rows, self.ctx)

            final[jobid] = out_row
            traces[jobid] = trace

            # debug: one-line trace
            if self.log.isEnabledFor(logging.DEBUG):
                self.log.debug(TracePrinter.one_line(trace))

        dataset["final"] = final
        dataset["traces"] = traces
        return dataset


# -----------------------------
# Reporter (minimal)
# -----------------------------
class Reporter(object):
    @staticmethod
    def print_table(final_map):
        header = [
            "JobID", "User", "JobName", "Part", "NCPUS",
            "Elapsed(s)", "CPUTime(s)", "TotalCPU(s)",
            "BillMode", "Bill(raw)", "Bill(rounded)"
        ]
        fmt = "{:<6s} {:<8s} {:<10s} {:<6s} {:>5s} {:>10s} {:>10s} {:>10s} {:<9s} {:>10s} {:>12s}"
        print(fmt.format(*header))

        for jid in sorted(final_map.keys(), key=lambda x: int(x)):
            r = final_map[jid]
            row = [
                str(r.get("JobID", jid)),
                (r.get("User", "") or "")[:8],
                (r.get("JobName", "") or "")[:10],
                (r.get("Partition", "") or "")[:6],
                str(r.get("NCPUS", "")),
                "{:.1f}".format(r.get("Elapsed_s", 0.0)),
                "{:.1f}".format(r.get("CPUTime_s", 0.0)),
                "{:.3f}".format(r.get("TotalCPU_s", 0.0)),
                r.get("BillMode", ""),
                "{:.3f}".format(r.get("BillSeconds_raw", 0.0)),
                "{:.3f}".format(r.get("BillSeconds_rounded", 0.0)),
            ]
            print(fmt.format(*row))


# -----------------------------
# CLI / main
# -----------------------------
def parse_args(argv):
    starttime = Config.DEFAULT_STARTTIME
    log_level = logging.WARNING
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--debug":
            log_level = logging.DEBUG
            i += 1
            continue
        if a == "--info":
            log_level = logging.INFO
            i += 1
            continue
        starttime = a
        i += 1
    return starttime, log_level


def main(argv):
    starttime, log_level = parse_args(argv)
    log = setup_logger(log_level)

    try:
        rows = SacctClient(Config.SACCT_PATH, log).fetch_rows(starttime=starttime, endtime="now")
        dataset = DatasetBuilder(log).build(rows)
        dataset = BillingEngine(Config, log).run(dataset)
        Reporter.print_table(dataset.get("final", {}))
    except Exception as e:
        log.info("Fatal error: %s", str(e))
        log.debug("Exception details", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv)