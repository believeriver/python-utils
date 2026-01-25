"""Prototype Design Pattern Example in Python.
This example demonstrates the Prototype design pattern, which allows
for the cloning of objects to create new instances without relying on
the traditional class instantiation process.

The Prototype pattern is useful when the cost of creating a new object
is expensive or complex. By cloning an existing object, we can create
new objects more efficiently.

In this example, we define a `Prototype` class with a `clone` method
that uses the `copy` module to create a shallow copy of the object.

We then create a `ConcretePrototype` class that inherits from `Prototype`
and adds additional attributes. Finally, we demonstrate how to clone
an instance of `ConcretePrototype` to create a new object.

原型となるインスタンスをコピーして新しいインスタンスを生成するパターン
親クラスでインスタンスをコピーするためのメソッドを定義し、子クラスで自分自身のコピーを返すように実装する
"""

from __future__ import annotations
import copy
from abc import ABC, abstractmethod
from typing import List, Union
import gc


class ItemPrototype(ABC):
    def __init__(self, name: str):
        self.__name = name
        self.__review: List[str] = []

    def __str__(self):
        return f"Item(name={self.__name}): reviews={self.__review}"

    def set_review(self, _review: str):
        self.__review.append(_review)

    @abstractmethod
    def clone(self) -> ItemPrototype:
        pass


class ShallowItem(ItemPrototype):

    def clone(self) -> ItemPrototype:
        return copy.copy(self)


class DeepItem(ItemPrototype):

    def clone(self) -> ItemPrototype:
        return copy.deepcopy(self)


class ItemManager:
    def __init__(self):
        self._items = {}

    def register_item(self, key:str, item: ItemPrototype):
        self._items[key] = item

    def create(self, key: str) -> Union[ItemPrototype, None]:
        if key in self._items:
            item = self._items[key]
            return item.clone()
        raise KeyError(f"Item {key} already exists.")


if __name__ == "__main__":
    manager = ItemManager()

    item1 = ShallowItem("ShallowItem1")
    item1.set_review("Good item.")
    manager.register_item("item1", item1)

    item2 = DeepItem("DeepItem1")
    item2.set_review("Excellent item.")
    manager.register_item("item2", item2)

    print(f'original item1: {item1}')
    print(f'original item2: {item2}')

    print('--- cloning items ---')

    cloned_item1 = manager.create("item1")
    cloned_item1.set_review("Cloned review for shallow item.")
    cloned_item2 = manager.create("item2")
    cloned_item2.set_review("Cloned review for deep item.")

    print(f'original item1: {item1}')
    print(f'original item2: {item2}')
    print(f'cloned item1:{cloned_item1}')
    print(f'cloned item2:{cloned_item2}')

    gc.collect()