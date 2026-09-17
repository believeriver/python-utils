import os
import json
from abc import ABC, abstractmethod
from typing import List
from pprint import pformat


# -----------------------------
# Reporter
# -----------------------------
class IReporterInterface(ABC):
    @staticmethod
    @abstractmethod
    def print_results(results: List[dict]) -> None:
        pass


class ReporterSample(IReporterInterface):
    @staticmethod
    def print_results(results: List[dict]) -> None:
        print('*' * 80)
        print("[INFO]: Results Summary")
        # print(json.dumps(worker.results, indent=2, ensure_ascii=False))
        width = 12
        for res in results:
            for hostname, lines in res.items():
                print("-" * 80)
                hostname_str = str(hostname) if hostname is not None else "Unknown Host"
                # print(f"--- results for {hostname} ---")
                if lines == [] or lines is None:
                    print(f"{hostname_str:<{width}} | No data or error occurred.")
                    # print(f"{hostname_str}, No data or error occurred.")
                    continue
                for line in lines:
                    msg = line.replace("\\r", "").replace("\\n", "\n")
                    print(f"{hostname_str:<{width}} | {msg}")
                    # print(f"{hostname_str}, {msg}")
