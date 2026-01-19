"""
Factory Method Design Pattern Example in Python
ファクトリーメソッドパターンは、オブジェクトの生成をサブクラスに委譲するデザインパターンです。
このパターンを使用すると、クライアントコードは具体的なクラスに依存せず、
インターフェースや抽象クラスを通じてオブジェクトを生成できます。

生成したいオブジェクトのコンストラクタを呼び出してインスタンスを生成しないで、
親クラスに定義されたファクトリーメソッドを呼び出してインスタンスを生成します。

生成に関するデザインパターン

・類似した複数種類のオブジェクトを生成する場合に有効
　オープンクローズドの原則に違反することなく、新しい種類のオブジェクトを追加できる
・生成するオブジェクトの具体的なクラスが不明な場合に有効
　createメソッドを呼び出すだけで複雑な生成ロジックを記述せずに生成可能
・Productの種類や生成手順が頻繁に変更される可能性がある場合、
　利用側とProductの結びつきが弱いので、変更に強い設計となる
"""
from abc import ABC , abstractmethod
from typing import List


class CreditCard(ABC):
    """Product Interface"""
    def __init__(self, _owner: str) -> None:
        self.__owner: str = _owner

    @property
    def owner(self) -> str:
        return self.__owner

    @abstractmethod
    def get_card_type(self) -> str:
        pass

    @abstractmethod
    def get_annual_charge(self) -> int:
        pass


class PlatinumCreditCard(CreditCard):
    """Concrete Product"""
    def get_card_type(self) -> str:
        return "Platinum"

    def get_annual_charge(self) -> int:
        return 30000


class  GoldCreditCard(CreditCard):
    """Concrete Product"""
    def get_card_type(self) -> str:
        return "Gold"

    def get_annual_charge(self) -> int:
        return 10000


class CreditCardFactory(ABC):
    """Creator Abstract Class"""
    @abstractmethod
    def create_credit_card(self, _owner: str) -> CreditCard:
        pass

    @abstractmethod
    def register_card(self, _credit_card: CreditCard) -> None:
        pass

    def create(self, _owner: str) -> CreditCard:
        credit_card = self.create_credit_card(_owner)
        self.register_card(credit_card)
        return credit_card

credit_card_database: List[CreditCard] = []

class PlatinumCreditCardFactory(CreditCardFactory):
    """Concrete Creator"""
    def create_credit_card(self, _owner: str) -> CreditCard:
        return PlatinumCreditCard(_owner)

    def register_card(self, _credit_card: CreditCard) -> None:
        credit_card_database.append(_credit_card)
        print(f"Registering { _credit_card.get_card_type() } card for { _credit_card.owner }")


class GoldCreditCardFactory(CreditCardFactory):
    """Concrete Creator"""
    def create_credit_card(self, _owner: str) -> CreditCard:
        return GoldCreditCard(_owner)

    def register_card(self, _credit_card: CreditCard) -> None:
        credit_card_database.append(_credit_card)
        print(f"Registering { _credit_card.get_card_type() } card for { _credit_card.owner }")


# Example usage
if __name__ == "__main__":
    platinum_factory = PlatinumCreditCardFactory()
    gold_factory = GoldCreditCardFactory()

    card1 = platinum_factory.create("Alice")
    card2 = gold_factory.create("Bob")

    print(f"{card1.owner} has a {card1.get_card_type()} card with an annual charge of {card1.get_annual_charge()}.")
    print(f"{card2.owner} has a {card2.get_card_type()} card with an annual charge of {card2.get_annual_charge()}.")

    print(f"Total registered cards: {len(credit_card_database)}")
    for _credit_card in credit_card_database:
        print(f"- { _credit_card.owner }: { _credit_card.get_card_type() }")