from abc import ABCMeta, abstractmethod


class TestTemplate(metaclass=ABCMeta):
    def __init__(self):
        self._name= 'template'
        self.setup()
        self.execute()
        self.teardown()

    @abstractmethod
    def setup(self):
        pass

    @abstractmethod
    def execute(self):
        pass

    def teardown(self):
        print(f'{self._name}: teardown')


class ItemServiceTest(TestTemplate):
    def setup(self):
        print('ItemServiceTest setup')

    def execute(self):
        print('ItemServiceTest execute')


class UserServiceTest(TestTemplate):
    def setup(self):
        print('UserServiceTest setup')

    def execute(self):
        print('UserServiceTest execute')


if __name__ == '__main__':
    item_test = ItemServiceTest()
    print('')
    user_test = UserServiceTest()

