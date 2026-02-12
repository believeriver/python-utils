"""
Composite Design Pattern Example in Python
This example demonstrates the Composite Design Pattern,
which allows you to compose objects into tree structures
to represent part-whole hierarchies.
It lets clients treat individual objects and compositions of objects uniformly.

ツリー構造を持つデータに再起的な処理を行えるようにするパターン

ディレクトリツリー、組織改装、DOMツリーなどに利用される
"""

from abc import ABC, abstractmethod
from typing import List


# Component
class Entry(ABC):
    def __init__(self, name: str):
        self.__name = name

    @property
    def name(self):
        return self.__name

    @abstractmethod
    def get_sizes(self):
        pass

    @abstractmethod
    def remove(self):
        pass


# Leaf
class File(Entry):
    def __init__(self, name: str, size: int):
        super().__init__(name)
        self.__size = size

    def get_sizes(self):
        return self.__size

    def remove(self):
        print(f"Removing file: {self.name}")


# Composite
class Directory(Entry):
    def __init__(self, name: str):
        super().__init__(name)
        self.__entries: List[Entry] = []

    def add(self, entry: Entry):
        self.__entries.append(entry)

    def get_sizes(self):
        total_size = 0
        for entry in self.__entries:
            total_size += entry.get_sizes()
        return total_size

    def remove(self):
        print(f"Removing directory: {self.name}")
        for entry in self.__entries:
            entry.remove()
        self.__entries.clear()


def client(_entry: Entry):
    print(f"Total size of '{_entry.name}': {_entry.get_sizes()} bytes")
    _entry.remove()


# Client code
if __name__ == "__main__":
    # Create files
    file1 = File("file1.txt", 100)
    file2 = File("file2.txt", 200)

    # Create a directory and add files to it
    dir1 = Directory("dir1")
    dir1.add(file1)
    dir1.add(file2)

    # Create another file
    file3 = File("file3.txt", 300)

    # Create a root directory and add dir1 and file3 to it
    root_dir = Directory("root")
    root_dir.add(dir1)
    root_dir.add(file3)

    # Use the client function to operate on the root directory
    client(root_dir)