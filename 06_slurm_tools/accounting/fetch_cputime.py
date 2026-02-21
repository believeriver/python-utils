"""
SLURM CPU billing base program (Python 3.6 compatible).

Features:
- Fetch sacct (parsable2) rows including SubmitLine.
- CPU usage aggregation policy:
    * If a job has any step rows (jobid.*), use ONLY step sums for TotalCPU/UserCPU/SystemCPU.
    * If no step rows exist, use parent row CPU values (needed for some srun --pty jobs).
- Interactive detection:
    * interactive if SubmitLine contains '--pty' or 'salloc' (case-insensitive).
    * if SubmitLine is missing/empty => unknown => fall back to CPU-based billing (safe side).
- Billing CPU seconds:
    * batch jobs: TotalCPU (actual CPU time)
    * interactive jobs: choose TotalCPU or CPUTime (occupied = Elapsed*NCPUS) by config
- Rounding policy is configurable and easy to change later.
- Output:
    * default: human-readable table
    * optional: CSV output with --csv

Usage:
  python3.6 billing_slurm_cpu.py [starttime] [--csv out.csv]
  python3.6 billing_slurm_cpu.py 2026-02-01 --csv report.csv
"""

import subprocess
import re
import sys
import math
import csv


# -----------------------------
# Config (edit here)
# -----------------------------
class Config(object):
    # Default time range start
    DEFAULT_STARTTIME = "2026-01-01"

    # Interactive detection keywords (lowercase compare)
    INTERACTIVE_KEYWORDS = ["--pty", "salloc"]

    # If SubmitLine missing/empty, avoid overcharge:
    # True: treat unknown as CPU-billing (TotalCPU)
    # False: treat unknown as interactive (occupied)  -> NOT recommended for your policy
    UNKNOWN_AS_CPU_BILLING = True

    # Interactive billing mode:
    # True: interactive jobs billed by occupied time (CPUTime = Elapsed * NCPUS)
    # False: interactive jobs billed by TotalCPU (actual CPU time)
    #USE_OCCUPIED_FOR_INTERACTIVE = True
    USE_OCCUPIED_FOR_INTERACTIVE = False

    # Rounding unit in seconds (e.g. 60 for per-minute billing, 3600 for per-hour)
    ROUND_UNIT_SECONDS = 60

    # Rounding mode: "ceil", "floor", "round", "none"
    #ROUND_MODE = "ceil"
    ROUND_MODE = "none"

    # Optional minimum billable seconds (e.g. 60)
    MIN_BILLABLE_SECONDS = 0

    # Sacct path
    SACCT_PATH = "/usr/bin/sacct"


# -----------------------------
# Time conversion
# -----------------------------
class SlurmTime(object):
    @staticmethod
    def to_seconds(t):
        """
        Convert SLURM time string to seconds (float).
        Formats:
          - DD-HH:MM:SS[.mmm]
          - HH:MM:SS[.mmm]
          - MM:SS[.mmm]  (e.g. 00:00.054 or 18:07.645)
          - SS[.mmm]
        """
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
                h = int(parts[0])
                m = int(parts[1])
                s = float(parts[2])
            elif len(parts) == 2:
                h = 0
                m = int(parts[0])
                s = float(parts[1])
            elif len(parts) == 1:
                h = 0
                m = 0
                s = float(parts[0])
            else:
                return 0.0
        except ValueError:
            return 0.0

        return days * 86400.0 + h * 3600.0 + m * 60.0 + s

    @staticmethod
    def fmt_seconds(sec):
        # for display only
        if sec < 0:
            sec = 0.0
        return "{:.3f}".format(sec)


# -----------------------------
# sacct client
# -----------------------------
class SacctClient(object):
    def __init__(self, sacct_path):
        self.sacct_path = sacct_path

    def fetch_rows(self, starttime, endtime="now"):
        # Include CPUTime so we can bill occupied time for interactive if configured.
        fmt = ",".join([
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
        ])

        cmd = [
            "ssh",
            "root@192.168.64.2",
            self.sacct_path,
            "--starttime", starttime,
            "--endtime", endtime,
            "--format", fmt,
            "--parsable2",
            "-n",
        ]

        p = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        if p.returncode != 0:
            sys.stderr.write("ERROR: sacct failed\n")
            sys.stderr.write(p.stderr)
            sys.exit(2)

        rows = []
        for line in p.stdout.splitlines():
            if not line.strip():
                continue
            cols = line.split("|")
            # Expect 15 columns; tolerate missing trailing fields
            while len(cols) < 15:
                cols.append("")
            rows.append(cols[:15])
        return rows


