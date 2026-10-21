import logging
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from ticket_generator.assignment import TicketAssignmentService
from ticket_generator.data_sources import InputDataError, load_students, load_tickets
from ticket_generator.journal import JournalError, ResultJournal
from ticket_generator.models import Student, Ticket

logger = logging.getLogger(__name__)


class TicketGeneratorApp:
    def __init__(self, root: tk.Tk, data_dir: Path | None = None) -> None:
        self.root = root
        self.data_dir = data_dir or Path(__file__).resolve().parent.parent
        self.groups: dict[str, list[Student]] = {}
        self.tickets: dict[int, Ticket] = {}
        self.service: TicketAssignmentService | None = None
        self.student_options: dict[str, Student] = {}
        self.group_var = tk.StringVar()
        self.student_var = tk.StringVar()
        self._build_ui()
        self._load_data()

    def _build_ui(self) -> None:
        self.root.title("Билет — генератор экзаменационных билетов")
        self.root.geometry("760x570")
        self.root.minsize(650, 520)
        self.root.configure(bg="#F4F7FB")
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("TCombobox", padding=10, font=("Segoe UI", 11))
        style.configure(
            "Primary.TButton",
            background="#2563EB",
            foreground="white",
            font=("Segoe UI Semibold", 11),
            padding=(16, 12),
        )
        style.map("Primary.TButton", background=[("active", "#1D4ED8")])

        page = tk.Frame(self.root, bg="#F4F7FB", padx=42, pady=36)
        page.pack(fill="both", expand=True)
        tk.Label(
            page, text="Б И Л Е Т", bg="#F4F7FB", fg="#2563EB",
            font=("Segoe UI Semibold", 10),
        ).pack(anchor="w")
        tk.Label(
            page, text="Генератор экзаменационных билетов",
            bg="#F4F7FB", fg="#172554", font=("Segoe UI Semibold", 23),
        ).pack(anchor="w", pady=(8, 5))
        tk.Label(
            page, text="Выберите группу и студента — результат сразу сохранится в журнал.",
            bg="#F4F7FB", fg="#64748B", font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(0, 24))

        card = tk.Frame(
            page, bg="white", padx=27, pady=25,
            highlightbackground="#E2E8F0", highlightthickness=1,
        )
        card.pack(fill="x")
        self._label(card, "01", "Группа").pack(anchor="w")
        self.group_combo = ttk.Combobox(
            card, textvariable=self.group_var, state="disabled"
        )
        self.group_combo.pack(fill="x", pady=(9, 21))
        self.group_combo.bind("<<ComboboxSelected>>", self._group_changed)

        self._label(card, "02", "Студент").pack(anchor="w")
        self.student_combo = ttk.Combobox(
            card, textvariable=self.student_var, state="disabled"
        )
        self.student_combo.pack(fill="x", pady=(9, 21))
        self.student_combo.bind("<<ComboboxSelected>>", self._update_button)

        self.generate_button = ttk.Button(
            card, text="Сгенерировать билет", style="Primary.TButton",
            state="disabled", command=self._generate,
        )
        self.generate_button.pack(fill="x")
        self.status = tk.Label(
            page, text="Загрузка файлов…", bg="#F4F7FB", fg="#64748B",
            font=("Segoe UI", 9), wraplength=660, justify="left",
        )
        self.status.pack(anchor="w", pady=(15, 0))
        tk.Label(
            page, text="История результатов сохраняется после каждой выдачи.",
            bg="#F4F7FB", fg="#64748B", font=("Segoe UI", 9),
        ).pack(side="bottom", anchor="w", pady=(12, 0))

    @staticmethod
    def _label(parent: tk.Widget, number: str, title: str) -> tk.Frame:
        frame = tk.Frame(parent, bg="white")
        tk.Label(
            frame, text=number, bg="#EFF6FF", fg="#2563EB",
            font=("Segoe UI Semibold", 9), padx=8, pady=3,
        ).pack(side="left")
        tk.Label(
            frame, text=title, bg="white", fg="#172033",
            font=("Segoe UI Semibold", 11),
        ).pack(side="left", padx=9)
        return frame

    def _load_data(self) -> None:
        issues: list[str] = []
        try:
            journal = ResultJournal(self.data_dir / "results.xlsx")
        except (JournalError, OSError) as error:
            journal = None
            issues.append(f"Журнал: {error}")
            logger.exception("Не удалось подготовить журнал")
        try:
            self.groups = load_students(self.data_dir / "students.xlsx")
        except InputDataError as error:
            issues.append(str(error))
            logger.error("Ошибка файла студентов: %s", error)
        try:
            self.tickets = load_tickets(self.data_dir / "tickets.docx")
        except InputDataError as error:
            issues.append(str(error))
            logger.error("Ошибка файла билетов: %s", error)
        if journal is not None and self.tickets:
            self.service = TicketAssignmentService(journal, self.tickets)
        self.group_combo.configure(values=tuple(self.groups))
        if self.groups:
            self.group_combo.configure(state="readonly")
        if issues:
            self.status.configure(
                text="Проверьте исходные файлы и ticket_generator.log.", fg="#B45309"
            )
            messagebox.showerror(
                "Проверьте файлы",
                "\n\n".join(issues),
                parent=self.root,
            )
        elif not self.groups:
            self.status.configure(text="В файле нет листов с группами.", fg="#B45309")
        else:
            self.status.configure(
                text=f"Групп: {len(self.groups)} · билетов: {len(self.tickets)}",
                fg="#15803D",
            )

    def _group_changed(self, _event: tk.Event | None = None) -> None:
        students = self.groups.get(self.group_var.get(), [])
        self.student_var.set("")
        self.student_options = {s.display_name: s for s in students}
        self.student_combo.configure(
            values=tuple(self.student_options),
            state="readonly" if students else "disabled",
        )
        if not students:
            self.status.configure(
                text=f"В группе «{self.group_var.get()}» нет студентов.",
                fg="#64748B",
            )
        self._update_button()

    def _update_button(self, _event: tk.Event | None = None) -> None:
        enabled = (
            self.group_var.get()
            and self.student_var.get() in self.student_options
            and self.service is not None
        )
        self.generate_button.configure(state="normal" if enabled else "disabled")

    def _generate(self) -> None:
        if self.service is None:
            messagebox.showerror(
                "Приложение не готово",
                "Проверьте файлы данных и журнал.",
                parent=self.root,
            )
            return
        student = self.student_options.get(self.student_var.get())
        if student is None:
            self._update_button()
            return
        try:
            assignment = self.service.prepare(student)
        except (JournalError, OSError) as error:
            logger.exception("Не удалось прочитать журнал")
            messagebox.showerror(
                "Ошибка журнала", str(error), parent=self.root
            )
            return
        while True:
            try:
                self.service.record(student, assignment)
                break
            except PermissionError as error:
                logger.warning("Журнал заблокирован: %s", error)
                if not messagebox.askretrycancel(
                    "Журнал недоступен",
                    "Закройте results.xlsx в Excel и нажмите «Повторить».",
                    parent=self.root,
                ):
                    return
            except OSError as error:
                logger.exception("Не удалось сохранить результат")
                messagebox.showerror(
                    "Ошибка сохранения",
                    f"Не удалось записать results.xlsx:\n{error}",
                    parent=self.root,
                )
                return
        self._show_result(student, assignment)

    def _show_result(self, student: Student, assignment) -> None:
        ticket = self.tickets[assignment.ticket_number]
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Ваш билет № {ticket.number}")
        dialog.geometry("620x530")
        dialog.minsize(500, 430)
        dialog.configure(bg="#F4F7FB")
        dialog.transient(self.root)
        card = tk.Frame(
            dialog, bg="white", padx=28, pady=24,
            highlightbackground="#E2E8F0", highlightthickness=1,
        )
        card.pack(fill="both", expand=True, padx=20, pady=20)
        tk.Label(
            card, text="ВАШ БИЛЕТ", bg="#EFF6FF", fg="#2563EB",
            font=("Segoe UI Semibold", 9), padx=10, pady=5,
        ).pack(anchor="w")
        tk.Label(
            card, text=f"№ {ticket.number}", bg="white", fg="#172554",
            font=("Segoe UI Semibold", 30),
        ).pack(anchor="w", pady=(7, 0))
        repeat = "Повторная выдача · первоначальный номер сохранён" if assignment.is_repeat else "Новый билет назначен"
        tk.Label(
            card, text=f"{student.display_name} · {student.group}  |  {repeat}",
            bg="white", fg="#64748B", font=("Segoe UI", 9),
            wraplength=520, justify="left",
        ).pack(anchor="w", pady=(0, 14))
        for index, question in enumerate(ticket.questions, start=1):
            row = tk.Frame(
                card, bg="#F8FAFC", padx=12, pady=12,
                highlightbackground="#E7EDF5", highlightthickness=1,
            )
            row.pack(fill="x", pady=4)
            tk.Label(
                row, text=f"{index:02d}", bg="#F8FAFC", fg="#2563EB",
                font=("Segoe UI Semibold", 11),
            ).pack(side="left", anchor="n", padx=(0, 12))
            tk.Label(
                row, text=question, bg="#F8FAFC", fg="#172033",
                font=("Segoe UI", 10), wraplength=440, justify="left",
            ).pack(side="left", fill="x", expand=True)
        tk.Label(
            card, text="Результат сохранён в results.xlsx", bg="white",
            fg="#15803D", font=("Segoe UI Semibold", 9),
        ).pack(anchor="w", pady=(12, 8))

        def close_dialog() -> None:
            try:
                dialog.grab_release()
            except tk.TclError:
                pass
            dialog.destroy()
            self.student_var.set("")
            self._update_button()
            self.student_combo.focus_set()

        button = ttk.Button(
            card, text="Вернуться к выбору", style="Primary.TButton",
            command=close_dialog,
        )
        button.pack(fill="x", side="bottom")
        dialog.bind("<Escape>", lambda _event: close_dialog())
        dialog.protocol("WM_DELETE_WINDOW", close_dialog)
        dialog.grab_set()
        button.focus_set()
