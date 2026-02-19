
def bubble_sort(numbers):
    limit = len(numbers)
    for i in range(1, limit):
        for j in range(0, limit - i):
            if numbers[j] > numbers[j + 1]:
                # Swap
                numbers[j], numbers[j + 1] = numbers[j + 1], numbers[j]
    return numbers

if __name__ == "__main__":
    arr = [2, 5, 1, 8, 7, 3]
    print(bubble_sort(arr))
