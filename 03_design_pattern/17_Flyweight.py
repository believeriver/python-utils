"""
Flyweight Pattern
The Flyweight pattern is a structural design pattern that allows you to minimize memory usage by sharing as much data as possible with similar objects.
It is particularly useful when you have a large number of objects that share common data, and you want to avoid creating multiple instances of that data.
In the Flyweight pattern, you typically have two types of objects: the Flyweight and the Client.
The Flyweight is the shared object that contains the common data,
while the Client is the object that uses the Flyweight and contains its own unique data.
Here's a simple example of the Flyweight pattern in Python:

ボクシングのフライ級の選手を例にしてみましょう。フライ級の選手は体重が同じであるため、体重に関する情報は共有できますが、名前や国籍などの個別の情報は異なります。
インスタンス化されたオブジェクトを効率よく共有することで、リソースの消費を抑えるパターン
"""
class Flyweight:
    def __init__(self, shared_state):
        self.shared_state = shared_state

    def operation(self, unique_state):
        print(f"Shared State: {self.shared_state}, Unique State: {unique_state}")


class FlyweightFactory:
    def __init__(self):
        self._flyweights = {}

    def get_flyweight(self, shared_state):
        if shared_state not in self._flyweights:
            self._flyweights[shared_state] = Flyweight(shared_state)
        return self._flyweights[shared_state]


class Stamp(object):
    def __init__(self, char: str):
        self.__char = char

    def print_char(self):
        print(self.__char)


class StampFactory(object):
    def __init__(self):
        self._stamps = {}

    def get_stamp(self, char: str) -> Stamp:
        stamp = self._stamps.get(char)
        if stamp:
            return Stamp(char)
        new_stamp = Stamp(char)
        self._stamps[char] = new_stamp
        return new_stamp

    def get_stamps(self):
        return self._stamps


# Client code
if __name__ == "__main__":
    factory = FlyweightFactory()

    flyweight1 = factory.get_flyweight("Shared Data")
    flyweight2 = factory.get_flyweight("Shared Data")

    print(flyweight1 is flyweight2)  # True, both are the same instance

    flyweight1.operation("Unique Data 1")
    flyweight2.operation("Unique Data 2")

    print('--- Stamp Factory Example ---')
    factory = StampFactory()
    stamp1 = factory.get_stamp("F")
    stamp2 = factory.get_stamp("L")
    stamp3 = factory.get_stamp("Y")
    stamp4 = factory.get_stamp("F")
    stamp5 = factory.get_stamp("Y")

    stamp1.print_char()
    stamp2.print_char()
    stamp3.print_char()
    stamp4.print_char()
    stamp5.print_char()

    print(factory.get_stamps())