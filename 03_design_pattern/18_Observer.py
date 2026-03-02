"""
Observer
観測対象のオブジェクトの状態変化が発生した際に、複数の観測者に対して通知を行うパターン

観測者よりも通知に絨毯が置かれており、Publish - Subscribeパターンと呼ばれることもある
"""
from abc import ABC, abstractmethod
from typing import List


class Observer(ABC):
    @abstractmethod
    def update(self, name: str):
        pass


class StoreObserver(Observer):
    def update(self, name: str):
        print(f"{name}が入荷されました、仕入れが可能です")


class PersonalObserver(Observer):
    def update(self, name: str):
        print(f"{name}が入荷されました、購入が可能です")


class ItemSubject(ABC):
    def __init__(self, name: str):
        self.__name = name
        self.__observers: List[Observer] = []
