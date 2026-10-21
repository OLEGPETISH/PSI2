# Copilot Chat Prompt Specification

Use this detailed English specification with Copilot Chat. The development
environment is already configured; do not repeat Git, VS Code, or authentication
installation steps.

> Implement a modular Windows desktop application in Python 3.10+ with Tkinter
> for a Russian-language exam ticket generator. Runtime dependencies are
> `openpyxl` and `python-docx`.
>
> Read `students.xlsx` beside the application: each worksheet is a group, row 1
> contains headers, and rows 2+ contain surname in column A and first name in
> column B. Preserve empty groups, ignore blank rows, and log incomplete records.
> Read `tickets.docx` from the same folder. A ticket heading is a standalone
> paragraph `Билет N`; following numbered paragraphs such as `1. Question`
> contain its questions. Use the first three questions. Skip and log malformed
> headings, duplicate ticket numbers, and tickets containing fewer than three
> questions without stopping the parser.
>
> Populate a group dropdown at startup. Selecting a group populates a student
> dropdown with `Фамилия Имя`. Keep the generate button disabled until a group,
> a student, usable input data, and a valid result journal are available.
> Selecting an empty group must clear and disable the student dropdown.
> Generation opens a result dialog headed `Ваш билет № N` and shows exactly
> three questions. Escape and the close button close only this dialog, clear the
> selected student, and return to the selection UI.
>
> Create `results.xlsx` at first launch with these columns:
> `Группа`, `Фамилия`, `Имя`, `Номер билета`, `Дата и время`, `Повтор`.
> Identify students by exact (group, surname, first name). A returning student
> receives the number from the earliest matching journal row, and a new row
> with `Повтор=да` is appended. A new student gets a uniformly random valid
> ticket number and an appended row with `Повтор=нет`. Never overwrite prior
> result rows. Persist before showing the result.
>
> Missing/unreadable source files must display actionable errors without
> crashing the UI. On a write lock (for example, Excel opened on the journal),
> tell the user to close Excel and offer retry/cancel. Retrying must reuse the
> same prepared ticket. Validate existing journal headers instead of replacing
> malformed files. Log parser and journal problems.
>
> Keep data parsing, ticket assignment, and journal access separate from Tk
> widgets. Provide pytest coverage for Word parsing and malformed tickets,
> student lookup by group, append-only journal behavior, and repeat-assignment
> idempotency. Include a polished Russian README explaining formats, launch,
> tests, errors, and acceptance criteria. Do not include real student data.
