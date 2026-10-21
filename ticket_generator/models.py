from dataclasses import dataclass


@dataclass(frozen=True)
class Student:
    group: str
    surname: str
    first_name: str

    @property
    def display_name(self) -> str:
        return f"{self.surname} {self.first_name}"


@dataclass(frozen=True)
class Ticket:
    number: int
    questions: tuple[str, str, str]


@dataclass(frozen=True)
class Assignment:
    ticket_number: int
    is_repeat: bool
