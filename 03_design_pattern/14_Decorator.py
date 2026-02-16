"""
Decorator Pattern
The decorator pattern is a design pattern that allows behavior to be added to an individual object,
either statically or dynamically, without affecting the behavior of other objects from the same class.
It is often used to extend the functionalities of classes in a flexible and reusable way.
In the decorator pattern, you have a component interface that defines the common behavior for both
the concrete component and the decorators.
The concrete component is the original object that you want to extend,
while the decorators are classes that wrap the concrete component and add new behavior.
Here's a simple example in Python to illustrate the decorator pattern:

基本となるオブジェクトに対して、柔軟に機能追加をするパターン
継承よりも柔軟で、動的に機能追加が可能
基本のオブジェクトを包むように見えるので、Wrapperパターンと呼ばれることもある

例）ログの出力を拡張する
"""

import datetime
from abc import ABC, abstractmethod


class Component(ABC):
    @abstractmethod
    def get_log_message(self, _msg: str) -> str:
        pass


class Logger(Component):
    def get_log_message(self, _msg: str) -> str:
        return _msg


class Decorator(Component):
    def __init__(self, component: Component):
        self._component = component

    @abstractmethod
    def get_log_message(self, _msg: str) -> str:
        pass


class TimestampDecorator(Decorator):
    def get_log_message(self, _msg: str) -> str:
        timestamp = datetime.datetime.now().isoformat()
        return f"{timestamp} - {self._component.get_log_message(_msg)}"


class LogLevelDecorator(Decorator):
    def __init__(self, component: Component, level: str):
        super().__init__(component)
        self._level = level

    def get_log_message(self, _msg: str) -> str:
        return self._component.get_log_message(f"[{self._level}] {_msg}")


# 使用例
if __name__ == "__main__":
    log_message = "This is a log message."

    # 基本のログメッセージ
    basic_log = Logger()
    print(basic_log.get_log_message(log_message))

    # タイムスタンプを追加
    timestamp_log = TimestampDecorator(basic_log)
    print(timestamp_log.get_log_message(log_message))

    # ログレベルを追加
    level_log = LogLevelDecorator(timestamp_log, "INFO")
    print(level_log.get_log_message(log_message))
