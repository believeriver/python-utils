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


def marge_sort(numbers: List[int]) -> List[int]:
    if len(numbers) <= 1:
        return numbers
    center = len(numbers) // 2
    left = marge_sort(numbers[:center])
    right = marge_sort(numbers[center:])

    marge_sort(left)
    marge_sort(right)

    i = j = k = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            numbers[k] = left[i]
            i += 1
        else:
            numbers[k] = right[j]
            j += 1
        k += 1
    while i < len(left):
        numbers[k] = left[i]
        i += 1
        k += 1

    while j < len(right):
        numbers[k] = right[j]
        j += 1
        k += 1

    return numbers




if __name__ == "__main__":
    arr = [2, 5, 1, 8, 7, 3]
    import random
    numbers = [random.randint(1, 100) for _ in range(10)]
    print(f'Before sorting: {numbers}')
    print(f'bubble:         {bubble_sort(numbers)}')
    print(f'selection:      {selection_sort(numbers)}')
    print(f'marge:          {marge_sort(numbers)}')
