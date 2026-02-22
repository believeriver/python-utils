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
    DEFAULT_STARTTIME = 90

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
class Schema(ABC):
    @abstractmethod
    def format_arg(cls):
        pass


class SubmitClient(ABC):
    @abstractmethod
    def run_command(self, cmd):
        pass


class SacctSchema(ABC):
    def __init__(self):
        self.FIELDS = [
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


class SacctClient(object):
    def __init__(self, sacct_path, logger, schema: SacctSchema, day_ago=90):
        self.sacct_path = sacct_path
        self.log = logger
        self.schema = schema
        self.days_ago = day_ago

    def calc_starttime(self, endtime=None):
        """
        days_ago: int (例: 90)
        endtime: datetime or None (None = now)
        return: 'YYYY-MM-DDTHH:MM'
        """
        if endtime is None or endtime == "now":
            endtime = datetime.now()

        start = endtime - timedelta(days=self.days_ago)

        # sacct が素直に読める形式
        return start.strftime("%Y-%m-%dT%H:%M")

    def fetch_rows(self, endtime="now"):
        cmd = [
            "ssh",
            "root@192.168.64.2",
            self.sacct_path,
            "--starttime", self.calc_starttime(endtime),
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
        # self.log.debug("raw_lines: %s", raw_lines)
        # debug: raw all
        if self.log.isEnabledFor(logging.DEBUG):
            self.log.debug("RAW_ALL_BEGIN total=%d", len(raw_lines))
            for ln in raw_lines:
                self.log.debug("RAW|%s", ln)
            self.log.debug("RAW_ALL_END")
        return [self.schema.parse_line(ln) for ln in raw_lines]


if __name__ == "__main__":
    log = setup_logger(Config.log_level)
    schema = SacctSchema()
    client = SacctClient(
        Config.SACCT_PATH, log, schema, day_ago=Config.DEFAULT_STARTTIME)
    rows = client.fetch_rows()
    for r in rows:
        log.info("ROW: %s", r)





