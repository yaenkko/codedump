"""Nutzerverwaltung: Anmeldung, Passwörter (gehasht) und Rollen.

Passwörter werden niemals im Klartext gespeichert, sondern als PBKDF2-HMAC-SHA256
mit zufälligem Salt. Beim ersten Start wird automatisch ein Admin-Konto angelegt:

    Benutzername: admin
    Passwort:     admin   (bitte nach dem ersten Login ändern!)
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional

from . import config

ROLE_ADMIN = "admin"
ROLE_USER = "user"

_PBKDF2_ITERATIONS = 200_000

DEFAULT_ADMIN_NAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin"


@dataclass
class User:
    name: str
    salt: str
    pwd_hash: str
    role: str = ROLE_USER
    created: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    @property
    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN


def _hash_password(password: str, salt_hex: str) -> str:
    salt = bytes.fromhex(salt_hex)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS
    )
    return digest.hex()


class UserStore:
    """Lädt, speichert und verwaltet alle Nutzerkonten."""

    def __init__(self) -> None:
        self._users: Dict[str, User] = {}
        self.load()
        self._ensure_default_admin()

    # ------------------------------------------------------------------ Laden/Speichern

    def load(self) -> None:
        path = config.users_file()
        self._users = {}
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            for name, info in data.get("users", {}).items():
                self._users[name.lower()] = User(
                    name=info.get("name", name),
                    salt=info["salt"],
                    pwd_hash=info["hash"],
                    role=info.get("role", ROLE_USER),
                    created=info.get("created", ""),
                )
        except (json.JSONDecodeError, KeyError, OSError):
            # Beschädigte Datei nicht überschreiben, aber leer starten.
            self._users = {}

    def save(self) -> None:
        path = config.users_file()
        data = {
            "users": {
                u.name: {
                    "name": u.name,
                    "salt": u.salt,
                    "hash": u.pwd_hash,
                    "role": u.role,
                    "created": u.created,
                }
                for u in self._users.values()
            }
        }
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _ensure_default_admin(self) -> None:
        if not self._users:
            self.create_user(DEFAULT_ADMIN_NAME, DEFAULT_ADMIN_PASSWORD, ROLE_ADMIN)

    # ------------------------------------------------------------------ Abfragen

    def get(self, name: str) -> Optional[User]:
        return self._users.get(name.lower())

    def exists(self, name: str) -> bool:
        return name.lower() in self._users

    def all_users(self) -> list[User]:
        return sorted(self._users.values(), key=lambda u: u.name.lower())

    def admin_count(self) -> int:
        return sum(1 for u in self._users.values() if u.is_admin)

    def authenticate(self, name: str, password: str) -> Optional[User]:
        """Gibt den Nutzer bei korrektem Passwort zurück, sonst None."""
        user = self.get(name)
        if user is None:
            return None
        candidate = _hash_password(password, user.salt)
        # Konstantzeit-Vergleich gegen Timing-Angriffe.
        if secrets.compare_digest(candidate, user.pwd_hash):
            return user
        return None

    # ------------------------------------------------------------------ Verändern

    def create_user(self, name: str, password: str, role: str = ROLE_USER) -> User:
        name = name.strip()
        if not name:
            raise ValueError("Der Benutzername darf nicht leer sein.")
        if self.exists(name):
            raise ValueError(f"Der Benutzer '{name}' existiert bereits.")
        if not password:
            raise ValueError("Das Passwort darf nicht leer sein.")

        salt = os.urandom(16).hex()
        user = User(name=name, salt=salt, pwd_hash=_hash_password(password, salt), role=role)
        self._users[name.lower()] = user
        self.save()
        return user

    def set_password(self, name: str, new_password: str) -> None:
        user = self.get(name)
        if user is None:
            raise ValueError("Unbekannter Benutzer.")
        if not new_password:
            raise ValueError("Das Passwort darf nicht leer sein.")
        user.salt = os.urandom(16).hex()
        user.pwd_hash = _hash_password(new_password, user.salt)
        self.save()

    def set_role(self, name: str, role: str) -> None:
        user = self.get(name)
        if user is None:
            raise ValueError("Unbekannter Benutzer.")
        if user.is_admin and role != ROLE_ADMIN and self.admin_count() <= 1:
            raise ValueError("Der letzte Administrator kann nicht herabgestuft werden.")
        user.role = role
        self.save()

    def delete_user(self, name: str) -> None:
        user = self.get(name)
        if user is None:
            raise ValueError("Unbekannter Benutzer.")
        if user.is_admin and self.admin_count() <= 1:
            raise ValueError("Der letzte Administrator kann nicht gelöscht werden.")
        del self._users[name.lower()]
        self.save()
