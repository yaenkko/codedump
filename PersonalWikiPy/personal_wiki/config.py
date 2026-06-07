"""Pfade und globale Konfiguration.

Alle Daten (Nutzerkonten und die Bibliotheken) liegen in einem einzigen
Datenordner. Standard ist ``Dokumente/PersonalWiki``. Für die Migration auf
einen anderen PC genügt es, diesen Ordner zu kopieren.
"""

from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "PersonalWiki"


def default_data_dir() -> Path:
    """Standard-Datenordner: Dokumente/PersonalWiki (plattformübergreifend)."""
    home = Path.home()
    documents = home / "Documents"
    base = documents if documents.exists() else home
    return base / APP_NAME


def data_dir() -> Path:
    """Aktueller Datenordner.

    Kann über die Umgebungsvariable ``PERSONAL_WIKI_DATA`` überschrieben werden
    (praktisch zum Testen oder für portable Installationen neben der EXE).
    """
    override = os.environ.get("PERSONAL_WIKI_DATA")
    path = Path(override) if override else default_data_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


def users_file() -> Path:
    """Datei mit allen Nutzerkonten."""
    return data_dir() / "users.json"


def libraries_dir() -> Path:
    """Ordner, der alle Nutzer-Bibliotheken enthält."""
    path = data_dir() / "libraries"
    path.mkdir(parents=True, exist_ok=True)
    return path
