"""Dialoge: Benutzerverwaltung (Admin), Freigaben und einfache Eingaben."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from typing import Optional

from . import library
from .auth import ROLE_ADMIN, ROLE_USER, User, UserStore


def prompt(master: tk.Misc, title: str, label: str, initial: str = "") -> Optional[str]:
    """Einfache Texteingabe. Gibt None bei Abbruch zurück."""
    value = simpledialog.askstring(title, label, initialvalue=initial, parent=master)
    if value is None:
        return None
    value = value.strip()
    return value or None


class ChangePasswordDialog(tk.Toplevel):
    """Lässt einen Nutzer sein eigenes Passwort ändern."""

    def __init__(self, master: tk.Misc, store: UserStore, user: User) -> None:
        super().__init__(master)
        self.store = store
        self.user = user
        self.title("Passwort ändern")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        frame = ttk.Frame(self, padding=16)
        frame.grid()

        ttk.Label(frame, text="Aktuelles Passwort:").grid(row=0, column=0, sticky="w", pady=4)
        self.old_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.old_var, show="•", width=26).grid(row=0, column=1, pady=4)

        ttk.Label(frame, text="Neues Passwort:").grid(row=1, column=0, sticky="w", pady=4)
        self.new_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.new_var, show="•", width=26).grid(row=1, column=1, pady=4)

        ttk.Label(frame, text="Neues Passwort (Wdh.):").grid(row=2, column=0, sticky="w", pady=4)
        self.rep_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.rep_var, show="•", width=26).grid(row=2, column=1, pady=4)

        row = ttk.Frame(frame)
        row.grid(row=3, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(row, text="Abbrechen", command=self.destroy).grid(row=0, column=0, padx=4)
        ttk.Button(row, text="Speichern", command=self._save).grid(row=0, column=1)

    def _save(self) -> None:
        if self.store.authenticate(self.user.name, self.old_var.get()) is None:
            messagebox.showerror("Fehler", "Das aktuelle Passwort ist falsch.", parent=self)
            return
        if self.new_var.get() != self.rep_var.get():
            messagebox.showerror("Fehler", "Die neuen Passwörter stimmen nicht überein.", parent=self)
            return
        if not self.new_var.get():
            messagebox.showerror("Fehler", "Das Passwort darf nicht leer sein.", parent=self)
            return
        self.store.set_password(self.user.name, self.new_var.get())
        messagebox.showinfo("Erledigt", "Passwort geändert.", parent=self)
        self.destroy()


class UserManagerDialog(tk.Toplevel):
    """Admin-Dialog: Nutzer anlegen, löschen, Rolle ändern, Passwort zurücksetzen."""

    def __init__(self, master: tk.Misc, store: UserStore, current: User) -> None:
        super().__init__(master)
        self.store = store
        self.current = current
        self.title("Benutzerverwaltung")
        self.geometry("520x360")
        self.transient(master)
        self.grab_set()

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)

        columns = ("name", "role", "created")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=10)
        self.tree.heading("name", text="Benutzer")
        self.tree.heading("role", text="Rolle")
        self.tree.heading("created", text="Erstellt")
        self.tree.column("name", width=160)
        self.tree.column("role", width=80, anchor="center")
        self.tree.column("created", width=180)
        self.tree.pack(fill="both", expand=True)

        button_row = ttk.Frame(frame)
        button_row.pack(fill="x", pady=(10, 0))
        ttk.Button(button_row, text="Neuer Nutzer…", command=self._add).pack(side="left")
        ttk.Button(button_row, text="Passwort zurücksetzen…", command=self._reset_pwd).pack(side="left", padx=4)
        ttk.Button(button_row, text="Rolle umschalten", command=self._toggle_role).pack(side="left", padx=4)
        ttk.Button(button_row, text="Löschen", command=self._delete).pack(side="left", padx=4)
        ttk.Button(button_row, text="Schließen", command=self.destroy).pack(side="right")

        self._refresh()

    def _refresh(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for u in self.store.all_users():
            self.tree.insert("", "end", iid=u.name, values=(u.name, u.role, u.created))

    def _selected_name(self) -> Optional[str]:
        sel = self.tree.selection()
        return sel[0] if sel else None

    def _add(self) -> None:
        name = prompt(self, "Neuer Nutzer", "Benutzername:")
        if not name:
            return
        if self.store.exists(name):
            messagebox.showerror("Fehler", "Dieser Benutzer existiert bereits.", parent=self)
            return
        password = simpledialog.askstring("Neuer Nutzer", f"Passwort für '{name}':",
                                          show="•", parent=self)
        if not password:
            return
        make_admin = messagebox.askyesno("Rolle", "Soll dieser Nutzer Administrator sein?", parent=self)
        try:
            self.store.create_user(name, password, ROLE_ADMIN if make_admin else ROLE_USER)
            library.library_root(name)  # leere Bibliothek anlegen
            self._refresh()
        except ValueError as exc:
            messagebox.showerror("Fehler", str(exc), parent=self)

    def _reset_pwd(self) -> None:
        name = self._selected_name()
        if not name:
            return
        password = simpledialog.askstring("Passwort zurücksetzen",
                                          f"Neues Passwort für '{name}':",
                                          show="•", parent=self)
        if not password:
            return
        try:
            self.store.set_password(name, password)
            messagebox.showinfo("Erledigt", "Passwort wurde gesetzt.", parent=self)
        except ValueError as exc:
            messagebox.showerror("Fehler", str(exc), parent=self)

    def _toggle_role(self) -> None:
        name = self._selected_name()
        if not name:
            return
        user = self.store.get(name)
        if user is None:
            return
        new_role = ROLE_USER if user.is_admin else ROLE_ADMIN
        try:
            self.store.set_role(name, new_role)
            self._refresh()
        except ValueError as exc:
            messagebox.showerror("Fehler", str(exc), parent=self)

    def _delete(self) -> None:
        name = self._selected_name()
        if not name:
            return
        if name.lower() == self.current.name.lower():
            messagebox.showerror("Fehler", "Du kannst dich nicht selbst löschen.", parent=self)
            return
        if not messagebox.askyesno(
            "Löschen bestätigen",
            f"Benutzer '{name}' und dessen Bibliothek wirklich löschen?",
            parent=self,
        ):
            return
        try:
            self.store.delete_user(name)
            library.delete_library(name)
            self._refresh()
        except ValueError as exc:
            messagebox.showerror("Fehler", str(exc), parent=self)


class ShareDialog(tk.Toplevel):
    """Lässt den Besitzer seine Bibliothek für andere Nutzer freigeben."""

    def __init__(self, master: tk.Misc, store: UserStore, owner: User) -> None:
        super().__init__(master)
        self.store = store
        self.owner = owner
        self.title(f"Freigaben — Bibliothek von {owner.name}")
        self.geometry("460x340")
        self.transient(master)
        self.grab_set()

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Deine Bibliothek ist freigegeben für:").pack(anchor="w")

        self.tree = ttk.Treeview(frame, columns=("user", "perm"), show="headings", height=8)
        self.tree.heading("user", text="Benutzer")
        self.tree.heading("perm", text="Recht")
        self.tree.column("user", width=220)
        self.tree.column("perm", width=140, anchor="center")
        self.tree.pack(fill="both", expand=True, pady=(4, 8))

        row = ttk.Frame(frame)
        row.pack(fill="x")
        ttk.Button(row, text="Freigeben…", command=self._add).pack(side="left")
        ttk.Button(row, text="Recht ändern", command=self._toggle_perm).pack(side="left", padx=4)
        ttk.Button(row, text="Entziehen", command=self._remove).pack(side="left", padx=4)
        ttk.Button(row, text="Schließen", command=self.destroy).pack(side="right")

        self._refresh()

    def _perm_label(self, perm: str) -> str:
        return "Schreiben" if perm == library.PERM_WRITE else "Lesen"

    def _refresh(self) -> None:
        self.tree.delete(*self.tree.get_children())
        shares = library.load_shares(self.owner.name)
        for user, perm in sorted(shares.items()):
            self.tree.insert("", "end", iid=user, values=(user, self._perm_label(perm)))

    def _selected(self) -> Optional[str]:
        sel = self.tree.selection()
        return sel[0] if sel else None

    def _add(self) -> None:
        # Auswahl aus den vorhandenen Nutzern (außer dem Besitzer selbst).
        candidates = [u.name for u in self.store.all_users()
                      if u.name.lower() != self.owner.name.lower()]
        if not candidates:
            messagebox.showinfo("Hinweis", "Es gibt keine weiteren Nutzer.", parent=self)
            return
        picker = _PickUserDialog(self, candidates)
        self.wait_window(picker)
        if picker.result is None:
            return
        name, write = picker.result
        library.set_share(self.owner.name, name,
                          library.PERM_WRITE if write else library.PERM_READ)
        self._refresh()

    def _toggle_perm(self) -> None:
        name = self._selected()
        if not name:
            return
        shares = library.load_shares(self.owner.name)
        current = shares.get(name, library.PERM_READ)
        new = library.PERM_READ if current == library.PERM_WRITE else library.PERM_WRITE
        library.set_share(self.owner.name, name, new)
        self._refresh()

    def _remove(self) -> None:
        name = self._selected()
        if not name:
            return
        library.remove_share(self.owner.name, name)
        self._refresh()


class _PickUserDialog(tk.Toplevel):
    """Hilfsdialog: einen Nutzer und das Recht auswählen."""

    def __init__(self, master: tk.Misc, candidates: list[str]) -> None:
        super().__init__(master)
        self.result: Optional[tuple[str, bool]] = None
        self.title("Bibliothek freigeben")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        frame = ttk.Frame(self, padding=14)
        frame.grid()

        ttk.Label(frame, text="Nutzer:").grid(row=0, column=0, sticky="w", pady=4)
        self.user_var = tk.StringVar(value=candidates[0])
        ttk.Combobox(frame, textvariable=self.user_var, values=candidates,
                     state="readonly", width=24).grid(row=0, column=1, pady=4)

        self.write_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Schreibrecht (sonst nur Lesen)",
                        variable=self.write_var).grid(row=1, column=0, columnspan=2,
                                                      sticky="w", pady=6)

        row = ttk.Frame(frame)
        row.grid(row=2, column=0, columnspan=2, sticky="e", pady=(8, 0))
        ttk.Button(row, text="Abbrechen", command=self.destroy).grid(row=0, column=0, padx=4)
        ttk.Button(row, text="Freigeben", command=self._ok).grid(row=0, column=1)

    def _ok(self) -> None:
        self.result = (self.user_var.get(), self.write_var.get())
        self.destroy()
