# Personal Wiki

Ein **lokales, persönliches Wiki** für Windows 11 mit grafischer Oberfläche.
Es läuft als eigenständige `.exe` und speichert alle Inhalte als ganz normale
**Markdown-Dateien in Ordnern** auf deiner Festplatte – nichts liegt in einer
Cloud, einer Datenbank oder der Registry.

> Du speist deine Daten selbst als Dateien ein. Dadurch ist beim Umzug auf einen
> anderen PC bereits alles sauber sortiert abgelegt – einfach den Ordner kopieren.

## Funktionen

- **Baumansicht** links: Kategorien (Ordner) und Seiten (Markdown-Dateien)
- **Editor** rechts mit umschaltbarer **HTML-Vorschau** des Markdowns
- **Neue Kategorien & Seiten** anlegen, **umbenennen**, **löschen**
- **Importieren** bestehender `.md`/`.txt`-Dateien direkt in eine Kategorie
- **Suche** über alle Seitentitel
- **Automatisches Speichern** beim Seitenwechsel und Schließen, zusätzlich `Strg+S`
- **Datenordner frei wählbar** (Standard: `Dokumente\PersonalWiki`)

## So werden die Daten gespeichert

```
Dokumente\PersonalWiki\          <- Datenordner (frei wählbar)
├── Arbeit\                      <- Kategorie  = Ordner
│   ├── Projekt A.md             <- Seite      = Markdown-Datei
│   └── Notizen.md
├── Privat\
│   ├── Rezepte\                 <- Unterkategorien sind möglich
│   │   └── Pizza.md
│   └── Ideen.md
└── Startseite.md
```

Jede Seite ist eine einfache, menschenlesbare `.md`-Datei. Für die **Migration**
kopierst du einfach den gesamten Datenordner – alles bleibt sortiert erhalten.

## Voraussetzungen

- **Windows 11** (oder Windows 10)
- Zum Bauen: **Visual Studio 2022** mit der Workload
  *".NET-Desktopentwicklung"* – oder das **.NET 8 SDK**

## Starten / Bauen in Visual Studio

1. `PersonalWiki/PersonalWiki.sln` in Visual Studio öffnen
2. **F5** drücken (Debug) bzw. Konfiguration auf *Release* stellen und **Strg+F5**
3. Die fertige `PersonalWiki.exe` liegt danach unter
   `PersonalWiki\bin\Release\net8.0-windows\`

## Eine einzelne, portable EXE erzeugen

Über die Kommandozeile (im Ordner `PersonalWiki`) lässt sich eine
**eigenständige** EXE erzeugen, die ohne installiertes .NET läuft:

```powershell
dotnet publish PersonalWiki/PersonalWiki.csproj -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true
```

Ergebnis:
`PersonalWiki\bin\Release\net8.0-windows\win-x64\publish\PersonalWiki.exe`

Diese eine Datei kannst du z. B. auf den Desktop oder einen USB-Stick legen und
direkt per Doppelklick starten.

> Tipp: Benötigt das Zielsystem ohnehin .NET 8, kannst du `--self-contained false`
> verwenden – die EXE wird dann deutlich kleiner.

## Projektaufbau

| Datei | Zweck |
|-------|-------|
| `Program.cs`          | Einstiegspunkt der Anwendung |
| `MainForm.cs`         | Hauptfenster: Baum, Editor, Vorschau, alle Aktionen |
| `WikiStore.cs`        | Datei-Operationen (Anlegen, Lesen, Umbenennen, Löschen) |
| `MarkdownRenderer.cs` | Kleiner Markdown→HTML-Konverter für die Vorschau |
| `AppConfig.cs`        | Merkt sich den gewählten Datenordner |
| `Dialogs.cs`          | Einfacher Eingabedialog |
