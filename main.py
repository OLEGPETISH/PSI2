import logging
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

from ticket_generator.app import TicketGeneratorApp


def main() -> None:
    project_dir = Path(__file__).resolve().parent
    logging.basicConfig(
        filename=project_dir / "ticket_generator.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        encoding="utf-8",
    )
    root = tk.Tk()
    try:
        TicketGeneratorApp(root, project_dir)
    except tk.TclError as error:
        root.destroy()
        messagebox.showerror("Ошибка интерфейса", str(error))
        return
    root.mainloop()


if __name__ == "__main__":
    main()
