#!/usr/bin/env python3
"""Lokales macOS-Inventar. Liest Systemzustand; schreibt nur neue Berichte.

Python >= 3.9, nur Standardbibliothek. Kein sudo, Netzwerk, Upload, Scan oder
Installationsschritt. Plists sind nicht vertrauenswürdige Daten, niemals Code.
"""

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import plistlib
import re
import stat
import subprocess
import sys
import tempfile

VERSION = "0.1.0"
SCHEMA_VERSION = 1
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MAX_PLIST_BYTES = 1024 * 1024
MAX_ITEMS = 2000
MAX_TEXT = 500
COMMAND_TIMEOUT = 15
COMMAND_OUTPUT_LIMIT = 16000

# Nur diese fest definierten Statusabfragen dürfen ausgeführt werden.
# Verfügbarkeit und Ausgabe können je nach macOS-Version variieren.
CHECK_COMMANDS = {
    "macos_version": ("/usr/bin/sw_vers",),
    "sip_status": ("/usr/bin/csrutil", "status"),
    "gatekeeper_status": ("/usr/sbin/spctl", "--status"),
    "filevault_status": ("/usr/bin/fdesetup", "status"),
    "firewall_status": (
        "/usr/libexec/ApplicationFirewall/socketfilterfw", "--getglobalstate"
    ),
}

# Bewusste Grenzen der ersten Ausbaustufe, auch bei technisch erfolgreichem Lauf.
NOT_ASSESSED = [
    "Schadsoftware, aktive Prozesse und Netzwerkverbindungen",
    "Vollständigkeit und Aktualität der XProtect-Erkennung",
    "Verfügbarkeit neuer Betriebssystem- und App-Updates",
    "Codesignaturen und Unbedenklichkeit von Programmen",
    "Moderne Anmelde-/Hintergrundobjekte außerhalb der genannten Plist-Ordner",
    "Browsererweiterungen, TCC-Berechtigungen, MDM/Profile und Kontositzungen",
    "Cronjobs, Shell-Startdateien und weitere Persistenzmechanismen",
    "Andere Benutzerkonten, Apps außerhalb der genannten Ordner, Symlink-Ziele",
    "Ubuntu, iPhone, externe Datenträger und Backup-Inhalte",
]


def text_value(value, home=None):
    """Begrenzte Metadaten; Pfade kürzen ist keine vollständige Anonymisierung."""
    if not isinstance(value, str):
        return None
    if home is not None:
        value = value.replace(str(home), "<HOME>")
    value = re.sub(r"/Users/[^/\s]+", "/Users/<USER>", value)
    value = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", value)
    return value[:MAX_TEXT]


def display_path(path, home):
    return text_value(str(path), home)


def read_plist(path):
    """Keine Symlinks, FIFOs oder unbegrenzten Dateien verfolgen/lesen."""
    path = Path(path)
    try:
        if any(p.is_symlink() for p in (path, *path.parents)):
            return None, "symlink_not_followed"
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | os.O_NONBLOCK
        fd = os.open(str(path), flags)
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode):
                return None, "not_regular_file"
            if info.st_size > MAX_PLIST_BYTES:
                return None, "size_limit"
            data = stream.read(MAX_PLIST_BYTES + 1)
        if len(data) > MAX_PLIST_BYTES:
            return None, "size_limit"
        parsed = plistlib.loads(data)
        if not isinstance(parsed, dict):
            return None, "not_dictionary"
        return parsed, None
    except FileNotFoundError:
        return None, "not_found"
    except PermissionError:
        return None, "permission_denied"
    except (OSError, ValueError, TypeError, plistlib.InvalidFileException,
            OverflowError, RecursionError) as exc:
        # Keine Exception-Texte mit privaten Pfaden/Inhalten übernehmen.
        return None, "read_error:" + type(exc).__name__
    except Exception as exc:
        # Parserfehler variieren (z.B. XML-Parser). Nicht als Erfolg verstecken.
        return None, "parse_error:" + type(exc).__name__


