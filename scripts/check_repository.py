#!/usr/bin/env python3
"""Prüft Quellpfade und wenige eindeutige Secret-Muster, ohne Netzwerk.

Ergänzende Barriere, kein vollständiger Datenschutz- oder Secret-Scan.
Es werden auch unversionierte Dateien betrachtet. Inhalte werden nie ausgegeben.
"""

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
TOP_LEVEL = {"README.md", "AGENTS.md", "SECURITY.md", "CHANGELOG.md", ".gitignore"}
PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{50,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
)


def allowed_path(relative):
    if relative.as_posix() in TOP_LEVEL:
        return True
    parts = relative.parts
    if len(parts) != 2:
        return False
    folder, name = parts
    if folder in {"docs", "prompts"}:
        return name.endswith(".md")
    if folder == "scripts":
        return name.endswith(".py")
    if folder == "tests":
        return name.startswith("test_") and name.endswith(".py")
    return relative.as_posix() in {"templates/report.md", "templates/report.tex", "reports/README.md"}


def inspect_tree(root):
    issues = []

    def visit(folder):
        for path in sorted(folder.iterdir()):
            relative = path.relative_to(root)
            if path.is_symlink():
                issues.append((str(relative), "Symlink im Quellbaum"))
            elif path.is_dir():
                if relative.parts[0] == ".git" or path.name == "__pycache__":
                    continue
                visit(path)
            elif not allowed_path(relative):
                issues.append((str(relative), "Pfad nicht für Quellmaterial freigegeben"))
            elif path.stat().st_size > 512 * 1024:
                issues.append((str(relative), "Für Quelltext unerwartet große Datei"))
            else:
                try:
                    content = path.read_text(encoding="utf-8")
                except (UnicodeError, OSError):
                    issues.append((str(relative), "Nicht als UTF-8-Quelltext lesbar"))
                    continue
                if any(pattern.search(content) for pattern in PATTERNS):
                    issues.append((str(relative), "Mögliches Geheimnis; Inhalt nicht ausgegeben"))

    visit(root)
    return issues


def main():
    try:
        issues = inspect_tree(ROOT)
    except OSError:
        print("Projektprüfung fehlgeschlagen: unzugänglicher Pfad.", file=sys.stderr)
        return 2
    for path, reason in issues:
        print(path + ": " + reason)
    if issues:
        return 1
    print("Projektprüfung bestanden (Quellpfade und ausgewählte Secret-Muster).")
    print("Keine vollständige Datenschutzgarantie; vor Commit manuell prüfen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
