# reporter.py
from abc import ABC, abstractmethod
from typing import List


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
        width = 12
        for res in results:
            for hostname, lines in res.items():
                print("-" * 80)
                hostname_str = str(hostname) if hostname is not None else "Unknown Host"
                if lines == [] or lines is None:
                    print(f"{hostname_str:<{width}} | No data or error occurred.")
                    continue
                for line in lines:
                    msg = line.replace("\\r", "").replace("\\n", "\n")
                    print(f"{hostname_str:<{width}} | {msg}")