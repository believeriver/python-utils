#　与えられたリストの平均値を計算する関数
def calculate_average(numbers):
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)


# テストコード
if __name__ == "__main__":
    test_list = [10, 20, 30, 40, 50]
    average = calculate_average(test_list)
    print(f"The average of {test_list} is {average}")

