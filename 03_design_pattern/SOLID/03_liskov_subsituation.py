from abc import ABCMeta, abstractmethod

"""Liskov Substitution Principle Example
リスコフの置換原則(LSP: Liskov Substitution Principle)
- サブタイプは、その基底型と置換可能であるべきである
"""


class IShape(metaclass=ABCMeta):
    @abstractmethod
    def area(self) -> float:
        pass


class Rectangle(IShape):
    def __init__(self, width: float, height: float):
        self.__width = width
        self.__height = height

    @property
    def width(self) -> float:
        return self.__width

    @property
    def height(self) -> float:
        return self.__height

    @width.setter
    def width(self, width: float):
        self.__width = width

    @height.setter
    def height(self, height: float):
        self.__height = height

    def area(self) -> float:
        return self.__width * self.__height

class Square(IShape):
    def __init__(self, side: float):
        self.__side = side

    @property
    def side(self) -> float:
        return self.__side

    @side.setter
    def side(self, side: float):
        self.__side = side

    def area(self) -> float:
        return self.__side * self.__side


def f(shape: IShape, x: float=0.0, y: float=0.0):
    if isinstance(shape, Rectangle):
        shape.width = x
        shape.height = y
        print(f"Rectangleの面積: {shape.area()}")
    elif isinstance(shape, Square):
        shape.side = x
        print(f"Squareの面積: {shape.area()}")
    else:
        raise TypeError("Unsupported shape type")


if __name__ == '__main__':
    rect = Rectangle(2.0, 3.0)
    f(rect, 4.0, 5.0)  # Rectangleの面積: 20.0

    square = Square(4.0)
    f(square, 6.0)     # Squareの面積: 36.0
