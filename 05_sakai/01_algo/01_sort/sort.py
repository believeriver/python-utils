from typing import List


def bubble_sort(numbers: List[int]) -> List[int]:
    limit = len(numbers)
    for i in range(1, limit):
        for j in range(0, limit - i):
            if numbers[j] > numbers[j + 1]:
                # Swap
                numbers[j], numbers[j + 1] = numbers[j + 1], numbers[j]
    return numbers


def selection_sort(numbers: List[int]) -> List[int]:
    size = len(numbers)
    for i in range(size):
        min_index = i
        for j in range(i+1, size):
            if numbers[j] < numbers[min_index]:
                min_index = j
        # Swap
        numbers[i], numbers[min_index] = numbers[min_index], numbers[i]
    return numbers


if __name__ == "__main__":
    arr = [2, 5, 1, 8, 7, 3]
    print(f'Before sorting: {arr}')
    print(f'bubble:         {bubble_sort(arr)}')
    print(f'selection:      {selection_sort(arr)}')
