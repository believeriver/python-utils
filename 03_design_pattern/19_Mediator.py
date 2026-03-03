"""
Mediator Pattern
The Mediator pattern is a design pattern that promotes loose coupling between components by introducing a mediator object
that handles communication between them.
Instead of components communicating directly with each other,
they communicate through the mediator, which centralizes the interactions and reduces dependencies.

In the Mediator pattern, components (also known as colleagues) interact with each other through the mediator,
which acts as an intermediary.
The mediator is responsible for coordinating the interactions between the components,
allowing them to communicate without needing to know about each other's implementation details.

The main benefits of the Mediator pattern include:
1. Reduced Coupling:
   Components are decoupled from each other, as they only interact with the mediator.
   This makes it easier to modify or replace components without affecting others.
2. Centralized Control:
   The mediator centralizes the control of interactions,
   making it easier to manage and maintain the communication between components.
3. Improved Code Organization:
   The Mediator pattern can help improve code organization by separating the concerns of communication and business logic.
   Components can focus on their specific tasks, while the mediator handles the communication between them.
4. Enhanced Flexibility:
   The Mediator pattern allows for more flexible communication between components,
   as the mediator can easily be modified to accommodate changes in the interactions
   without affecting the components themselves.

Overall, the Mediator pattern is a powerful design pattern that can help improve the maintainability and flexibility of a software system
by promoting loose coupling and centralized control of interactions between components.

関連し合うオブジェクト間のやりとりについて、仲介者となるオブジェクトに集約し、
オブジェクトが直接やりとりすることを制限するパターン。
オブジェクト同士の結合度を下げるデザインパターン。

その他
from __future__ import annotations は、「型ヒントをその場で評価せず、いったん文字列として保持する」ためのフラグです。
このフラグを使用することで、クラス定義の中で自分自身を型ヒントとして使用することができます。
通常、Pythonではクラス定義の中で自分自身を型ヒントとして使用することはできませんが、from __future__ import annotations を使用することで、
クラス定義の中で自分自身を型ヒントとして使用することができます。
このフラグを使用することで、クラス定義の中で自分自身を型ヒントとして使用することができるため、クラス定義の中で
より柔軟な型ヒントを使用することができます。

アノテーションは実行時には「全部文字列」として __annotations__ に入ります（例: {'manager': 'User | None'}）。
そのため、定義順や自己参照をあまり気にせず、素直な文法で書けます。

"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List


class Mediator(ABC):
    @abstractmethod
    def register_user(self, user: User):
        pass

    @abstractmethod
    def send_message(self, msg: str, sender: User):
        pass


class ChatRoom(Mediator):
    def __init__(self):
        self.__users: List[User] = []

    def register_user(self, user: User):
        self.__users.append(user)

    def send_message(self, msg: str, sender: User):
        for user in self.__users:
            if user != sender:
                user.receive_message(msg)


class User(ABC):
    def __init__(self, name: str, mediator: Mediator):
        self._name = name
        self._mediator = mediator

    @abstractmethod
    def send_message(self, msg: str):
        pass

    @abstractmethod
    def receive_message(self, msg: str):
        pass


class ChatUser(User):
    def send_message(self, msg: str):
        print(f"{self._name} sends message: {msg}")
        self._mediator.send_message(f"{self._name}: {msg}", self)

    def receive_message(self, msg: str):
        print(f"{self._name} receives message: {msg}")


if __name__ == '__main__':
    chat_room = ChatRoom()

    user1 = ChatUser("Alice", chat_room)
    user2 = ChatUser("Bob", chat_room)

    chat_room.register_user(user1)
    chat_room.register_user(user2)

    user1.send_message("Hello, Bob!")
    user2.send_message("Hi, Alice!")
