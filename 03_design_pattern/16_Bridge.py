"""
Bridge Pattern
The bridge pattern is a design pattern that decouples an abstraction from its implementation, allowing the
two to vary independently. It is often used to separate the interface of a class from its implementation,
so that the two can be developed and modified independently.
In the bridge pattern, you have an abstraction that defines the high-level interface for the client,
and an implementation that defines the low-level interface for the concrete implementation. The abstraction
contains a reference to the implementation, and the client interacts with the abstraction rather than the implementation directly

機能を提供するクラスと、実装を提供するクラスを特立させるためのパターン
目的と手段を分離する
委譲を行うことで、機能と実装を独立して変更できるようにする
例）GUIフレームワークで、ウィンドウの描画とプ

複数のOSからアプリを使ってメッセージを送信する例
"""

from abc import ABC, abstractmethod


class MessageApp(ABC):
    @abstractmethod
    def send_message(self, _message: str) -> None:
        pass


class LINE(MessageApp):
    def send_message(self, _message: str) -> None:
        print(f"LINE: {_message}")


class Twiiter(MessageApp):
    def send_message(self, _message: str) -> None:
        print(f"Twitter: {_message}")


class Facebook(MessageApp):
    def send_message(self, _message: str) -> None:
        print(f"Facebook: {_message}")


class Manager(ABC):
    def __init__(self):
        self._app = None

    def set_app(self, _app: MessageApp) -> None:
        self._app = _app

    @abstractmethod
    def send_message(self) -> None:
        pass


class IOS(Manager):
    def send_message(self) -> None:
        if self._app is not None:
            self._app.send_message("Hello from iOS!")
        else:
            print("No app set for iOS.")


class Android(Manager):
    def send_message(self) -> None:
        if self._app is not None:
            self._app.send_message("Hello from Android!")
        else:
            print("No app set for Android.")


if __name__ == "__main__":
    ios_manager = IOS()
    android_manager = Android()

    line_app = LINE()
    twitter_app = Twiiter()
    facebook_app = Facebook()

    ios_manager.set_app(line_app)
    android_manager.set_app(twitter_app)

    ios_manager.send_message()  # LINE: Hello from iOS!
    android_manager.send_message()  # Twitter: Hello from Android!

    # Facebookに切り替え
    ios_manager.set_app(facebook_app)
    android_manager.set_app(facebook_app)

    ios_manager.send_message()  # Facebook: Hello from iOS!
    android_manager.send_message()  # Facebook: Hello from Android!
