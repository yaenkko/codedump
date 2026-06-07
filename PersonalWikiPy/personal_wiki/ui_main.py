"""Hauptfenster des Wikis."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Dict, Optional

from . import library, markdown_render
from .auth import User, UserStore
from .library import Library
from .ui_dialogs import (
    ChangePasswordDialog,
    ShareDialog,
    UserManagerDialog,
    prompt,
)


class MainWindow(tk.Toplevel):
    def __init__(self, master: tk.Misc, store: UserStore, user: User) -> None:
        super().__init__(master)
        self.store = store
        self.user = user
        self.logout_requested = False

        self.lib: Optional[Library] = None
        self._nodes: Dict[str, bool] = {}   # tree-iid -> is_directory
        self._current_file: Optional[Path] = None
        self._dirty = False
        self._loading = False
        self._preview_mode = False

        self.title("Personal Wiki")
        self.geometry("1100x700")
        self.minsize(720, 460)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_menu()
        self._build_toolbar()
        self._build_body()
        self._build_status()

        self._reload_library_choices()

    # ------------------------------------------------------------------ Aufbau

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)

        account = tk.Menu(menubar, tearoff=0)
        account.add_command(label="Passwort ändern…", command=self._change_password)
        account.add_separator()
        account.add_command(label="Abmelden", command=self._logout)
        account.add_command(label="Beenden", command=self._on_close)
        menubar.add_cascade(label="Konto", menu=account)

        edit = tk.Menu(menubar, tearoff=0)
        edit.add_command(label="Neue Kategorie", command=self._new_category)
        edit.add_command(label="Neue Seite", command=self._new_page)
        edit.add_command(label="Importieren…", command=self._import_files)
        edit.add_separator()
        edit.add_command(label="Speichern (Strg+S)", command=lambda: self._save(show=True))
        edit.add_command(label="Umbenennen", command=self._rename)
        edit.add_command(label="Löschen", command=self._delete)
        menubar.add_cascade(label="Bearbeiten", menu=edit)

        view = tk.Menu(menubar, tearoff=0)
        view.add_command(label="Vorschau ein/aus", command=self._toggle_preview)
        menubar.add_cascade(label="Ansicht", menu=view)

        share = tk.Menu(menubar, tearoff=0)
        share.add_command(label="Meine Bibliothek freigeben…", command=self._manage_shares)
        menubar.add_cascade(label="Freigabe", menu=share)

        if self.user.is_admin:
            admin = tk.Menu(menubar, tearoff=0)
            admin.add_command(label="Benutzerverwaltung…", command=self._manage_users)
            menubar.add_cascade(label="Admin", menu=admin)

        self.config(menu=menubar)
        self.bind("<Control-s>", lambda _e: self._save(show=True))

    def _build_toolbar(self) -> None:
        bar = ttk.Frame(self, padding=(6, 4))
        bar.pack(side="top", fill="x")

        ttk.Label(bar, text="Bibliothek:").pack(side="left")
        self.lib_var = tk.StringVar()
        self.lib_combo = ttk.Combobox(bar, textvariable=self.lib_var, state="readonly", width=34)
        self.lib_combo.pack(side="left", padx=(4, 12))
        self.lib_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_library_changed())

        self.btn_new_cat = ttk.Button(bar, text="Neue Kategorie", command=self._new_category)
        self.btn_new_cat.pack(side="left", padx=2)
        self.btn_new_page = ttk.Button(bar, text="Neue Seite", command=self._new_page)
        self.btn_new_page.pack(side="left", padx=2)
        self.btn_save = ttk.Button(bar, text="Speichern", command=lambda: self._save(show=True))
        self.btn_save.pack(side="left", padx=2)
        self.btn_import = ttk.Button(bar, text="Importieren…", command=self._import_files)
        self.btn_import.pack(side="left", padx=2)
        self.btn_rename = ttk.Button(bar, text="Umbenennen", command=self._rename)
        self.btn_rename.pack(side="left", padx=2)
        self.btn_delete = ttk.Button(bar, text="Löschen", command=self._delete)
        self.btn_delete.pack(side="left", padx=2)
        ttk.Button(bar, text="Vorschau", command=self._toggle_preview).pack(side="left", padx=2)

    def _build_body(self) -> None:
        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(side="top", fill="both", expand=True)

        # Linke Seite: Suche + Baum
        left = ttk.Frame(paned)
        self.search_var = tk.StringVar()
        search = ttk.Entry(left, textvariable=self.search_var)
        search.pack(side="top", fill="x", padx=4, pady=4)
        search.insert(0, "")
        self.search_var.trace_add("write", lambda *_: self._reload_tree())

        self.tree = ttk.Treeview(left, show="tree")
        self.tree.pack(side="top", fill="both", expand=True, padx=4, pady=(0, 4))
        self.tree.bind("<<TreeviewSelect>>", lambda _e: self._on_tree_select())
        left.configure(width=320)

        # Rechte Seite: Editor + Vorschau (umschaltbar)
        right = ttk.Frame(paned)
        self.editor_frame = ttk.Frame(right)
        self.editor_frame.pack(fill="both", expand=True)

        self.editor = tk.Text(self.editor_frame, wrap="word", undo=True,
                              font=("Consolas", 11))
        editor_scroll = ttk.Scrollbar(self.editor_frame, command=self.editor.yview)
        self.editor.configure(yscrollcommand=editor_scroll.set)
        editor_scroll.pack(side="right", fill="y")
        self.editor.pack(side="left", fill="both", expand=True)
        self.editor.bind("<<Modified>>", self._on_editor_modified)

        self.preview_frame = ttk.Frame(right)
        self.preview = tk.Text(self.preview_frame, wrap="word", state="disabled",
                               cursor="arrow", padx=8, pady=8)
        preview_scroll = ttk.Scrollbar(self.preview_frame, command=self.preview.yview)
        self.preview.configure(yscrollcommand=preview_scroll.set)
        preview_scroll.pack(side="right", fill="y")
        self.preview.pack(side="left", fill="both", expand=True)
        markdown_render.configure_tags(self.preview)

        paned.add(left, weight=0)
        paned.add(right, weight=1)

    def _build_status(self) -> None:
        self.status_var = tk.StringVar()
        status = ttk.Label(self, textvariable=self.status_var, relief="sunken",
                           anchor="w", padding=(6, 2))
        status.pack(side="bottom", fill="x")

    # ------------------------------------------------------------------ Bibliotheken

    def _reload_library_choices(self) -> None:
        usernames = [u.name for u in self.store.all_users()]
        self._lib_map: Dict[str, tuple[str, str]] = {}
        labels = []
        for owner, perm in library.accessible_libraries(self.user.name, usernames):
            label = self._lib_label(owner, perm)
            labels.append(label)
            self._lib_map[label] = (owner, perm)
        self.lib_combo.configure(values=labels)
        if labels:
            self.lib_var.set(labels[0])
            self._on_library_changed()

    def _lib_label(self, owner: str, perm: str) -> str:
        if perm == library.PERM_OWNER:
            return f"{owner} (meine)"
        recht = "Schreiben" if perm == library.PERM_WRITE else "Lesen"
        return f"{owner} (geteilt – {recht})"

    def _on_library_changed(self) -> None:
        self._save()  # vorherige Seite sichern
        label = self.lib_var.get()
        if label not in self._lib_map:
            return
        owner, perm = self._lib_map[label]
        self.lib = Library(owner, perm)
        self._current_file = None
        self._set_editor_text("")
        self._apply_permission_state()
        self._reload_tree()
        self._update_status()

    def _apply_permission_state(self) -> None:
        writable = bool(self.lib and self.lib.can_write)
        state = "normal" if writable else "disabled"
        for btn in (self.btn_new_cat, self.btn_new_page, self.btn_save,
                    self.btn_import, self.btn_rename, self.btn_delete):
            btn.configure(state=state)
        # Editor nur bei Schreibrecht bearbeitbar.
        self.editor.configure(state="normal" if writable else "disabled")

    # ------------------------------------------------------------------ Baum

    def _reload_tree(self) -> None:
        if self.lib is None:
            return
        flt = self.search_var.get().strip().lower()
        self.tree.delete(*self.tree.get_children())
        self._nodes.clear()
        self._add_children(self.lib.root, "", flt)
        if flt:
            self._expand_all()

    def _add_children(self, directory: Path, parent_iid: str, flt: str) -> bool:
        """Fügt den Inhalt eines Ordners hinzu. Gibt True zurück, wenn etwas passt."""
        added_any = False
        try:
            entries = sorted(directory.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except OSError:
            return False

        for entry in entries:
            if entry.name == library.SHARE_FILE:
                continue
            if entry.is_dir():
                iid = str(entry)
                node = self.tree.insert(parent_iid, "end", iid=iid,
                                        text="📁 " + entry.name, open=False)
                self._nodes[iid] = True
                has_match = self._add_children(entry, iid, flt)
                name_match = flt and flt in entry.name.lower()
                if flt and not has_match and not name_match:
                    self.tree.delete(iid)
                    self._nodes.pop(iid, None)
                else:
                    added_any = True
            elif entry.suffix.lower() == library.PAGE_EXT:
                title = entry.stem
                if flt and flt not in title.lower():
                    continue
                iid = str(entry)
                self.tree.insert(parent_iid, "end", iid=iid, text="📄 " + title)
                self._nodes[iid] = False
                added_any = True
        return added_any

    def _expand_all(self, parent: str = "") -> None:
        for child in self.tree.get_children(parent):
            self.tree.item(child, open=True)
            self._expand_all(child)

    def _selected(self) -> Optional[tuple[Path, bool]]:
        sel = self.tree.selection()
        if not sel:
            return None
        iid = sel[0]
        return Path(iid), self._nodes.get(iid, False)

    def _target_dir(self) -> Path:
        assert self.lib is not None
        sel = self._selected()
        if sel is None:
            return self.lib.root
        path, is_dir = sel
        return path if is_dir else path.parent

    def _on_tree_select(self) -> None:
        sel = self._selected()
        if sel is None:
            return
        path, is_dir = sel
        if is_dir:
            return
        self._open_page(path)

    # ------------------------------------------------------------------ Seiten

    def _open_page(self, path: Path) -> None:
        if self.lib is None:
            return
        self._save()  # aktuelle Seite zuerst sichern
        self._current_file = path
        self._set_editor_text(self.lib.read_page(path))
        if self._preview_mode:
            self._refresh_preview()
        self._update_status()

    def _set_editor_text(self, text: str) -> None:
        self._loading = True
        writable = bool(self.lib and self.lib.can_write)
        self.editor.configure(state="normal")
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", text)
        self.editor.edit_modified(False)
        self.editor.configure(state="normal" if writable else "disabled")
        self._dirty = False
        self._loading = False
        self._update_title()

    def _on_editor_modified(self, _event) -> None:
        if self._loading:
            self.editor.edit_modified(False)
            return
        if self.editor.edit_modified():
            self._dirty = True
            self._update_title()

    def _save(self, show: bool = False) -> None:
        if self.lib is None or self._current_file is None or not self._dirty:
            if show:
                self._set_status("Nichts zu speichern.")
            return
        if not self.lib.can_write:
            if show:
                self._set_status("Nur Leserecht – nicht gespeichert.")
            return
        try:
            content = self.editor.get("1.0", "end-1c")
            self.lib.write_page(self._current_file, content)
            self._dirty = False
            self.editor.edit_modified(False)
            self._update_title()
            if show:
                self._set_status(f"Gespeichert: {self._current_file.name}")
        except OSError as exc:
            messagebox.showerror("Fehler", f"Speichern fehlgeschlagen:\n{exc}", parent=self)

    # ------------------------------------------------------------------ Aktionen

    def _new_category(self) -> None:
        if not self._guard_write():
            return
        name = prompt(self, "Neue Kategorie", "Name der Kategorie:", "Neue Kategorie")
        if not name:
            return
        try:
            path = self.lib.create_category(self._target_dir(), name)
            self._reload_tree()
            self._select_path(path)
        except (OSError, PermissionError) as exc:
            messagebox.showerror("Fehler", str(exc), parent=self)

    def _new_page(self) -> None:
        if not self._guard_write():
            return
        title = prompt(self, "Neue Seite", "Titel der Seite:", "Neue Seite")
        if not title:
            return
        try:
            path = self.lib.create_page(self._target_dir(), title)
            self._reload_tree()
            self._select_path(path)
            self._open_page(path)
        except (OSError, PermissionError) as exc:
            messagebox.showerror("Fehler", str(exc), parent=self)

    def _import_files(self) -> None:
        if not self._guard_write():
            return
        files = filedialog.askopenfilenames(
            parent=self,
            title="Dateien ins Wiki importieren",
            filetypes=[("Text-/Markdown-Dateien", "*.md *.txt"), ("Alle Dateien", "*.*")],
        )
        if not files:
            return
        target = self._target_dir()
        last = None
        try:
            for f in files:
                last = self.lib.import_file(Path(f), target)
            self._reload_tree()
            if last:
                self._select_path(last)
                self._open_page(last)
            self._set_status(f"{len(files)} Datei(en) importiert.")
        except (OSError, PermissionError) as exc:
            messagebox.showerror("Fehler", str(exc), parent=self)

    def _rename(self) -> None:
        if not self._guard_write():
            return
        sel = self._selected()
        if sel is None:
            self._set_status("Bitte zuerst einen Eintrag auswählen.")
            return
        path, is_dir = sel
        current = path.name if is_dir else path.stem
        new_name = prompt(self, "Umbenennen", "Neuer Name:", current)
        if not new_name:
            return
        try:
            if not is_dir and path == self._current_file:
                self._save()
            new_path = self.lib.rename(path, new_name, is_dir)
            if not is_dir and path == self._current_file:
                self._current_file = new_path
            self._reload_tree()
            self._select_path(new_path)
        except (OSError, PermissionError) as exc:
            messagebox.showerror("Fehler", str(exc), parent=self)

    def _delete(self) -> None:
        if not self._guard_write():
            return
        sel = self._selected()
        if sel is None:
            self._set_status("Bitte zuerst einen Eintrag auswählen.")
            return
        path, is_dir = sel
        what = "die Kategorie samt Inhalt" if is_dir else "die Seite"
        name = path.name if is_dir else path.stem
        if not messagebox.askyesno("Löschen bestätigen",
                                   f"Soll {what} '{name}' wirklich gelöscht werden?",
                                   parent=self):
            return
        try:
            if not is_dir and path == self._current_file:
                self._current_file = None
                self._set_editor_text("")
            self.lib.delete(path, is_dir)
            self._reload_tree()
            self._set_status(f"Gelöscht: {name}")
        except (OSError, PermissionError) as exc:
            messagebox.showerror("Fehler", str(exc), parent=self)

    def _guard_write(self) -> bool:
        if self.lib is None:
            return False
        if not self.lib.can_write:
            messagebox.showinfo("Nur Lesen",
                                "Für diese Bibliothek hast du nur Leserecht.",
                                parent=self)
            return False
        return True

    # ------------------------------------------------------------------ Vorschau

    def _toggle_preview(self) -> None:
        self._preview_mode = not self._preview_mode
        if self._preview_mode:
            self._refresh_preview()
            self.editor_frame.pack_forget()
            self.preview_frame.pack(fill="both", expand=True)
        else:
            self.preview_frame.pack_forget()
            self.editor_frame.pack(fill="both", expand=True)

    def _refresh_preview(self) -> None:
        markdown_render.render(self.preview, self.editor.get("1.0", "end-1c"))

    # ------------------------------------------------------------------ Dialoge

    def _change_password(self) -> None:
        ChangePasswordDialog(self, self.store, self.user)

    def _manage_users(self) -> None:
        dlg = UserManagerDialog(self, self.store, self.user)
        self.wait_window(dlg)
        self._reload_library_choices()

    def _manage_shares(self) -> None:
        dlg = ShareDialog(self, self.store, self.user)
        self.wait_window(dlg)

    # ------------------------------------------------------------------ Sonstiges

    def _select_path(self, path: Path) -> None:
        iid = str(path)
        if self.tree.exists(iid):
            self.tree.see(iid)
            self.tree.selection_set(iid)

    def _update_title(self) -> None:
        name = self._current_file.stem if self._current_file else "Keine Seite"
        dirty = " *" if self._dirty else ""
        self.title(f"Personal Wiki — {self.user.name} — {name}{dirty}")

    def _set_status(self, text: str) -> None:
        self.status_var.set(text)

    def _update_status(self) -> None:
        if self.lib is None:
            return
        perm = {"owner": "Besitzer", "write": "Schreiben", "read": "Lesen"}.get(
            self.lib.permission, self.lib.permission)
        rolle = "Admin" if self.user.is_admin else "Nutzer"
        self._set_status(
            f"Angemeldet: {self.user.name} ({rolle})   |   "
            f"Bibliothek: {self.lib.owner} ({perm})   |   Ordner: {self.lib.root}")

    def _logout(self) -> None:
        self._save()
        self.logout_requested = True
        self.destroy()

    def _on_close(self) -> None:
        self._save()
        self.logout_requested = False
        self.destroy()
