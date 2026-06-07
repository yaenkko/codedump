"""Anwendungssteuerung: Anmeldung, Hauptfenster und Abmelde-Schleife."""

from __future__ import annotations

import tkinter as tk

from . import library
from .auth import UserStore
from .ui_login import LoginDialog
from .ui_main import MainWindow


def main() -> None:
    root = tk.Tk()
    root.withdraw()  # unsichtbares Wurzelfenster

    try:
        from tkinter import ttk
        ttk.Style().theme_use("vista")  # schöneres Aussehen unter Windows
    except tk.TclError:
        pass

    store = UserStore()

    while True:
        login = LoginDialog(root, store)
        root.wait_window(login)
        if login.user is None:
            break  # Anmeldung abgebrochen -> Programm beenden

        # Sicherstellen, dass die Bibliothek des Nutzers existiert.
        library.library_root(login.user.name)

        window = MainWindow(root, store, login.user)
        root.wait_window(window)

        if not window.logout_requested:
            break  # Fenster geschlossen -> beenden

    root.destroy()


if __name__ == "__main__":
    main()