# -----------------------------
# Data models and aggregation
# -----------------------------
class JobRecord(object):
    def __init__(self, jobid):
        self.jobid = jobid

        # meta (parent line preferred)
        self.end = ""
        self.user = ""
        self.jobname = ""
        self.partition = ""
        self.nodelist = ""
        self.ncpus = 0
        self.alloctres = ""
        self.state = ""
        self.submitline = ""

        # time (seconds)
        self.elapsed_s = 0.0
        self.cputime_s = 0.0  # Elapsed * NCPUS (occupied)
        # CPU usage (actual)
        self.totalcpu_s = 0.0
        self.usercpu_s = 0.0
        self.systemcpu_s = 0.0

        # For auditing aggregation source
        self.cpu_source = ""  # "steps" or "parent"


class JobAccumulator(object):
    _STEP_RE = re.compile(r"^(\d+)\..+$")
    _JOB_RE = re.compile(r"^\d+$")

    def __init__(self):
        self.parents = {}     # jobid -> parent fields dict (one row)
        self.step_sums = {}   # jobid -> [total,user,sys]
        self.has_steps = set()

    def ingest(self, cols):
        (jobid, elapsed, cputime, total, usercpu, syscpu, state, submit,
         jobname, user, partition, ncpus, alloctres, nodelist, endtime) = cols

        m = self._STEP_RE.match(jobid)
        if m:
            parent = m.group(1)
            self.has_steps.add(parent)
            cur = self.step_sums.get(parent)
            if cur is None:
                cur = [0.0, 0.0, 0.0]
                self.step_sums[parent] = cur
            cur[0] += SlurmTime.to_seconds(total)
            cur[1] += SlurmTime.to_seconds(usercpu)
            cur[2] += SlurmTime.to_seconds(syscpu)
            return

        if self._JOB_RE.match(jobid):
            # Keep latest parent row (should be one anyway)
            self.parents[jobid] = {
                "elapsed_s": SlurmTime.to_seconds(elapsed),
                "cputime_s": SlurmTime.to_seconds(cputime),
                "totalcpu_s": SlurmTime.to_seconds(total),
                "usercpu_s": SlurmTime.to_seconds(usercpu),
                "systemcpu_s": SlurmTime.to_seconds(syscpu),
                "state": state or "",
                "submitline": submit or "",
                "jobname": jobname or "",
                "user": user or "",
                "partition": partition or "",
                "ncpus": ncpus or "0",
                "alloctres": alloctres or "",
                "nodelist": nodelist or "",
                "end": endtime or "",
            }
            return

        # ignore any other

    def finalize(self):
        result = {}

        for jobid, p in self.parents.items():
            jr = JobRecord(jobid)
            jr.elapsed_s = p["elapsed_s"]
            jr.cputime_s = p["cputime_s"]
            jr.state = p["state"]
            jr.submitline = p["submitline"]
            jr.jobname = p["jobname"]
            jr.user = p["user"]
            jr.partition = p["partition"]
            jr.alloctres = p["alloctres"]
            jr.nodelist = p["nodelist"]
            jr.end = p["end"]

            try:
                jr.ncpus = int(p["ncpus"]) if p["ncpus"] else 0
            except ValueError:
                jr.ncpus = 0

            if jobid in self.has_steps:
                s = self.step_sums.get(jobid, [0.0, 0.0, 0.0])
                jr.totalcpu_s, jr.usercpu_s, jr.systemcpu_s = s[0], s[1], s[2]
                jr.cpu_source = "steps"
            else:
                jr.totalcpu_s = p["totalcpu_s"]
                jr.usercpu_s = p["usercpu_s"]
                jr.systemcpu_s = p["systemcpu_s"]
                jr.cpu_source = "parent"

            result[jobid] = jr

        return result


