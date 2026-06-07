"""Bibliotheken: pro Nutzer ein Ordner mit Kategorien und Markdown-Seiten.

Speichermodell (menschenlesbar und migrationsfreundlich):

    libraries/
        <nutzer>/
            .share.json            <- Freigaben dieser Bibliothek
            Kategorie A/           <- Kategorie  = Ordner
                Seite 1.md         <- Seite      = Markdown-Datei
            Kategorie B/
                Unterkategorie/    <- Unterkategorien sind möglich
                    Seite 2.md
            Startseite.md
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Dict, List

from . import config

PAGE_EXT = ".md"
SHARE_FILE = ".share.json"

# Berechtigungsstufen
PERM_OWNER = "owner"
PERM_WRITE = "write"
PERM_READ = "read"

_INVALID_CHARS = '<>:"/\\|?*'


def sanitize(name: str) -> str:
    """Entfernt für Datei-/Ordnernamen ungültige Zeichen."""
    name = name.strip()
    for ch in _INVALID_CHARS:
        name = name.replace(ch, "_")
    name = name.strip(". ")
    return name or "Unbenannt"


def library_root(owner: str) -> Path:
    path = config.libraries_dir() / sanitize(owner)
    path.mkdir(parents=True, exist_ok=True)
    return path


def delete_library(owner: str) -> None:
    """Entfernt die komplette Bibliothek eines Nutzers."""
    path = config.libraries_dir() / sanitize(owner)
    if path.exists():
        shutil.rmtree(path)


# ---------------------------------------------------------------------- Freigaben


def _share_path(owner: str) -> Path:
    return library_root(owner) / SHARE_FILE


def load_shares(owner: str) -> Dict[str, str]:
    """Gibt {nutzername: berechtigung} für eine Bibliothek zurück."""
    path = _share_path(owner)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {k.lower(): v for k, v in data.get("shared_with", {}).items()}
    except (json.JSONDecodeError, OSError):
        return {}


def save_shares(owner: str, shares: Dict[str, str]) -> None:
    path = _share_path(owner)
    path.write_text(
        json.dumps({"shared_with": shares}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def set_share(owner: str, user: str, permission: str) -> None:
    shares = load_shares(owner)
    shares[user.lower()] = permission
    save_shares(owner, shares)


def remove_share(owner: str, user: str) -> None:
    shares = load_shares(owner)
    shares.pop(user.lower(), None)
    save_shares(owner, shares)


def permission_for(owner: str, user: str) -> str | None:
    """Berechtigung eines Nutzers für die Bibliothek von ``owner``."""
    if owner.lower() == user.lower():
        return PERM_OWNER
    return load_shares(owner).get(user.lower())


def accessible_libraries(user: str, all_usernames: List[str]) -> List[tuple[str, str]]:
    """Liste (besitzer, berechtigung) aller für ``user`` zugänglichen Bibliotheken.

    Enthält immer die eigene Bibliothek und alle, die mit ``user`` geteilt wurden.
    """
    result: List[tuple[str, str]] = [(user, PERM_OWNER)]
    for owner in sorted(all_usernames, key=str.lower):
        if owner.lower() == user.lower():
            continue
        perm = load_shares(owner).get(user.lower())
        if perm:
            result.append((owner, perm))
    return result


# ---------------------------------------------------------------------- Eine Bibliothek


class Library:
    """Datei-Operationen für die Bibliothek eines bestimmten Besitzers."""

    def __init__(self, owner: str, permission: str) -> None:
        self.owner = owner
        self.permission = permission
        self.root = library_root(owner)

    @property
    def can_write(self) -> bool:
        return self.permission in (PERM_OWNER, PERM_WRITE)

    @property
    def is_owner(self) -> bool:
        return self.permission == PERM_OWNER

    # -- Lesen -----------------------------------------------------------------

    def read_page(self, path: Path) -> str:
        return path.read_text(encoding="utf-8") if path.exists() else ""

    # -- Schreiben (nur mit Schreibrecht) --------------------------------------

    def _require_write(self) -> None:
        if not self.can_write:
            raise PermissionError("Für diese Bibliothek besteht nur Leserecht.")

    def write_page(self, path: Path, content: str) -> None:
        self._require_write()
        path.write_text(content, encoding="utf-8")

    def create_category(self, parent: Path, name: str) -> Path:
        self._require_write()
        path = parent / sanitize(name)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def create_page(self, parent: Path, title: str) -> Path:
        self._require_write()
        parent.mkdir(parents=True, exist_ok=True)
        filename = sanitize(title)
        if not filename.lower().endswith(PAGE_EXT):
            filename += PAGE_EXT
        path = parent / filename
        if not path.exists():
            path.write_text(f"# {title}\n\n", encoding="utf-8")
        return path

    def import_file(self, source: Path, target_dir: Path) -> Path:
        self._require_write()
        target_dir.mkdir(parents=True, exist_ok=True)
        base = sanitize(source.stem)
        target = target_dir / (base + PAGE_EXT)
        counter = 1
        while target.exists():
            target = target_dir / f"{base} ({counter}){PAGE_EXT}"
            counter += 1
        shutil.copyfile(source, target)
        return target

    def rename(self, path: Path, new_name: str, is_dir: bool) -> Path:
        self._require_write()
        if is_dir:
            target = path.parent / sanitize(new_name)
        else:
            filename = sanitize(new_name)
            if not filename.lower().endswith(PAGE_EXT):
                filename += PAGE_EXT
            target = path.parent / filename
        path.rename(target)
        return target

    def delete(self, path: Path, is_dir: bool) -> None:
        self._require_write()
        if is_dir:
            if path.exists():
                shutil.rmtree(path)
        else:
            if path.exists():
                path.unlink()
