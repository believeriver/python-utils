class EmployeeData(object):
    def __init__(self, name: str, department: str):
        self.name = name
        self.department = department


class PayCalculator(object):
    @staticmethod
    def __get_regular_hours():
        print("給与計算専用の労働時間計算ロジック")

    def calculate_pay(self, _employee_data: EmployeeData):
        self.__get_regular_hours()
        print(f"{_employee_data.name}の給与を計算しました")


class HourReporter(object):
    @staticmethod
    def __get_regular_hours():
        print("労働時間レポート専用の労働時間計算ロジック")

    def calculate_pay(self, _employee_data: EmployeeData):
        self.__get_regular_hours()
        print(f"{_employee_data.name}の労働時間をレポートしましたV2")


class EmployeeRepository(object):
    def save(self):
        pass


if __name__ == '__main__':
    employee_data = EmployeeData("Suzuki", "develop")
    pay_calculator = PayCalculator()
    hour_reporter = HourReporter()

    print("経理部門")
    pay_calculator.calculate_pay(employee_data)

    print("")
    print("人事部門")
    hour_reporter.calculate_pay(employee_data)