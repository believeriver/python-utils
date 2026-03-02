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

    def attach(self, observer: Observer):
        self.__observers.append(observer)

    def detach(self, observer: Observer):
        self.__observers.remove(observer)

    def notify(self):
        for observer in self.__observers:
            observer.update(self.__name)

    @abstractmethod
    def restock(self):
        pass


class TvGameSubject(ItemSubject):
    def __init__(self, name: str):
        super().__init__(name)
        self.__in_stok = False

    def restock(self):
        print("TV Gameの入荷")
        self.__in_stok = True
        self.notify()


if __name__ == '__main__':
    store = StoreObserver()
    person = PersonalObserver()

    game = TvGameSubject("FF7")
    game.attach(store)
    game.attach(person)
    game.restock()

    game.detach(person)
    game.restock()

