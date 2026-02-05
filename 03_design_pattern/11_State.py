"""
State Design Pattern Example in Python
The State Pattern allows an object to alter its behavior when its internal state changes.
This example demonstrates the State Pattern using a simple traffic light system.
状態に応じてオブジェクトの振る舞いを変えるパターン
・状態ごとにクラスを定義し、状態遷移を管理する
・状態クラスは共通のインターフェースを持つ
・コンテキストクラスは状態クラスを保持し、状態に応じた振る舞いを委譲する
サンプル：信号機の状態管理
"""
from abc import ABC, abstractmethod
class TrafficLightState(ABC):
    """信号機の状態の抽象クラス:Stateに相当"""

    @abstractmethod
    def change(self, traffic_light: 'TrafficLight') -> None:
        pass
    @abstractmethod
    def report(self) -> str:
        pass


class RedLightState(TrafficLightState):
    """赤信号状態:ConcreteStateに相当"""

    def change(self, traffic_light: 'TrafficLight') -> None:
        traffic_light.state = GreenLightState()

    def report(self) -> str:
        return "Red Light - Stop"


class GreenLightState(TrafficLightState):
    """青信号状態:ConcreteStateに相当"""

    def change(self, traffic_light: 'TrafficLight') -> None:
        traffic_light.state = YellowLightState()

    def report(self) -> str:
        return "Green Light - Go"


class YellowLightState(TrafficLightState):
    """黄信号状態:ConcreteStateに相当"""

    def change(self, traffic_light: 'TrafficLight') -> None:
        traffic_light.state = RedLightState()

    def report(self) -> str:
        return "Yellow Light - Caution"


class TrafficLight:
    """信号機クラス:Contextに相当"""

    def __init__(self) -> None:
        self.state: TrafficLightState = RedLightState()

    def change(self) -> None:
        self.state.change(self)

    def report(self) -> str:
        return self.state.report()

if __name__ == "__main__":
    traffic_light = TrafficLight()

    for _ in range(6):
        print(traffic_light.report())
        traffic_light.change()

