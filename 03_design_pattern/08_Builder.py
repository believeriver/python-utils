"""
Builder Pattern
This example demonstrates the Builder design pattern, which separates the construction
of a complex object from its representation, allowing the same construction process
to create different representations. of the object.
The Builder pattern is useful when an object requires multiple steps to be constructed,
and when the construction process needs to be flexible and customizable.
In this example, we define a `Product` class that represents the complex object to be built
and a `Builder` interface that defines the steps required to build the product.

同じ生成手順で異なる材料を使ってオブジェクトを生成するパターン

１ ConcreteBuilder クラスで具体的な生成手順を実装する
２ Director クラスで生成手順を管理する

ConcreteBuilderのインスタンス化
ConcretaBuilderのインスタンスをDirectorに渡す
DirectorがConcreteBuilderのメソッドを呼び出してオブジェクトを生成する
ConcreteBuilderから生成されたオブジェクトを受け取る
"""

from abc import ABC, abstractmethod


class Computer:
    def __init__(self):
        self.cpu = None
        self.ram = None
        self.type = None

    def __str__(self):
        return f"Computer(type={self.type}, cpu={self.cpu}, ram={self.ram})"


class ComputerBuilder(ABC):
    @abstractmethod
    def set_cpu(self, _cpu: str):
        pass

    @abstractmethod
    def set_ram(self, _ram: str):
        pass


class DesktopBuilder(ComputerBuilder):
    def __init__(self):
        self.__computer = Computer()
        self.__computer.type = "Desktop"

    def set_cpu(self, _cpu: str):
        self.__computer.cpu = _cpu

    def set_ram(self, _ram: str):
        self.__computer.ram = _ram

    def get_computer(self) -> Computer:
        return self.__computer


class LaptopBuilder(ComputerBuilder):
    def __init__(self):
        self.__computer = Computer()
        self.__computer.type = "Laptop"

    def set_cpu(self, _cpu: str):
        self.__computer.cpu = _cpu

    def set_ram(self, _ram: str):
        self.__computer.ram = _ram

    def get_computer(self) -> Computer:
        return self.__computer


class Director:
    def __init__(self, builder: ComputerBuilder):
        self._builder = builder

    def construct(self) -> None:
        self._builder.set_cpu("Intel i7")
        self._builder.set_ram("16GB")

    def high_spec_construct(self) -> None:
        self._builder.set_cpu("Intel i9")
        self._builder.set_ram("32GB")


if __name__ == "__main__":
    # Desktopの生成
    desktop_builder = DesktopBuilder()
    director = Director(desktop_builder)
    director.construct()
    desktop = desktop_builder.get_computer()
    print(desktop)

    # Laptopの生成
    laptop_builder = LaptopBuilder()
    director = Director(laptop_builder)
    director.high_spec_construct()
    laptop = laptop_builder.get_computer()
    print(laptop)


