from abc import ABCMeta, abstractmethod

"""Interface Segregation Principle Example
インターフェース分離の原則(ISP: Interface Segregation Principle)
- クライアントは、使用しないメソッドに依存してはなら
- インターフェースは、そのクライアントに特化したものであるべきである。
"""

class VehicleInterface(metaclass=ABCMeta):
    def __init__(self, name: str, color: str) -> None:
        self.name = name
        self.color = color


class MovableInterface(VehicleInterface):
    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

class FlyableInterface(VehicleInterface):
    @abstractmethod
    def fly(self) -> None:
        pass


class Airplane(FlyableInterface, MovableInterface):
    def start(self) -> None:
        print(f"{self.name}が離陸しました。")

    def stop(self) -> None:
        print(f"{self.name}が着陸しました。")

    def fly(self) -> None:
        print(f"{self.name}が飛行中です。")


class Car(MovableInterface):
    def start(self) -> None:
        print(f"{self.name}が走り始めました。")

    def stop(self) -> None:
        print(f"{self.name}が止まりました。")


if __name__ == '__main__':
    airplane = Airplane("Boeing 747", "White")
    airplane.start()
    airplane.fly()
    airplane.stop()

    print("")

    car = Car("Toyota Corolla", "Blue")
    car.start()
    car.stop()