def run_status_check(check_id):
    """Nie vom Benutzer oder aus Plists gelieferte Befehle ausführen."""
    argv = CHECK_COMMANDS[check_id]
    result = {"id": check_id, "command": list(argv), "status": "error"}
    try:
        completed = subprocess.run(
            argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, shell=False, timeout=COMMAND_TIMEOUT,
            cwd="/", env={"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LC_ALL": "C"},
            check=False,
        )
    except FileNotFoundError:
        result["reason"] = "command_not_available"
        return result
    except subprocess.TimeoutExpired:
        result["reason"] = "timeout"
        return result
    except OSError as exc:
        result["reason"] = type(exc).__name__
        return result
    result["returncode"] = completed.returncode
    result["status"] = "collected" if completed.returncode == 0 else "error"
    for name in ("stdout", "stderr"):
        raw = getattr(completed, name)
        result[name] = text_value(raw[:COMMAND_OUTPUT_LIMIT].decode("utf-8", "replace"))
        if len(raw) > MAX_TEXT:
            result["output_truncated"] = True
            if result["status"] == "collected":
                result["status"] = "partial"
    if completed.returncode:
        result["reason"] = "nonzero_exit_requires_review"
    return result


def collect_directory(root, kind, home, max_depth=2):
    """Begrenzte Ordnerinventur, ohne Links zu verfolgen oder Apps zu starten."""
    root = Path(root)
    result = {"root": display_path(root, home), "kind": kind,
              "status": "collected", "items": [], "gaps": [],
              "max_depth": max_depth, "max_items": MAX_ITEMS}
    visited = 0

    def gap(path, reason):
        result["gaps"].append({"path": display_path(path, home), "reason": reason})
        result["status"] = "partial"

    def walk(folder, depth):
        nonlocal visited
        try:
            if any(p.is_symlink() for p in (folder, *folder.parents)):
                gap(folder, "symlink_not_followed")
                return
            with os.scandir(folder) as entries:
                for entry in entries:
                    visited += 1
                    if visited > MAX_ITEMS:
                        gap(folder, "item_limit")
                        return
                    path = Path(entry.path)
                    if entry.is_symlink():
                        gap(path, "symlink_not_followed")
                        continue
                    try:
                        if kind == "launch_plists":
                            if not entry.name.endswith(".plist"):
                                continue
                            plist, problem = read_plist(path)
                            if problem:
                                gap(path, problem)
                                continue
                            args = plist.get("ProgramArguments")
                            program = plist.get("Program")
                            if not isinstance(program, str) and isinstance(args, list) and args:
                                program = args[0]
                            result["items"].append({
                                "path": display_path(path, home),
                                "label": text_value(plist.get("Label"), home),
                                "program": text_value(program, home),
                                "argument_count": len(args) if isinstance(args, list) else None,
                                "run_at_load": plist.get("RunAtLoad") if isinstance(plist.get("RunAtLoad"), bool) else None,
                                "keep_alive_configured": "KeepAlive" in plist,
                                # Keine Argumente, Umgebungswerte oder vollständigen Plists.
                            })
                        elif entry.is_dir(follow_symlinks=False):
                            if entry.name.lower().endswith(".app"):
                                plist, problem = read_plist(path / "Contents" / "Info.plist")
                                row = {"path": display_path(path, home),
                                       "name": text_value(entry.name, home),
                                       "metadata_status": problem or "collected"}
                                if plist is not None:
                                    for src, dst in (("CFBundleIdentifier", "bundle_id"),
                                                     ("CFBundleShortVersionString", "version"),
                                                     ("CFBundleVersion", "build")):
                                        row[dst] = text_value(plist.get(src), home)
                                else:
                                    gap(path, problem)
                                result["items"].append(row)
                            elif depth < max_depth:
                                walk(path, depth + 1)
                            else:
                                gap(path, "depth_limit")
                    except OSError as exc:
                        gap(path, "entry_error:" + type(exc).__name__)
        except FileNotFoundError:
            if folder == root:
                result["status"] = "not_present"
            else:
                gap(folder, "disappeared_during_read")
        except OSError as exc:
            gap(folder, "directory_error:" + type(exc).__name__)

    walk(root, 0)
    result["items"].sort(key=lambda item: item["path"])
    return result


def collect_inventory(device_id, home):
    commands = [run_status_check(name) for name in CHECK_COMMANDS]
    directories = [collect_directory(p, "applications", home) for p in
                   (Path("/Applications"), Path("/System/Applications"), home / "Applications")]
    directories += [collect_directory(p, "launch_plists", home, max_depth=0) for p in
                    (Path("/Library/LaunchAgents"), Path("/Library/LaunchDaemons"),
                     home / "Library/LaunchAgents")]
    partial = any(c["status"] != "collected" for c in commands)
    partial |= any(d["status"] == "partial" for d in directories)
    return {
        "schema_version": SCHEMA_VERSION, "tool_version": VERSION,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "device_id": device_id, "platform": "Darwin", "architecture": platform.machine(),
        "collection_status": "partial" if partial else "collected_with_declared_limits",
        "security_verdict": "not_assessed", "commands": commands,
        "directories": directories, "not_assessed": NOT_ASSESSED,
        "privacy": "Vertrauliche lokale Metadaten; nicht für automatischen Upload freigegeben.",
    }


