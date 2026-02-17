"""
Proxy Pattern
The proxy pattern is a design pattern that provides a surrogate or placeholder for another object to control access
to it. It is often used to add an additional layer of functionality or to control access to a resource.
In the proxy pattern, you have a subject interface that defines the common behavior for both the real
subject and the proxy. The real subject is the original object that you want to control access to,
while the proxy is a class that implements the same interface and controls access to the real subject.
Here's a simple example in Python to illustrate the proxy pattern:

代理となるオブジェクトを通じて、間接的に目的のオブジェクトにアクセスするパターン
目的のオブジェクトへのアクセスを制御したり、追加の機能を提供したりするために使用される
目的のオブジェクトと同じインターフェースを持つ代理オブジェクトが、目的のオブジェクトへのアクセスを制御する
例）リモートオブジェクトへのアクセスを制御するリモートプロキシ
　　プロキシサーバ
　　ロギング、キャッシュ
"""

# サーバリクエストとロギングのアクセス制御


from abc import ABC, abstractmethod


class Server(ABC):
    @abstractmethod
    def handle(self, _user_id: str) -> None:
        pass


class RealServer(Server):
    def handle(self, _user_id: str) -> None:
        print(f"[INFO] Request processed for user: {_user_id}")


class ProxyServer(Server):
    def __init__(self, _server: Server):
        self.__server = _server

    def _authorize(self, _user_id: str) -> None:
        # 簡単な認証ロジック（例: user_idが"admin"の場合のみ許可）
        authorized_users = ["admin", "user1", "user2"]
        print(_user_id)
        if _user_id not in authorized_users:
            raise Exception(f"[ERR0R] proxy User {_user_id} is not authorized")

    def handle(self, _user_id: str) -> None:
        self._authorize(_user_id)
        print(f"[INFO] ProxyServer: {_user_id} Access granted, forwarding request to RealServer.")
        self.__server.handle(_user_id)
        print(f"[INFO] ProxyServer: {_user_id} Request handled by Server.")


def execute(_user_id: str):
    real_server = RealServer()
    proxy_server = ProxyServer(real_server)
    try:
        proxy_server.handle(_user_id= _user_id)
    except Exception as e:
        print(e)
    finally:
        print("[INFO] Request processing completed.")


if __name__ == "__main__":
    execute("admin")
    execute("user1")
    execute("user2")
    execute("unauthorized_user")




