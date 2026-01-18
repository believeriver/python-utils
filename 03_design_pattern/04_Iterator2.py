from typing import List


class Patient(object):
    def __init__(self, _id: int, _name: str) -> None:
        self.id = _id
        self.name = _name

    def __repr__(self):
        return f"Patient(id={self.id}, name='{self.name}')"


class WaitingRoom(object):
    def __init__(self):
        self._patients = []

    def check_in(self, patient: Patient) -> None:
        self._patients.append(patient)

    def __iter__(self):
        return WaitingRoomIterator(self._patients)


class WaitingRoomIterator(object):
    def __init__(self, patients: List[Patient]) -> None:
        self._patients = patients
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._index < len(self._patients):
            patient = self._patients[self._index]
            self._index += 1
            return patient
        else:
            raise StopIteration


# Example usage
if __name__ == "__main__":
    waiting_room = WaitingRoom()
    waiting_room.check_in(Patient(1, "Alice"))
    waiting_room.check_in(Patient(2, "Bob"))
    waiting_room.check_in(Patient(3, "Charlie"))

    for patient in waiting_room:
        print(patient)

