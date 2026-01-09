import math
from abc import ABCMeta, abstractmethod

class IEmployee(metaclass=ABCMeta):
    def __init__(self, _name: str):
        self.name = _name

    @abstractmethod
    def get_bonus(self, base: int) -> int:
        pass


class JuniorEmployee(IEmployee):
    def get_bonus(self, base: int) -> int:
        return math.floor(base * 1.1)


class MidLevelEmployee(IEmployee):
    def get_bonus(self, base: int) -> int:
        return math.floor(base * 1.2)


class LowLevelEmployee(IEmployee):
    def get_bonus(self, base: int) -> int:
        return math.floor(base * 0.8)


class SeniorEmployee(IEmployee):
    def get_bonus(self, base: int) -> int:
        return math.floor(base * 1.3)


class ExpertEmployee(IEmployee):
    def get_bonus(self, base: int) -> int:
        return math.floor(base * 3)


if __name__ == '__main__':
    employees = [
        JuniorEmployee("Suzuki"),
        MidLevelEmployee("Takahashi"),
        LowLevelEmployee("Tanaka"),
        SeniorEmployee("Sato"),
        ExpertEmployee("Yamamoto"),
    ]

    base_salary = 1000
    for emp in employees:
        bonus = emp.get_bonus(base_salary)
        print(f"{emp.name}のボーナスは{bonus}円です")

