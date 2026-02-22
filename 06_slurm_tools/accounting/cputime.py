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
from datetime import datetime, timedelta


# -----------------------------
# Config
# -----------------------------
class Config(object):
    # DEFAULT_STARTTIME = "2026-01-01"
    DEFAULT_SPAN = 34
    SSH_HOST = "192.168.64.2"
    SSH_USER = "root"

    INTERACTIVE_KEYWORDS = ["--pty", "salloc"]
    UNKNOWN_AS_CPU_BILLING = True

    # Policy switches (easy to flip later)
    USE_OCCUPIED_FOR_INTERACTIVE = True

    # Rounding
    ROUND_UNIT_SECONDS = 60
    ROUND_MODE = "ceil"
    MIN_BILLABLE_SECONDS = 0

    SACCT_PATH = "/usr/bin/sacct"
    log_level = logging.DEBUG


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


class ISacctClientBase(ABC):
    def __init__(self, sacct_path, logger, schema:ISchema, days_ago=90,
                 ssh_host=None, ssh_user=None):
        self.sacct_path = sacct_path
        self.log = logger
        self.schema = schema
        self.days_ago = int(days_ago)
        self.ssh_host = ssh_host
        self.ssh_user = ssh_user

    def _parse_endtime(self, endtime):
        """
        endtime:
          - "now"
          - None
          - "YYYY-MM-DDTHH:MM"
        """
        if endtime is None or endtime == "now":
            return datetime.now()

        try:
            return datetime.strptime(endtime, "%Y-%m-%dT%H:%M")
        except ValueError:
            raise ValueError("Unsupported endtime format: %s" % endtime)

    def calc_starttime(self, endtime=None):
        """
        days_ago: int (例: 90)
        endtime: datetime or None (None = now)
        return: 'YYYY-MM-DDTHH:MM'
        """
        end_dt = self._parse_endtime(endtime)
        start = end_dt - timedelta(days=self.days_ago)

        # sacct が素直に読める形式
        return start.strftime("%Y-%m-%dT%H:%M")

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
        starttime = self.calc_starttime(endtime)
        cmd = []
        if self.ssh_host:
            user_at = "{}@{}".format(self.ssh_user, self.ssh_host) if self.ssh_user else self.ssh_host
            cmd += ["ssh", user_at]

        cmd += [
            self.sacct_path,
            "--starttime", starttime,
            "--endtime", endtime,
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
        self.log.debug("Dataset built: parents=%d step_parents=%d", len(ds["parents"]), len(ds["steps"]))
        return ds


class App(object):
    def run(self):
        log = setup_logger(Config.log_level)
        cpu_schema = SacctCpuSchema()
        client = SacctClient(
            sacct_path=Config.SACCT_PATH,
            logger=log,
            schema=cpu_schema,
            days_ago=Config.DEFAULT_SPAN,
            ssh_host=Config.SSH_HOST,
            ssh_user=Config.SSH_USER,)
        rows = client.fetch_rows()
        dataset = DatasetCpuBuilder(logger=log).build(rows)

        for r in rows:
            log.info("ROW: %s", r)

        print('')
        print(dataset)


if __name__ == "__main__":
    app = App()
    app.run()


