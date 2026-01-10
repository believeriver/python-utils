from abc import ABCMeta, abstractmethod


"""Dependency Inversion Principle Example
依存関係逆転の原則(DIP: Dependency Inversion Principle)
- 高水準モジュールは低水準モジュールに依存してはならない。両者は抽象に依存するべきである。
- 抽象は詳細に依存してはならない。詳細は抽象に依存するべきである。
"""

class User(object):
    pass


class IUserService(metaclass=ABCMeta):
    @abstractmethod
    def find_by_id(self, user_id: int) -> User:
        pass

    @abstractmethod
    def create(self, user: User) -> None:
        pass


class IUserRepository(metaclass=ABCMeta):
    @abstractmethod
    def find_by_id(self, user_id: int) -> User:
        pass

    @abstractmethod
    def create(self, user: User) -> None:
        pass


class UserController(object):
    def __init__(self, user_service: IUserService):
        self.__user_service = user_service

    def create_user(self, user: User) -> None:
        self.__user_service.create(user)

    def find_user(self, user_id: int) -> User:
        return self.__user_service.find_by_id(user_id)


class UserService(IUserService):
    def __init__(self, user_repository: IUserRepository):
        self.__user_repository = user_repository

    def find_by_id(self, user_id: int) -> User:
        return self.__user_repository.find_by_id(user_id)

    def create(self, user: User) -> None:
        self.__user_repository.create(user)


class UserRepository(IUserRepository):
    def find_by_id(self, user_id: int) -> User:
        print(f"ユーザーID {user_id} のユーザーをデータベースから取得しました。")
        return User()

    def create(self, user: User) -> None:
        print("新しいユーザーをデータベースに保存しました。")
        return user


if __name__ == '__main__':
    user_repository = UserRepository()
    user_service = UserService(user_repository)
    user_controller = UserController(user_service)

    new_user = User()
    user_controller.create_user(new_user)

    user = user_controller.find_user(1)
    # print(user)

