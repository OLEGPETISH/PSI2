import random
from collections.abc import Mapping

from ticket_generator.journal import ResultJournal
from ticket_generator.models import Assignment, Student, Ticket


class TicketAssignmentService:
    def __init__(
        self,
        journal: ResultJournal,
        tickets: Mapping[int, Ticket],
        rng: random.Random | None = None,
    ) -> None:
        self._journal = journal
        self._tickets = tickets
        self._rng = rng or random.Random()

    def prepare(self, student: Student) -> Assignment:
        first_number = self._journal.find_first_ticket(student)
        if first_number is not None:
            return Assignment(first_number, True)
        return Assignment(self._rng.choice(tuple(self._tickets)), False)

    def record(self, student: Student, assignment: Assignment) -> None:
        self._journal.append(student, assignment)
