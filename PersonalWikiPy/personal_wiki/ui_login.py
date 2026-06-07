"""Anmelde-Fenster."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from .auth import User, UserStore


class LoginDialog(tk.Toplevel):
    """Modales Anmeldefenster. Ergebnis steht danach in ``self.user``."""

    def __init__(self, master: tk.Misc, store: UserStore) -> None:
        super().__init__(master)
        self.store = store
        self.user: Optional[User] = None

        self.title("Personal Wiki — Anmeldung")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        frame = ttk.Frame(self, padding=20)
        frame.grid(sticky="nsew")

        ttk.Label(frame, text="Anmeldung", font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(0, 12)
        )

        ttk.Label(frame, text="Benutzername:").grid(row=1, column=0, sticky="w", pady=4)
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(frame, textvariable=self.name_var, width=28)
        name_entry.grid(row=1, column=1, pady=4)

        ttk.Label(frame, text="Passwort:").grid(row=2, column=0, sticky="w", pady=4)
        self.pwd_var = tk.StringVar()
        pwd_entry = ttk.Entry(frame, textvariable=self.pwd_var, width=28, show="•")
        pwd_entry.grid(row=2, column=1, pady=4)

        self.error_var = tk.StringVar()
        error_label = ttk.Label(frame, textvariable=self.error_var, foreground="#c0392b")
        error_label.grid(row=3, column=0, columnspan=2, pady=(4, 8))

        button_row = ttk.Frame(frame)
        button_row.grid(row=4, column=0, columnspan=2, sticky="e")
        ttk.Button(button_row, text="Abbrechen", command=self._cancel).grid(row=0, column=0, padx=4)
        ttk.Button(button_row, text="Anmelden", command=self._login).grid(row=0, column=1)

        # Komfort: Enter meldet an, Fokus auf Benutzername.
        self.bind("<Return>", lambda _e: self._login())
        self.bind("<Escape>", lambda _e: self._cancel())
        name_entry.focus_set()

        self._center_on(master)

    def _center_on(self, master: tk.Misc) -> None:
        self.update_idletasks()
        try:
            mx = master.winfo_rootx()
            my = master.winfo_rooty()
            mw = master.winfo_width()
            mh = master.winfo_height()
            w = self.winfo_width()
            h = self.winfo_height()
            x = mx + (mw - w) // 2
            y = my + (mh - h) // 2
            self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        except tk.TclError:
            pass

    def _login(self) -> None:
        name = self.name_var.get().strip()
        password = self.pwd_var.get()
        if not name:
            self.error_var.set("Bitte einen Benutzernamen eingeben.")
            return
        user = self.store.authenticate(name, password)
        if user is None:
            self.error_var.set("Benutzername oder Passwort ist falsch.")
            self.pwd_var.set("")
            return
        self.user = user
        self.destroy()

    def _cancel(self) -> None:
        self.user = None
        self.destroy()
