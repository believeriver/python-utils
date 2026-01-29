"""Abstract Factory Design Pattern Example in Python.
This example demonstrates the Abstract Factory pattern by creating
a family of related objects (Buttons and Checkboxes) without specifying
their concrete classes.

関連したオブジェクト（部品）のセットを生成するためのインターフェースを提供するデザインパターン。
部品の具体的な実装には着目せず、抽象のAPIに注目して、そのAPIを通じて部品を生成する。

"""

from abc import ABC, abstractmethod

# Abstract Products
class Button(ABC):
    @abstractmethod
    def press(self) -> str:
        pass

class Checkbox(ABC):
    @abstractmethod
    def check(self) -> str:
        pass


# Concrete Products
class WindowsButton(Button):
    def press(self) -> str:
        return "Windows Button Pressed"


class MacOSButton(Button):
    def press(self) -> str:
        return "MacOS Button Pressed"


class WindowsCheckbox(Checkbox):
    def check(self) -> str:
        return "Windows Checkbox Checked"


class MacOSCheckbox(Checkbox):
    def check(self) -> str:
        return "MacOS Checkbox Checked"


# Abstract Factory
class GUIFactory(ABC):
    @abstractmethod
    def create_button(self) -> Button:
        pass

    @abstractmethod
    def create_checkbox(self) -> Checkbox:
        pass


# Concrete Factories
class WindowsFactory(GUIFactory):
    def create_button(self) -> Button:
        return WindowsButton()

    def create_checkbox(self) -> Checkbox:
        return WindowsCheckbox()


class MacOSFactory(GUIFactory):
    def create_button(self) -> Button:
        return MacOSButton()

    def create_checkbox(self) -> Checkbox:
        return MacOSCheckbox()


# Client Code
def client_code(factory: GUIFactory) -> None:
    button = factory.create_button()
    checkbox = factory.create_checkbox()

    print(button.press())
    print(checkbox.check())


if __name__ == "__main__":
    print("Client: Testing client code with Windows Factory:")
    windows_factory = WindowsFactory()
    client_code(windows_factory)

    print("\nClient: Testing client code with MacOS Factory:")
    macos_factory = MacOSFactory()
    client_code(macos_factory)

