from pathlib import Path
import random

from ticket_generator.assignment import TicketAssignmentService
from ticket_generator.journal import ResultJournal
from ticket_generator.models import Student, Ticket


def test_repeated_student_gets_first_ticket_and_adds_history(tmp_path: Path) -> None:
    journal = ResultJournal(tmp_path / "results.xlsx")
    tickets = {
        2: Ticket(2, ("A", "B", "C")),
        9: Ticket(9, ("D", "E", "F")),
    }
    service = TicketAssignmentService(journal, tickets, random.Random(4))
    student = Student("ФИЗ-1", "Петров", "Пётр")

    first = service.prepare(student)
    service.record(student, first)
    repeated = service.prepare(student)
    service.record(student, repeated)

    assert first.ticket_number in tickets
    assert first.is_repeat is False
    assert repeated.ticket_number == first.ticket_number
    assert repeated.is_repeat is True
    assert journal.find_first_ticket(student) == first.ticket_number
