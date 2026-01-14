"""
Singleton Design Pattern Example in Python
クラスが一つのインスタンスのみを持つことを保証し、
このインスタンスへのアクセスするためのグローバルな方法を提供するパターン

開発者は一度しかインスタンス化してはならないといったことを気にしなくて良い

ただし、Singletonはアンチパターンと言われることが多い
"""

import datetime


class SingletonMeta(type):
    """
    Singletonのメタクラス
    クラスがインスタンス化されるときに呼び出される
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

class Singleton(metaclass=SingletonMeta):
    """
    Singletonクラス
    """
    def __init__(self):
        self.value = None
        self.created_at = datetime.datetime.now()


class Logger(metaclass=SingletonMeta):
    """
    Loggerクラスの例
    """
    def log(self, message: str):
        print(f"[{datetime.datetime.now()}] {message}")


class Test(object):
    pass


# 使用例
if __name__ == "__main__":
    singleton1 = Singleton()
    singleton1.value = "First Instance"

    singleton2 = Singleton()

    print(singleton1 is singleton2)  # True
    print(singleton2.value)           # "First Instance"
    print(singleton1.created_at)      # 作成日時
    print(singleton2.created_at)      # 同じ作成日時

    print('--- Logger Example ---')
    logger1 = Logger()
    logger2 = Logger()
    logger1.log("This is a log message.")
    print(logger1 is logger2)  # True
    logger2.log("This is another log message.")

    print('---- Test Example ---')
    test1 = Test()
    test2 = Test()
    print(test1 is test2)  # False, TestクラスはSingletonではない