# -----------------------------
# Interactive classifier
# -----------------------------
class InteractiveClassifier(object):
    def __init__(self, keywords):
        self.keywords = [k.lower() for k in keywords]

    def classify(self, submitline):
        if not submitline:
            return None  # unknown
        s = submitline.lower()
        for k in self.keywords:
            if k in s:
                return True
        return False


# -----------------------------
# Rounding policy
# -----------------------------
class RoundingPolicy(object):
    def __init__(self, unit_seconds, mode, min_seconds=0):
        self.unit = float(unit_seconds) if unit_seconds and unit_seconds > 0 else 0.0
        self.mode = (mode or "none").lower()
        self.min_seconds = float(min_seconds) if min_seconds and min_seconds > 0 else 0.0

    def apply(self, seconds):
        if seconds < 0:
            seconds = 0.0

        # Minimum billable
        if self.min_seconds > 0 and seconds > 0 and seconds < self.min_seconds:
            seconds = self.min_seconds

        if self.mode == "none" or self.unit == 0.0:
            return seconds

        q = seconds / self.unit

        if self.mode == "ceil":
            return math.ceil(q) * self.unit
        if self.mode == "floor":
            return math.floor(q) * self.unit
        if self.mode == "round":
            # round-half-away-from-zero is not available directly; Python round is bankers.
            # For billing, many prefer floor(x+0.5). We'll implement that.
            return math.floor(q + 0.5) * self.unit

        # fallback
        return seconds


# -----------------------------
# Billing engine
# -----------------------------
class BillingEngine(object):
    def __init__(self, classifier, rounding_policy, use_occupied_for_interactive, unknown_as_cpu_billing):
        self.classifier = classifier
        self.rounding = rounding_policy
        self.use_occupied_for_interactive = use_occupied_for_interactive
        self.unknown_as_cpu_billing = unknown_as_cpu_billing

    def bill_seconds(self, jobrec):
        """
        Returns dict:
          - bill_mode: "cpu" or "occupied"
          - interactive: True/False/None
          - raw_seconds: before rounding
          - billed_seconds: after rounding
          - decision_note: explanation string
        """
        submit = jobrec.submitline
        interactive = self.classifier.classify(submit)

        # Decide mode
        if interactive is True and self.use_occupied_for_interactive:
            raw = jobrec.cputime_s
            mode = "occupied"
            note = "interactive (SubmitLine matched) -> CPUTime"
        elif interactive is True and not self.use_occupied_for_interactive:
            raw = jobrec.totalcpu_s
            mode = "cpu"
            note = "interactive (SubmitLine matched) -> TotalCPU"
        elif interactive is False:
            raw = jobrec.totalcpu_s
            mode = "cpu"
            note = "batch -> TotalCPU"
        else:
            # unknown
            if self.unknown_as_cpu_billing:
                raw = jobrec.totalcpu_s
                mode = "cpu"
                note = "SubmitLine missing -> safe fallback TotalCPU"
            else:
                raw = jobrec.cputime_s
                mode = "occupied"
                note = "SubmitLine missing -> treated as occupied"

        billed = self.rounding.apply(raw)

        return {
            "interactive": interactive,
            "bill_mode": mode,
            "raw_seconds": raw,
            "billed_seconds": billed,
            "decision_note": note,
        }


