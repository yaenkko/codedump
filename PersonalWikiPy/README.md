# Personal Wiki (Python)

Ein **lokales, persönliches Wiki** für Windows 11 mit grafischer Oberfläche
(Python + Tkinter). Es läuft als `.exe` und speichert alle Inhalte als ganz
normale **Markdown-Dateien in Ordnern**.

Neu in dieser Version:

- 🔐 **Anmeldung** mit gehashten Passwörtern (PBKDF2)
- 👑 **Vorhandener Admin-Nutzer** – beim ersten Start automatisch angelegt
- ➕ Admin kann **weitere Nutzer anlegen / löschen / verwalten**
- 📚 **Jeder Nutzer hat eine eigene Library**
- 🤝 Nutzer können ihre Library **untereinander freigeben** (Lesen oder Schreiben)

## Standard-Zugang

Beim ersten Start wird automatisch ein Administrator angelegt:

| Benutzername | Passwort |
|--------------|----------|
| `admin`      | `admin`  |

> **Bitte nach dem ersten Login ändern** über *Konto → Passwort ändern*.

## Bedienung

- **Konto** – Passwort ändern, Abmelden, Beenden
- **Bearbeiten** – Neue Kategorie/Seite, Importieren, Speichern (`Strg+S`),
  Umbenennen, Löschen
- **Ansicht** – Markdown-Vorschau ein-/ausschalten
- **Freigabe** – *Meine Bibliothek freigeben…* (Lese- oder Schreibrecht je Nutzer)
- **Admin** (nur für Administratoren) – *Benutzerverwaltung…*: Nutzer anlegen,
  Passwort zurücksetzen, Rolle umschalten, löschen
- **Bibliothek** (oben links) – zwischen eigener und freigegebenen Bibliotheken
  wechseln

Bei nur **Leserecht** sind Editor und Bearbeiten-Schaltflächen automatisch
gesperrt.

## So werden die Daten gespeichert

```
Dokumente\PersonalWiki\          <- Datenordner
├── users.json                   <- Nutzerkonten (Passwörter nur als Hash!)
└── libraries\
    ├── admin\                   <- eigene Bibliothek je Nutzer
    │   ├── .share.json          <- Freigaben dieser Bibliothek
    │   └── Notizen\             <- Kategorie = Ordner
    │       └── Idee.md          <- Seite = Markdown-Datei
    └── alice\
        └── Startseite.md
```

Jede Seite ist eine menschenlesbare `.md`-Datei. Für die **Migration** kopierst
du einfach den gesamten Ordner `Dokumente\PersonalWiki` – alles bleibt sortiert
und inklusive Nutzer/Freigaben erhalten.

> Der Datenordner lässt sich über die Umgebungsvariable `PERSONAL_WIKI_DATA`
> umlenken (z. B. für eine portable Installation neben der EXE).

## Voraussetzungen

- **Python 3.10+** (Windows-Installer von python.org enthält Tkinter bereits)
- Es werden **keine** externen Pakete benötigt – nur die Standardbibliothek.

## Starten (während der Entwicklung)

```powershell
python run.py
```

oder

```powershell
python -m personal_wiki
```

## Eine `.exe` erzeugen (Windows)

1. Einmalig PyInstaller installieren:
   ```powershell
   pip install pyinstaller
   ```
2. Bauen – entweder per Doppelklick auf **`build_exe.bat`** oder von Hand:
   ```powershell
   pyinstaller --onefile --windowed --name PersonalWiki run.py
   ```
3. Die fertige Datei liegt unter **`dist\PersonalWiki.exe`** und startet per
   Doppelklick (kein installiertes Python auf dem Zielrechner nötig).

## Projektaufbau

| Datei | Zweck |
|-------|-------|
| `run.py`                          | Startpunkt (auch PyInstaller-Eingang) |
| `personal_wiki/app.py`            | Anmelde-/Abmelde-Schleife |
| `personal_wiki/config.py`         | Pfade / Datenordner |
| `personal_wiki/auth.py`           | Nutzer, Passwörter (Hash), Rollen |
| `personal_wiki/library.py`        | Bibliotheken (Dateien) + Freigaben |
| `personal_wiki/markdown_render.py`| Markdown-Vorschau im Text-Widget |
| `personal_wiki/ui_login.py`       | Anmeldefenster |
| `personal_wiki/ui_main.py`        | Hauptfenster |
| `personal_wiki/ui_dialogs.py`     | Benutzerverwaltung, Freigaben, Eingaben |

## Sicherheitshinweis

Die Anmeldung schützt vor versehentlichem Zugriff zwischen den App-Konten und
speichert Passwörter nur als Hash. Es handelt sich um ein lokales Einzelplatz-
Werkzeug – wer direkten Dateizugriff auf den Datenordner hat, kann die
Markdown-Dateien natürlich auch ohne Anmeldung lesen.
