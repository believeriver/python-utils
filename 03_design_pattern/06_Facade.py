"""Facade Pattern Example
ファサードパターンは、複雑なサブシステムへの簡単なインターフェースを提供するデザインパターンです。
このパターンを使用すると、クライアントコードはサブシステムの詳細を知らなくても、
簡単に操作できるようになります。
ファサードクラスは、サブシステムの複数のクラスをまとめて扱い、
クライアントに対してシンプルなメソッドを提供します。

構造に関するデザインパターン
複雑な内部処理をまとめて、システムの外側に簡素化されたインターフェース（API）を提供する
ことで、利用者がシステムを簡単に利用できるようにするパターン

"""


class Product(object):
    @staticmethod
    def get_product(_name: str) -> None:
        print(f"{_name}を取得しました")


class Payment(object):
    @staticmethod
    def make_payment(_name: str) -> None:
        print(f"{_name}の支払いが完了しました")


class Invoice(object):
    @staticmethod
    def generate_invoice(_name: str) -> None:
        print(f"{_name}の請求書が発行されました")


class OrderFacade(object):
    def __init__(self):
        self._product = Product()
        self._payment = Payment()
        self._invoice = Invoice()

    def place_order(self, _product_name: str) -> None:
        print("注文処理を開始します")
        self._product.get_product(_product_name)
        self._payment.make_payment(_product_name)
        self._invoice.generate_invoice(_product_name)
        print("注文処理が完了しました")


# Example usage
if __name__ == "__main__":
    order_facade = OrderFacade()
    print('--- 顧客の注文 ---')
    order_facade.place_order("ノートパソコン")
    print('--- 顧客の注文 ---')
    order_facade.place_order("スマートフォン")
    print('--- 顧客の注文 ---')
    order_facade.place_order("タブレット")
