from abc import ABCMeta, abstractmethod
from typing import List


"""Iterator Pattern Example
コレクションの内部構造を利用者に見せずに、その要素に順番にアクセスする方法を提供するパターン
（コレクション：配列や辞書などのデータをまとめて格納するもの）

ループ処理のインデックスの役割を抽象化し一般化したもの

振る舞いに関するデザインパターン
"""


class Patient(object):
    def __init__(self, _name: str, _id: int) -> None:
        self.id = _id
        self.name = _name

    def __str__(self) -> str:
        return self.name


class Iterator(metaclass=ABCMeta):
    @abstractmethod
    def has_next(self) -> bool:
        pass

    @abstractmethod
    def next(self) -> Patient:
        pass

class Aggregate(metaclass=ABCMeta):
    @abstractmethod
    def create_iterator(self) -> Iterator:
        pass


class WaitingRoomIterator(Iterator):
    def __init__(self, _aggregate: 'WaitingRoom') -> None:
        self.aggregate = _aggregate
        self.current_index = 0

    def has_next(self) -> bool:
        return self.current_index < len(self.aggregate.patients)

    def next(self) -> Patient:
        if not self.has_next():
            print("No more patients.")
            return None
        _patient = self.aggregate.patients[self.current_index]
        self.current_index += 1
        return _patient


class WaitingRoom(Aggregate):
    def __init__(self) -> None:
        self.patients: List[Patient] = []

    def add_patient(self, _patient: Patient) -> None:
        self.patients.append(_patient)

    def create_iterator(self) -> Iterator:
        return WaitingRoomIterator(self)

    def get_patient(self) -> List[Patient]:
        return self.patients


if __name__ == '__main__':
    waiting_room = WaitingRoom()
    waiting_room.add_patient(Patient('P1', 1))
    waiting_room.add_patient(Patient('P2', 2))
    waiting_room.add_patient(Patient('P3', 3))

    iterator = waiting_room.create_iterator()
    while iterator.has_next():
        patient = iterator.next()
        print(f"Next patient: {patient}")

    # Output:
    # Next patient: P1
    # Next patient: P2
    # Next patient: P3