def md_safe(value):
    # Metadaten dürfen keine Markdown/HTML-Anweisungen einschleusen.
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(
        ">", "&gt;").replace("|", "\\|").replace("`", "&#96;").replace("\n", " ")


def render_summary(report):
    lines = ["# Lokales Mac-Inventar", "", "**Kein Malware-Scan. Sicherheitsurteil: nicht bewertet.**", "",
             "- Gerät: " + md_safe(report["device_id"]),
             "- UTC: " + report["created_at_utc"],
             "- Erfassungsstatus: " + report["collection_status"],
             "- Skriptversion: " + VERSION,
             "- SHA-256 des ausgeführten Skripts: " + report["script_sha256"], "",
             "## Statusabfragen", "", "| Abfrage | Erfassung | Ausgabe (keine Bewertung) |",
             "| --- | --- | --- |"]
    for check in report["commands"]:
        output = check.get("stdout") or check.get("stderr") or check.get("reason", "")
        lines.append("| " + " | ".join(md_safe(v) for v in (check["id"], check["status"], output)) + " |")
    lines += ["", "## Verzeichnisse", "", "| Bereich | Erfassung | Einträge | Lücken |",
              "| --- | --- | --- | --- |"]
    for section in report["directories"]:
        lines.append("| " + " | ".join(md_safe(v) for v in (section["root"], section["status"],
                     len(section["items"]), len(section["gaps"]))) + " |")
    lines += ["", "Details und Fehlergründe stehen in inventory.json. Die Dateien sind vertraulich.",
              "", "## Nicht geprüft", ""] + ["- " + x for x in report["not_assessed"]]
    lines += ["", "Nächster Schritt: docs/macos-pilot.md abarbeiten; Befunde fachlich bewerten.", ""]
    return "\n".join(lines)


def validate_output_root(root):
    root = Path(root).expanduser().resolve()
    for ancestor in (root, *root.parents):
        if (ancestor / ".git").exists() or ancestor == PROJECT_ROOT:
            raise ValueError("Ausgabe innerhalb eines Git-Repositorys ist gesperrt.")
    return root


def write_reports(report, output_root):
    root = validate_output_root(output_root)
    previous_umask = os.umask(0o077)
    try:
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        run_dir = Path(tempfile.mkdtemp(prefix="inventory-", dir=root))
        for name, content in (("inventory.json", json.dumps(report, ensure_ascii=False, indent=2) + "\n"),
                              ("summary.md", render_summary(report))):
            # Nur neue Dateien in neuem privaten Ordner; nie Ergebnisse überschreiben.
            fd = os.open(run_dir / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(content)
        return run_dir
    finally:
        os.umask(previous_umask)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device-id", default="mac-m1", help="Neutrale Kennung, keine Seriennummer")
    parser.add_argument("--output-root", type=Path,
                        default=Path.home() / "Library/Application Support/PersonalSecurityAudit/runs")
    parser.add_argument("--version", action="version", version=VERSION)
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,39}", args.device_id):
        parser.error("Gerätekennung: 1–40 Kleinbuchstaben, Zahlen, Bindestrich oder Unterstrich.")
    if platform.system() != "Darwin":
        print("Nicht ausgeführt: Dieses Inventarskript benötigt einen realen Mac (macOS).", file=sys.stderr)
        return 2
    if os.geteuid() == 0:
        print("Nicht ausgeführt: Als normaler Benutzer starten, ohne sudo/root.", file=sys.stderr)
        return 2
    try:
        root = validate_output_root(args.output_root)
        report = collect_inventory(args.device_id, Path.home())
        run_dir = write_reports(report, root)
    except (OSError, ValueError) as exc:
        print("Lauf nicht abgeschlossen: " + type(exc).__name__ + ". Ausgabe und Rechte prüfen.", file=sys.stderr)
        return 2
    print("Inventar lokal gespeichert: " + str(run_dir))
    print("Sicherheitsurteil: NICHT BEWERTET. Kein Malware-Scan; Details und Lücken im Bericht.")
    return 1 if report["collection_status"] == "partial" else 0


if __name__ == "__main__":
    raise SystemExit(main())