# -----------------------------
# Reporting
# -----------------------------
class Reporter(object):
    @staticmethod
    def print_table(records, billing_results):
        # Header: include enough for audit
        header = [
            "JobID", "User", "JobName", "Part", "NCPUS",
            "Elapsed(s)", "CPUTime(s)", "TotalCPU(s)",
            "BillMode", "BillSec(raw)", "BillSec(rounded)",
            "Submit?", "CPUfrom"
        ]
        fmt = "{:<6s} {:<8s} {:<10s} {:<6s} {:>5s} {:>10s} {:>10s} {:>10s} {:<9s} {:>12s} {:>14s} {:<6s} {:<6s}"
        print(fmt.format(*header))

        for jid in sorted(records.keys(), key=lambda x: int(x)):
            r = records[jid]
            b = billing_results[jid]
            submit_flag = "Y" if (r.submitline and r.submitline.strip()) else "N"

            row = [
                jid,
                (r.user or "")[:8],
                (r.jobname or "")[:10],
                (r.partition or "")[:6],
                str(r.ncpus),
                "{:.1f}".format(r.elapsed_s),
                "{:.1f}".format(r.cputime_s),
                "{:.3f}".format(r.totalcpu_s),
                b["bill_mode"],
                "{:.3f}".format(b["raw_seconds"]),
                "{:.3f}".format(b["billed_seconds"]),
                submit_flag,
                r.cpu_source or "",
            ]
            print(fmt.format(*row))

    @staticmethod
    def write_csv(path, records, billing_results):
        fields = [
            "JobID", "End", "User", "JobName", "Partition", "NodeList", "NCPUS", "AllocTRES",
            "State", "SubmitLine",
            "Elapsed_s", "CPUTime_s", "TotalCPU_s", "UserCPU_s", "SystemCPU_s",
            "CPU_source",
            "Interactive", "BillMode", "BillSeconds_raw", "BillSeconds_rounded", "DecisionNote"
        ]
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for jid in sorted(records.keys(), key=lambda x: int(x)):
                r = records[jid]
                b = billing_results[jid]
                w.writerow({
                    "JobID": jid,
                    "End": r.end,
                    "User": r.user,
                    "JobName": r.jobname,
                    "Partition": r.partition,
                    "NodeList": r.nodelist,
                    "NCPUS": r.ncpus,
                    "AllocTRES": r.alloctres,
                    "State": r.state,
                    "SubmitLine": r.submitline,
                    "Elapsed_s": r.elapsed_s,
                    "CPUTime_s": r.cputime_s,
                    "TotalCPU_s": r.totalcpu_s,
                    "UserCPU_s": r.usercpu_s,
                    "SystemCPU_s": r.systemcpu_s,
                    "CPU_source": r.cpu_source,
                    "Interactive": b["interactive"],
                    "BillMode": b["bill_mode"],
                    "BillSeconds_raw": b["raw_seconds"],
                    "BillSeconds_rounded": b["billed_seconds"],
                    "DecisionNote": b["decision_note"],
                })


# -----------------------------
# App
# -----------------------------
class App(object):
    def __init__(self, cfg):
        self.cfg = cfg
        self.client = SacctClient(cfg.SACCT_PATH)
        self.classifier = InteractiveClassifier(cfg.INTERACTIVE_KEYWORDS)
        self.rounding = RoundingPolicy(cfg.ROUND_UNIT_SECONDS, cfg.ROUND_MODE, cfg.MIN_BILLABLE_SECONDS)
        self.billing = BillingEngine(
            classifier=self.classifier,
            rounding_policy=self.rounding,
            use_occupied_for_interactive=cfg.USE_OCCUPIED_FOR_INTERACTIVE,
            unknown_as_cpu_billing=cfg.UNKNOWN_AS_CPU_BILLING
        )

    def run(self, starttime, csv_path=None):
        rows = self.client.fetch_rows(starttime=starttime, endtime="now")

        acc = JobAccumulator()
        for cols in rows:
            acc.ingest(cols)

        records = acc.finalize()

        billing_results = {}
        for jid, r in records.items():
            billing_results[jid] = self.billing.bill_seconds(r)

        Reporter.print_table(records, billing_results)

        if csv_path:
            Reporter.write_csv(csv_path, records, billing_results)
            print("\nCSV written to: {}".format(csv_path))


def parse_args(argv):
    # billing_slurm_cpu.py [starttime] [--csv out.csv]
    starttime = Config.DEFAULT_STARTTIME
    csv_path = None

    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--csv" and i + 1 < len(argv):
            csv_path = argv[i + 1]
            i += 2
            continue
        # otherwise treat as starttime
        starttime = a
        i += 1

    return starttime, csv_path


def main(argv):
    starttime, csv_path = parse_args(argv)
    app = App(Config)
    app.run(starttime=starttime, csv_path=csv_path)


if __name__ == "__main__":
    main(sys.argv)