"""Einfache Markdown-Vorschau für ein Tkinter-Text-Widget.

Tkinter kann kein HTML darstellen, deshalb wird das Markdown hier zeilenweise
geparst und mit Text-Tags formatiert (Überschriften, Listen, Code, Fett/Kursiv).
Bewusst klein gehalten und ohne externe Bibliotheken.
"""

from __future__ import annotations

import re
import tkinter as tk
import tkinter.font as tkfont


def configure_tags(text: tk.Text) -> None:
    """Legt die Stil-Tags für das Vorschau-Widget an."""
    base = tkfont.nametofont("TkTextFont")
    family = base.cget("family")
    size = base.cget("size")
    if size <= 0:
        size = 11

    text.tag_configure("h1", font=(family, size + 8, "bold"), spacing1=10, spacing3=6)
    text.tag_configure("h2", font=(family, size + 5, "bold"), spacing1=8, spacing3=4)
    text.tag_configure("h3", font=(family, size + 2, "bold"), spacing1=6, spacing3=3)
    text.tag_configure("bold", font=(family, size, "bold"))
    text.tag_configure("italic", font=(family, size, "italic"))
    text.tag_configure("code", font=("Consolas", size), background="#f2f2f2")
    text.tag_configure("codeblock", font=("Consolas", size), background="#f6f8fa",
                       lmargin1=20, lmargin2=20, spacing1=2, spacing3=2)
    text.tag_configure("bullet", lmargin1=20, lmargin2=40)
    text.tag_configure("quote", lmargin1=20, lmargin2=20, foreground="#555555")


_INLINE_PATTERNS = [
    (re.compile(r"\*\*([^*]+)\*\*"), "bold"),
    (re.compile(r"\*([^*]+)\*"), "italic"),
    (re.compile(r"`([^`]+)`"), "code"),
]


def _insert_inline(text: tk.Text, line: str, base_tags: tuple[str, ...] = ()) -> None:
    """Fügt eine Zeile ein und wendet einfache Inline-Formatierung an."""
    # Wir suchen das jeweils früheste Vorkommen eines Inline-Musters.
    pos = 0
    while pos < len(line):
        earliest = None
        earliest_tag = None
        for pattern, tag in _INLINE_PATTERNS:
            m = pattern.search(line, pos)
            if m and (earliest is None or m.start() < earliest.start()):
                earliest = m
                earliest_tag = tag
        if earliest is None:
            text.insert("end", line[pos:], base_tags)
            break
        # Text vor dem Treffer normal einfügen.
        if earliest.start() > pos:
            text.insert("end", line[pos:earliest.start()], base_tags)
        text.insert("end", earliest.group(1), base_tags + (earliest_tag,))
        pos = earliest.end()
    text.insert("end", "\n", base_tags)


def render(text: tk.Text, markdown: str) -> None:
    """Schreibt das gerenderte Markdown in das (read-only) Text-Widget."""
    text.configure(state="normal")
    text.delete("1.0", "end")

    in_code = False
    for raw in (markdown or "").replace("\r\n", "\n").split("\n"):
        stripped = raw.strip()

        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            text.insert("end", raw + "\n", ("codeblock",))
            continue

        heading = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if heading:
            level = len(heading.group(1))
            _insert_inline(text, heading.group(2), (f"h{level}",))
            continue

        if stripped.startswith("> "):
            _insert_inline(text, stripped[2:], ("quote",))
            continue

        if stripped.startswith(("- ", "* ")):
            text.insert("end", "•  ", ("bullet",))
            _insert_inline(text, stripped[2:], ("bullet",))
            continue

        ol = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if ol:
            text.insert("end", f"{ol.group(1)}.  ", ("bullet",))
            _insert_inline(text, ol.group(2), ("bullet",))
            continue

        if stripped in ("---", "***", "___"):
            text.insert("end", "─" * 40 + "\n")
            continue

        _insert_inline(text, raw)

    text.configure(state="disabled")
