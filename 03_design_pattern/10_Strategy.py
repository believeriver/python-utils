"""Strategy Pattern Example in Python.
The Strategy Pattern defines a family of algorithms, encapsulates each one, and makes them interchangeable.
This allows the algorithm to vary independently from clients that use it.
This example demonstrates the Strategy Pattern using different sorting algorithms.

複数のアルゴリズムを個別のクラスとして定義し、切り替えができるようにするパターン

・親クラスでクライアントにアクセスさせるための共通APIを定義する
・子クラスで、具体的なアルゴリズムを定義する

サンプル：複数の支払い方法が選択可能なショッピングカート
"""

from abc import ABC, abstractmethod


class PaymentStrategy(ABC):
    """支払い戦略の抽象クラス:Strategyに相当"""

    @abstractmethod
    def pay(self, amount: float) -> None:
        pass


class CreditCardPayment(PaymentStrategy):
    """クレジットカード支払い戦略:ConcreteStrategyに相当"""

    def __init__(self, card_number: str, card_holder: str, cvv: str, expiry_date: str):
        self.card_number = card_number
        self.card_holder = card_holder
        self.cvv = cvv
        self.expiry_date = expiry_date

    def pay(self, amount: float) -> None:
        print(f"Processing credit card payment of ${amount:.2f} for {self.card_holder}")


class PayPalPayment(PaymentStrategy):
    """PayPal支払い戦略:ConcreteStrategyに相当"""

    def __init__(self, email: str):
        self.email = email

    def pay(self, amount: float) -> None:
        print(f"Processing PayPal payment of ${amount:.2f} for {self.email}")


class ChashOnDeliveryPayment(PaymentStrategy):
    """代金引換支払い戦略:ConcreteStrategyに相当"""

    def pay(self, amount: float) -> None:
        print(f"Processing cash on delivery payment of ${amount:.2f}")


class ShoppingCart:
    """ショッピングカートクラス:Cntextに相当"""

    def __init__(self, payment_strategy: PaymentStrategy):
        self.payment_strategy = payment_strategy
        self.items = []

    def add_item(self, item: str, price: float) -> None:
        self.items.append((item, price))

    def calculate_total(self) -> float:
        return sum(price for item, price in self.items)

    def checkout(self) -> None:
        total_amount = self.calculate_total()
        self.payment_strategy.pay(total_amount)


# クライアントコードの例
if __name__ == "__main__":
    # クレジットカード支払いを選択
    credit_card_payment = CreditCardPayment(
        card_number="1234-5678-9012-3456",
        card_holder="John Doe",
        cvv="123",
        expiry_date="12/25"
    )
    cart1 = ShoppingCart(payment_strategy=credit_card_payment)
    cart1.add_item("Laptop", 999.99)
    cart1.add_item("Mouse", 49.99)
    cart1.checkout()
    print()
    # PayPal支払いを選択
    paypal_payment = PayPalPayment(email="user01@email.com")
    cart2 = ShoppingCart(payment_strategy=paypal_payment)
    cart2.add_item("Smartphone", 699.99)
    cart2.add_item("Headphones", 199.99)
    cart2.checkout()
    print()
    # 代金引換支払いを選択
    cod_payment = ChashOnDeliveryPayment()
    cart3 = ShoppingCart(payment_strategy=cod_payment)
    cart3.add_item("Book", 29.99)
    cart3.add_item("Pen", 3.99)
    cart3.checkout()


