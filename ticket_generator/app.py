import logging
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from ticket_generator.assignment import TicketAssignmentService
from ticket_generator.data_sources import InputDataError, load_students, load_tickets
from ticket_generator.journal import JournalError, ResultJournal
from ticket_generator.models import Assignment, Student, Ticket

logger = logging.getLogger(__name__)

_COLORS = {
    "background": "#F4F3FA",
    "surface": "#FFFFFF",
    "ink": "#201D36",
    "muted": "#77748D",
    "navy": "#24213F",
    "navy_light": "#343052",
    "purple": "#7056F5",
    "purple_dark": "#5B42DE",
    "lavender": "#F0EDFF",
    "mint": "#29B994",
    "mint_light": "#E6F8F3",
    "coral": "#FF826F",
    "yellow": "#F5B945",
    "line": "#EAE8F1",
    "white": "#FFFFFF",
}


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
        self.root.geometry("1120x780")
        self.root.minsize(940, 700)
        self.root.configure(bg=_COLORS["background"])
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure(
            "TCombobox",
            padding=(13, 12),
            font=("Segoe UI", 11),
            foreground=_COLORS["ink"],
            fieldbackground="#FBFAFE",
            background="#FBFAFE",
            bordercolor=_COLORS["line"],
            lightcolor=_COLORS["line"],
            darkcolor=_COLORS["line"],
            arrowsize=14,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", "#FBFAFE")],
            foreground=[("readonly", _COLORS["ink"])],
        )
        style.configure(
            "Primary.TButton",
            background=_COLORS["purple"],
            foreground=_COLORS["white"],
            font=("Segoe UI Semibold", 12),
            padding=(18, 15),
            borderwidth=0,
            focusthickness=0,
        )
        style.map(
            "Primary.TButton",
            background=[
                ("disabled", "#D5D1E5"),
                ("active", _COLORS["purple_dark"]),
            ],
            foreground=[("disabled", "#FFFFFF")],
        )

        shell = tk.Frame(self.root, bg=_COLORS["background"])
        shell.pack(fill="both", expand=True)
        shell.grid_rowconfigure(0, weight=1)
        shell.grid_columnconfigure(1, weight=1)
        self._build_sidebar(shell)
        self._build_dashboard(shell)

    def _build_sidebar(self, parent: tk.Widget) -> None:
        sidebar = tk.Frame(parent, bg=_COLORS["navy"], width=252)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        brand = tk.Frame(sidebar, bg=_COLORS["navy"], padx=25, pady=27)
        brand.pack(fill="x")
        mark = tk.Canvas(
            brand, width=44, height=44, bg=_COLORS["navy"], highlightthickness=0
        )
        mark.pack(side="left")
        mark.create_oval(2, 2, 42, 42, fill=_COLORS["purple"], outline="")
        mark.create_text(
            22, 22, text="B", fill="white", font=("Segoe UI Semibold", 21)
        )
        brand_text = tk.Frame(brand, bg=_COLORS["navy"])
        brand_text.pack(side="left", padx=(11, 0))
        tk.Label(
            brand_text, text="БИЛЕТ", bg=_COLORS["navy"], fg="white",
            font=("Segoe UI Semibold", 15),
        ).pack(anchor="w")
        tk.Label(
            brand_text, text="EXAM STUDIO", bg=_COLORS["navy"], fg="#A29EBB",
            font=("Segoe UI Semibold", 7),
        ).pack(anchor="w", pady=(1, 0))

        tk.Label(
            sidebar, text="РАБОЧЕЕ ПРОСТРАНСТВО", bg=_COLORS["navy"],
            fg="#8885A4", font=("Segoe UI Semibold", 8),
        ).pack(anchor="w", padx=26, pady=(37, 12))
        active = tk.Frame(sidebar, bg=_COLORS["navy_light"], padx=13, pady=12)
        active.pack(fill="x", padx=14)
        tk.Label(
            active, text="▦", bg=_COLORS["navy_light"], fg="#C6BCFF",
            font=("Segoe UI", 15),
        ).pack(side="left")
        tk.Label(
            active, text="Выдача билетов", bg=_COLORS["navy_light"], fg="white",
            font=("Segoe UI Semibold", 10),
        ).pack(side="left", padx=(11, 0))

        tk.Label(
            sidebar, text="КАК ЭТО РАБОТАЕТ", bg=_COLORS["navy"],
            fg="#8885A4", font=("Segoe UI Semibold", 8),
        ).pack(anchor="w", padx=26, pady=(32, 12))
        steps = (
            ("01", "Выберите группу", "Список учебных групп", _COLORS["purple"]),
            ("02", "Найдите студента", "Укажите получателя", _COLORS["mint"]),
            ("03", "Получите билет", "Три вопроса для экзамена", _COLORS["coral"]),
        )
        for number, title, detail, accent in steps:
            step = tk.Frame(sidebar, bg=_COLORS["navy"], padx=25, pady=10)
            step.pack(fill="x")
            badge = tk.Canvas(
                step, width=32, height=32, bg=_COLORS["navy"], highlightthickness=0
            )
            badge.pack(side="left", anchor="n")
            badge.create_oval(2, 2, 30, 30, fill=_COLORS["navy_light"], outline="")
            badge.create_text(
                16, 16, text=number, fill=accent,
                font=("Segoe UI Semibold", 8),
            )
            copy = tk.Frame(step, bg=_COLORS["navy"])
            copy.pack(side="left", padx=(10, 0))
            tk.Label(
                copy, text=title, bg=_COLORS["navy"], fg="#ECEAF6",
                font=("Segoe UI Semibold", 9),
            ).pack(anchor="w")
            tk.Label(
                copy, text=detail, bg=_COLORS["navy"], fg="#9894AF",
                font=("Segoe UI", 8),
            ).pack(anchor="w", pady=(3, 0))

        spacer = tk.Frame(sidebar, bg=_COLORS["navy"])
        spacer.pack(fill="both", expand=True)
        note = tk.Frame(
            sidebar, bg="#302D4B", padx=15, pady=15,
            highlightbackground="#45415F", highlightthickness=1,
        )
        note.pack(fill="x", padx=16, pady=(10, 12))
        tk.Label(
            note, text="✦  УМНОЕ НАЗНАЧЕНИЕ", bg="#302D4B", fg="#C8BFFF",
            font=("Segoe UI Semibold", 8),
        ).pack(anchor="w")
        tk.Label(
            note, text="При повторном выборе студент получит свой первый билет.",
            bg="#302D4B", fg="#CECCDB", font=("Segoe UI", 8),
            justify="left", wraplength=185,
        ).pack(anchor="w", pady=(9, 0))
        decoration = tk.Canvas(
            sidebar, height=55, bg=_COLORS["navy"], highlightthickness=0
        )
        decoration.pack(fill="x", side="bottom")
        decoration.create_oval(174, 12, 214, 52, fill="#373353", outline="")
        decoration.create_oval(194, -3, 239, 42, fill="#403A63", outline="")
        decoration.create_oval(226, 24, 253, 51, fill=_COLORS["purple"], outline="")

    def _build_dashboard(self, parent: tk.Widget) -> None:
        content = tk.Frame(parent, bg=_COLORS["background"], padx=36, pady=24)
        content.grid(row=0, column=1, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(3, weight=1)

        topbar = tk.Frame(content, bg=_COLORS["background"])
        topbar.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        tk.Label(
            topbar, text="ПАНЕЛЬ УПРАВЛЕНИЯ", bg=_COLORS["background"],
            fg=_COLORS["muted"], font=("Segoe UI Semibold", 8),
        ).pack(side="left")
        self.live_badge = tk.Frame(
            topbar, bg=_COLORS["mint_light"], padx=11, pady=6
        )
        self.live_badge.pack(side="right")
        tk.Label(
            self.live_badge, text="●", bg=_COLORS["mint_light"],
            fg=_COLORS["mint"], font=("Segoe UI", 8),
        ).pack(side="left")
        self.live_text = tk.Label(
            self.live_badge, text="ГОТОВ К РАБОТЕ", bg=_COLORS["mint_light"],
            fg="#27846D", font=("Segoe UI Semibold", 8),
        )
        self.live_text.pack(side="left", padx=(6, 0))

        self.hero_canvas = tk.Canvas(
            content, height=162, bg=_COLORS["background"], highlightthickness=0
        )
        self.hero_canvas.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        self.hero_canvas.bind("<Configure>", self._draw_hero)
        self._draw_hero()

        stats = tk.Frame(content, bg=_COLORS["background"])
        stats.grid(row=2, column=0, sticky="ew", pady=(0, 16))
        for column in range(3):
            stats.grid_columnconfigure(column, weight=1, uniform="stats")
        self.group_count_value = self._stat_card(
            stats, 0, "ГРУППЫ", "—", "▦", "#7056F5", "#F0EDFF"
        )
        self.student_count_value = self._stat_card(
            stats, 1, "СТУДЕНТЫ", "—", "♙", "#21A984", "#E6F8F3"
        )
        self.ticket_count_value = self._stat_card(
            stats, 2, "БИЛЕТЫ", "—", "✧", "#E89234", "#FFF4E2"
        )

        card = tk.Frame(
            content, bg=_COLORS["surface"], padx=22, pady=18,
            highlightbackground=_COLORS["line"], highlightthickness=1,
        )
        card.grid(row=3, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        header = tk.Frame(card, bg=_COLORS["surface"])
        header.grid(row=0, column=0, sticky="ew", pady=(0, 13))
        icon = tk.Canvas(
            header, width=40, height=40, bg=_COLORS["surface"], highlightthickness=0
        )
        icon.pack(side="left")
        icon.create_oval(1, 1, 39, 39, fill=_COLORS["lavender"], outline="")
        icon.create_text(
            20, 20, text="✦", fill=_COLORS["purple"],
            font=("Segoe UI Semibold", 16),
        )
        heading = tk.Frame(header, bg=_COLORS["surface"])
        heading.pack(side="left", padx=(10, 0))
        tk.Label(
            heading, text="Кому выдаём билет?", bg=_COLORS["surface"],
            fg=_COLORS["ink"], font=("Segoe UI Semibold", 14),
        ).pack(anchor="w")
        tk.Label(
            heading, text="Выберите учебную группу и студента",
            bg=_COLORS["surface"], fg=_COLORS["muted"],
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(2, 0))

        selection = tk.Frame(card, bg=_COLORS["surface"])
        selection.grid(row=1, column=0, sticky="ew")
        selection.grid_columnconfigure(0, weight=1, uniform="selection")
        selection.grid_columnconfigure(1, weight=1, uniform="selection")
        group_field = tk.Frame(selection, bg=_COLORS["surface"])
        group_field.grid(row=0, column=0, sticky="ew", padx=(0, 9))
        student_field = tk.Frame(selection, bg=_COLORS["surface"])
        student_field.grid(row=0, column=1, sticky="ew", padx=(9, 0))
        self._label(group_field, "01", "Учебная группа").pack(
            anchor="w", pady=(0, 7)
        )
        self.group_combo = ttk.Combobox(
            group_field, textvariable=self.group_var, state="disabled"
        )
        self.group_combo.pack(fill="x")
        self.group_combo.bind("<<ComboboxSelected>>", self._group_changed)
        self._label(student_field, "02", "Студент").pack(
            anchor="w", pady=(0, 7)
        )
        self.student_combo = ttk.Combobox(
            student_field, textvariable=self.student_var, state="disabled"
        )
        self.student_combo.pack(fill="x")
        self.student_combo.bind("<<ComboboxSelected>>", self._update_button)

        self.selection_preview = tk.Frame(
            card, bg="#FBFAFE", padx=11, pady=8
        )
        self.selection_preview.grid(row=2, column=0, sticky="ew", pady=(12, 11))
        self.selection_avatar = tk.Canvas(
            self.selection_preview, width=33, height=33,
            bg="#FBFAFE", highlightthickness=0,
        )
        self.selection_avatar.pack(side="left")
        self.selection_avatar.create_oval(
            2, 2, 31, 31, fill="#E9E5F8", outline=""
        )
        self.selection_avatar_text = self.selection_avatar.create_text(
            16, 16, text="•", fill=_COLORS["purple"],
            font=("Segoe UI Semibold", 12),
        )
        preview_copy = tk.Frame(self.selection_preview, bg="#FBFAFE")
        preview_copy.pack(side="left", padx=(8, 0))
        tk.Label(
            preview_copy, text="ТЕКУЩИЙ ВЫБОР", bg="#FBFAFE",
            fg="#9995AA", font=("Segoe UI Semibold", 7),
        ).pack(anchor="w")
        self.selection_text = tk.Label(
            preview_copy, text="Сначала выберите группу",
            bg="#FBFAFE", fg=_COLORS["muted"],
            font=("Segoe UI Semibold", 9),
        )
        self.selection_text.pack(anchor="w", pady=(2, 0))

        self.generate_button = ttk.Button(
            card,
            text="✦   Сгенерировать мой билет",
            style="Primary.TButton",
            state="disabled",
            command=self._generate,
        )
        self.generate_button.grid(row=3, column=0, sticky="ew")

        self.status = tk.Label(
            content, text="Загрузка файлов…", bg=_COLORS["background"],
            fg=_COLORS["muted"], font=("Segoe UI", 9), wraplength=650,
            justify="left",
        )
        self.status.grid(row=4, column=0, sticky="w", pady=(11, 0))
        footer = tk.Frame(content, bg=_COLORS["background"])
        footer.grid(row=5, column=0, sticky="ew", pady=(10, 0))
        tk.Frame(footer, bg=_COLORS["line"], height=1).pack(fill="x", pady=(0, 8))
        tk.Label(
            footer,
            text="◈  Результаты сохраняются сразу  ·  Esc закрывает только окно билета",
            bg=_COLORS["background"], fg=_COLORS["muted"],
            font=("Segoe UI", 8),
        ).pack(anchor="w")

    def _draw_hero(self, _event: tk.Event | None = None) -> None:
        canvas = self.hero_canvas
        width = max(canvas.winfo_width(), 400)
        canvas.delete("all")
        canvas.create_rectangle(6, 8, width - 3, 157, fill="#E5E0F3", outline="")
        canvas.create_rectangle(2, 2, width - 7, 151, fill=_COLORS["purple"], outline="")
        canvas.create_oval(
            width - 210, -58, width - 24, 128, fill="#806AF8", outline=""
        )
        canvas.create_oval(
            width - 146, -31, width - 22, 93, fill="#947FFF", outline=""
        )
        canvas.create_oval(
            width - 104, 91, width - 46, 149, fill="#FF9A83", outline=""
        )
        canvas.create_oval(
            width - 259, 101, width - 202, 158, fill="#5D48D5", outline=""
        )
        canvas.create_polygon(
            width - 134, 25, width - 103, 64, width - 126, 112,
            width - 154, 74, fill="#B5A8FF", outline="",
        )
        canvas.create_text(
            31, 32, text="ВАШ ЭКЗАМЕН — ВАШ СТАРТ", anchor="w",
            fill="#D9D2FF", font=("Segoe UI Semibold", 8),
        )
        canvas.create_text(
            29, 67, text="Готовы вытянуть\nсвой билет?", anchor="w",
            fill="white", font=("Segoe UI Semibold", 21),
            justify="left",
        )
        canvas.create_text(
            31, 124, text="Пара кликов — и вопросы уже ждут вас.",
            anchor="w", fill="#E6E0FF", font=("Segoe UI", 9),
        )
        canvas.create_oval(
            width - 85, 29, width - 55, 59, fill="#FDBD52", outline=""
        )
        canvas.create_text(
            width - 70, 44, text="✦", fill="white",
            font=("Segoe UI", 14),
        )

    @staticmethod
    def _stat_card(
        parent: tk.Widget,
        column: int,
        title: str,
        value: str,
        icon_text: str,
        accent: str,
        pale: str,
    ) -> tk.Label:
        card = tk.Frame(
            parent, bg=_COLORS["surface"], padx=12, pady=9,
            highlightbackground=_COLORS["line"], highlightthickness=1,
        )
        card.grid(
            row=0, column=column, sticky="ew",
            padx=(0 if column == 0 else 5, 0 if column == 2 else 5),
        )
        icon = tk.Canvas(
            card, width=34, height=34, bg=_COLORS["surface"], highlightthickness=0
        )
        icon.pack(side="left")
        icon.create_oval(1, 1, 33, 33, fill=pale, outline="")
        icon.create_text(
            17, 17, text=icon_text, fill=accent,
            font=("Segoe UI Semibold", 14),
        )
        copy = tk.Frame(card, bg=_COLORS["surface"])
        copy.pack(side="left", padx=(7, 0))
        tk.Label(
            copy, text=title, bg=_COLORS["surface"], fg=_COLORS["muted"],
            font=("Segoe UI Semibold", 7),
        ).pack(anchor="w")
        value_label = tk.Label(
            copy, text=value, bg=_COLORS["surface"], fg=_COLORS["ink"],
            font=("Segoe UI Semibold", 15),
        )
        value_label.pack(anchor="w", pady=(1, 0))
        return value_label

    @staticmethod
    def _label(parent: tk.Widget, number: str, title: str) -> tk.Frame:
        frame = tk.Frame(parent, bg=_COLORS["surface"])
        tk.Label(
            frame, text=number, bg=_COLORS["lavender"], fg=_COLORS["purple"],
            font=("Segoe UI Semibold", 8), padx=8, pady=3,
        ).pack(side="left")
        tk.Label(
            frame, text=title, bg=_COLORS["surface"], fg=_COLORS["ink"],
            font=("Segoe UI Semibold", 10),
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
        self.group_count_value.configure(text=str(len(self.groups)))
        self.student_count_value.configure(
            text=str(sum(len(students) for students in self.groups.values()))
        )
        self.ticket_count_value.configure(text=str(len(self.tickets)))
        if self.groups:
            self.group_combo.configure(state="readonly")
        if issues:
            self.status.configure(
                text="Проверьте исходные файлы и ticket_generator.log.",
                fg="#C25B38",
            )
            self.live_badge.configure(bg="#FFF0ED")
            self.live_text.configure(
                text="НУЖНА ПРОВЕРКА",
                bg="#FFF0ED",
                fg="#C25B38",
            )
            messagebox.showerror(
                "Проверьте файлы",
                "\n\n".join(issues),
                parent=self.root,
            )
        elif not self.groups:
            self.status.configure(
                text="В файле нет листов с группами.", fg="#C25B38"
            )
            self.live_badge.configure(bg="#FFF0ED")
            self.live_text.configure(
                text="НЕТ ГРУПП",
                bg="#FFF0ED",
                fg="#C25B38",
            )
        else:
            self.status.configure(
                text="Файлы загружены — выберите группу, чтобы продолжить.",
                fg="#27846D",
            )

    def _group_changed(self, _event: tk.Event | None = None) -> None:
        group = self.group_var.get()
        students = self.groups.get(group, [])
        self.student_var.set("")
        self.student_options = {s.display_name: s for s in students}
        self.student_combo.configure(
            values=tuple(self.student_options),
            state="readonly" if students else "disabled",
        )
        self.selection_text.configure(
            text=(
                f"{group}  ·  {len(students)} "
                f"{'студент' if len(students) == 1 else 'студентов'}"
                if students
                else f"{group}  ·  пока без студентов"
            ),
            fg=_COLORS["ink"] if students else _COLORS["muted"],
        )
        self.selection_avatar.itemconfigure(
            self.selection_avatar_text,
            text=group[:1].upper() if group else "•",
        )
        if not students:
            self.status.configure(
                text=f"В группе «{group}» нет студентов — выберите другую группу.",
                fg=_COLORS["muted"],
            )
        self._update_button()

    def _update_button(self, _event: tk.Event | None = None) -> None:
        student = self.student_options.get(self.student_var.get())
        enabled = (
            self.group_var.get()
            and student is not None
            and self.service is not None
        )
        self.generate_button.configure(state="normal" if enabled else "disabled")
        if student is not None:
            self.selection_text.configure(
                text=f"{student.display_name}  ·  {student.group}",
                fg=_COLORS["ink"],
            )
            self.selection_avatar.itemconfigure(
                self.selection_avatar_text,
                text=student.first_name[:1].upper(),
            )
            if self.service is not None:
                self.status.configure(
                    text="Отлично! Всё готово — билет будет сохранён в журнал сразу.",
                    fg="#27846D",
                )

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

    def _show_result(self, student: Student, assignment: Assignment) -> None:
        ticket = self.tickets[assignment.ticket_number]
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Билет № {ticket.number} · ваш результат")
        dialog.geometry("750x710")
        dialog.minsize(590, 610)
        dialog.configure(bg=_COLORS["background"])
        dialog.transient(self.root)
        page = tk.Frame(
            dialog, bg=_COLORS["background"], padx=25, pady=23
        )
        page.pack(fill="both", expand=True)

        banner = tk.Canvas(
            page, height=190, bg=_COLORS["background"], highlightthickness=0
        )
        banner.pack(fill="x", pady=(0, 16))

        def draw_ticket_banner(event: tk.Event) -> None:
            width = max(event.width, 350)
            banner.delete("all")
            banner.create_rectangle(5, 8, width - 3, 184, fill="#E5E0F3", outline="")
            banner.create_rectangle(1, 2, width - 8, 177, fill=_COLORS["navy"], outline="")
            banner.create_oval(
                width - 236, -59, width - 39, 138, fill="#39345C", outline=""
            )
            banner.create_oval(
                width - 165, -31, width - 37, 97, fill=_COLORS["purple"], outline=""
            )
            banner.create_oval(
                width - 106, 108, width - 42, 172, fill=_COLORS["coral"], outline=""
            )
            banner.create_oval(
                width - 275, 123, width - 209, 189, fill="#2E896F", outline=""
            )
            banner.create_text(
                27, 33, text="ЭКЗАМЕНАЦИОННЫЙ БИЛЕТ", anchor="w",
                fill="#C8C2DE", font=("Segoe UI Semibold", 8),
            )
            banner.create_text(
                27, 91, text=f"№ {ticket.number}", anchor="w",
                fill="white", font=("Segoe UI Semibold", 40),
            )
            banner.create_text(
                28, 142, text="Три вопроса. Один уверенный ответ за раз.",
                anchor="w", fill="#D5D0E8", font=("Segoe UI", 9),
            )
            banner.create_text(
                width - 92, 55, text="✦", fill="#FFE4A5",
                font=("Segoe UI", 35),
            )

        banner.bind("<Configure>", draw_ticket_banner)

        identity = tk.Frame(
            page, bg=_COLORS["surface"], padx=15, pady=12,
            highlightbackground=_COLORS["line"], highlightthickness=1,
        )
        identity.pack(fill="x", pady=(0, 13))
        initials = f"{student.surname[:1]}{student.first_name[:1]}".upper()
        avatar = tk.Canvas(
            identity, width=43, height=43, bg=_COLORS["surface"],
            highlightthickness=0,
        )
        avatar.pack(side="left")
        avatar.create_oval(2, 2, 41, 41, fill=_COLORS["lavender"], outline="")
        avatar.create_text(
            21, 21, text=initials, fill=_COLORS["purple"],
            font=("Segoe UI Semibold", 12),
        )
        identity_copy = tk.Frame(identity, bg=_COLORS["surface"])
        identity_copy.pack(side="left", padx=(11, 0))
        tk.Label(
            identity_copy, text=student.display_name, bg=_COLORS["surface"],
            fg=_COLORS["ink"], font=("Segoe UI Semibold", 11),
        ).pack(anchor="w")
        tk.Label(
            identity_copy, text=f"Учебная группа  ·  {student.group}",
            bg=_COLORS["surface"], fg=_COLORS["muted"],
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(2, 0))
        state_bg = "#FFF0ED" if assignment.is_repeat else _COLORS["mint_light"]
        state_fg = "#C25B38" if assignment.is_repeat else "#27846D"
        state_text = "↻  ПОВТОР" if assignment.is_repeat else "✦  НОВЫЙ БИЛЕТ"
        tk.Label(
            identity, text=state_text, bg=state_bg, fg=state_fg,
            font=("Segoe UI Semibold", 8), padx=9, pady=7,
        ).pack(side="right")

        question_header = tk.Frame(page, bg=_COLORS["background"])
        question_header.pack(fill="x", pady=(1, 9))
        tk.Label(
            question_header, text="ВОПРОСЫ К БИЛЕТУ",
            bg=_COLORS["background"], fg=_COLORS["muted"],
            font=("Segoe UI Semibold", 8),
        ).pack(side="left")
        tk.Label(
            question_header, text="03 ВОПРОСА", bg=_COLORS["lavender"],
            fg=_COLORS["purple"], font=("Segoe UI Semibold", 7),
            padx=8, pady=4,
        ).pack(side="right")

        question_colors = (
            ("#F0EDFF", "#7056F5"),
            ("#E6F8F3", "#21A984"),
            ("#FFF2E8", "#E89234"),
        )
        for index, question in enumerate(ticket.questions, start=1):
            row = tk.Frame(
                page, bg=_COLORS["surface"], padx=14, pady=11,
                highlightbackground=_COLORS["line"], highlightthickness=1,
            )
            row.pack(fill="x", pady=4)
            pale, accent = question_colors[(index - 1) % len(question_colors)]
            number = tk.Canvas(
                row, width=38, height=38, bg=_COLORS["surface"],
                highlightthickness=0,
            )
            number.pack(side="left", anchor="n")
            number.create_oval(1, 1, 37, 37, fill=pale, outline="")
            number.create_text(
                19, 19, text=f"{index:02d}", fill=accent,
                font=("Segoe UI Semibold", 10),
            )
            tk.Label(
                row, text=question, bg=_COLORS["surface"], fg=_COLORS["ink"],
                font=("Segoe UI", 10), wraplength=560, justify="left",
                anchor="w",
            ).pack(side="left", fill="x", expand=True, padx=(12, 0))

        saved = tk.Frame(page, bg=_COLORS["mint_light"], padx=12, pady=9)
        saved.pack(fill="x", pady=(10, 10))
        tk.Label(
            saved, text="✓", bg=_COLORS["mint_light"], fg=_COLORS["mint"],
            font=("Segoe UI Semibold", 12),
        ).pack(side="left")
        tk.Label(
            saved, text="Билет уже сохранён в журнал результатов",
            bg=_COLORS["mint_light"], fg="#27846D",
            font=("Segoe UI Semibold", 9),
        ).pack(side="left", padx=(8, 0))

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
            page, text="←   Вернуться к выбору", style="Primary.TButton",
            command=close_dialog,
        )
        button.pack(fill="x", side="bottom", pady=(0, 1))
        dialog.bind("<Escape>", lambda _event: close_dialog())
        dialog.protocol("WM_DELETE_WINDOW", close_dialog)
        dialog.grab_set()
        button.focus_set()
