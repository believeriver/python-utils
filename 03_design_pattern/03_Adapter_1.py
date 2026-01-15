from abc import ABCMeta, abstractmethod
from typing import List, Dict


class Target(metaclass=ABCMeta):
    @abstractmethod
    def get_csv_data(self) -> str:
        pass


class NewLibrary(object):
    @staticmethod
    def get_json_data() -> List[Dict[str, str]]:
        return [
            {
                "data1": "Json_data_A",
                "data2": "Json_data_B",
            },
            {
                "data1": "Json_data_C",
                "data2": "Json_data_D",
            },
        ]


class JsonToCsvAdapter(NewLibrary, Target):
    def get_csv_data(self) -> str:
        json_data = self.get_json_data()

        header = ",".join(list(json_data[0].keys())) + "\n"
        body = "\n".join([",".join(list(d.values()))for d in json_data])

        return header + body


if __name__ == '__main__':
    adaptee = NewLibrary()
    print("=== Adaptee data")
    print(adaptee.get_json_data())
    print("")

    adapter = JsonToCsvAdapter()
    print("=== Adapter converted data")
    print(adapter.get_csv_data())