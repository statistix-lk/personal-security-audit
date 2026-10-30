# Personal Security Audit

> **Kritischer Review vom 30.10.2026:** Der Originalcode 0.1.0 ist zur
> Aufbewahrung importiert. Drei nachgewiesene Fehler sind noch offen, darunter
> umgehbare Pfadprüfungen bei gleichzeitig veränderten Ordnern.
> Vor einem echten Geräte-Pilotlauf beheben und erneut prüfen.
> Befunde, Reproduktionen und Grenzen: [Import-Review](docs/review-2026-10-30.md).

Privates Arbeitsprojekt für nachvollziehbare Sicherheitsprüfungen von Mac,
Ubuntu, iPhone und externen Datenträgern. Es verbindet lokale Prüfprogramme,
Arbeitsaufträge für Codex und einheitliche Berichte.

**Version 0.1.0: erster Ausbauschritt.** Implementiert ist ein begrenztes,
lokales Mac-Inventar. Ein echter Mac-Probelauf steht noch aus. Dieses Repository
bestätigt weder die Sicherheit eines Geräts noch eine Infektion.

## Was bereits enthalten ist

| Bereich | Inhalt |
| --- | --- |
| [AGENTS.md](AGENTS.md) | Arbeitsregeln, Datenschutz und Grenzen für Codex |
| [docs/macos-pilot.md](docs/macos-pilot.md) | Sicherer erster Probelauf und manuelle Ergänzungen |
| [docs/privacy.md](docs/privacy.md) | Lokale Datenhaltung und kontrollierte Veröffentlichung |
| [docs/roadmap.md](docs/roadmap.md) | Ausbau und vorgeschlagener Prüfrhythmus |
| [docs/sources.md](docs/sources.md) | Primärquellen und Dokumentation |
| [prompts/01-first-audit.md](prompts/01-first-audit.md) | Erstprüfung und Inventar |
| [prompts/02-follow-up.md](prompts/02-follow-up.md) | Folgeprüfung und Veränderungen |
| [prompts/03-triage.md](prompts/03-triage.md) | Befund bewerten und weitere Schritte planen |
| [scripts/macos_inventory.py](scripts/macos_inventory.py) | macOS-Inventar ohne Änderungen an Systemeinstellungen |
| [templates/report.md](templates/report.md) | Vollständige Berichtsvorlage |
| [templates/report.tex](templates/report.tex) | Bearbeitbare LaTeX-Vorlage für Overleaf |
| [tests/](tests/) | Künstliche Testfälle für Sicherheit und Fehlerbehandlung |

## Erster Start auf dem eigenen Mac

1. [Pilot-Anleitung](docs/macos-pilot.md) lesen. Bei konkretem Infektionsverdacht
   zuerst [Vorfallsablauf](docs/incident-response.md) berücksichtigen.
2. Vorhandenes Python **ab 3.9** verwenden; das Projekt installiert nichts.
   Fehlt Python, zunächst nur die manuelle Checkliste bearbeiten.
3. Im heruntergeladenen Repository ausführen:

```sh
python3 -B scripts/macos_inventory.py --device-id mac-m1
```

Das Skript liest festgelegte Statusabfragen, App-Metadaten sowie drei
LaunchAgent-/LaunchDaemon-Ordner. Es startet keine gefundenen Apps/Skripte,
nutzt kein `sudo` und enthält keinen Netzwerk- oder Uploadschritt.
**Einzige beabsichtigte Schreibvorgänge:** neue lokale Berichtsdateien in
`~/Library/Application Support/PersonalSecurityAudit/runs/`.
Wie bei jedem Lesezugriff kann macOS eigene Protokolle/Dateimetadaten aktualisieren;
dies ist keine forensische Untersuchung mit Schreibblocker.

Pro Lauf entstehen ein neuer privater Ordner (0700), `inventory.json` und
`summary.md` (0600). Die Dateien enthalten vertrauliche Metadaten und bleiben
außerhalb von Git. Vorhandene Ergebnisse werden nicht überschrieben.

| Exitcode | Bedeutung |
| --- | --- |
| `0` | Geplante Inventarerfassung abgeschlossen, mit dokumentierten Grenzen |
| `1` | Inventar geschrieben, aber mindestens eine technische Prüflücke vorhanden |
| `2` | Lauf nicht abgeschlossen bzw. Plattform, Rechte oder Eingabe ungeeignet |

**Keiner dieser Codes bedeutet „schadsoftwarefrei“.** Die Bewertung ist immer
`not_assessed`. Unter Linux wird der Produktivlauf vor jeder Erfassung abgebrochen.

## Grenzen der Version 0.1.0

Keine Malware-Erkennung, kein vollständiges Persistenzinventar, keine Prüfung von
Codesignaturen, Browserdaten, Konten, MDM/TCC, XProtect-Aktualität oder verfügbaren
Updates. Apps werden nur bis zur dokumentierten Ordnertiefe betrachtet. Symlinks
werden ausgelassen und als Lücke gemeldet. iPhone, Ubuntu und externe Datenträger
werden noch nicht automatisiert untersucht.

Moderne Anmelde- und Hintergrundobjekte müssen zusätzlich in den
Systemeinstellungen kontrolliert werden. Ein vorhandener Autostart ist häufig
legitim. Ein Inventar darf nicht ungeprüft zur „guten“ Vergleichsbasis werden.

## Projektprüfung

```sh
python3 -B -m unittest discover -s tests -v
python3 -B scripts/check_repository.py
```

Die Tests verwenden künstliche Dateien und simulierte Betriebssystemantworten.
Sie benötigen keinen Mac, keine Administratorrechte und keine echte Schadsoftware.
Das ersetzt den noch ausstehenden Mac-Pilotlauf nicht.

## GitHub und Automatisierung

GitHub speichert Code, Prompts, Vorlagen und kontrollierte Zusammenfassungen.
Rohdaten werden nicht automatisch übertragen. Das Verzeichnis `reports/` enthält
zunächst nur eine Anleitung. Ein privates Repository ist kein Tresor für sensible
Gerätedaten. `.gitignore` und der Projektcheck ergänzen die manuelle Prüfung;
sie garantieren keine vollständige Erkennung von Geheimnissen.

Es sind **keine geplanten Läufe, Self-hosted Runner, Fernzugänge, Scan-Dienste
oder GitHub-Actions-Workflows aktiviert**. Ein lokaler Zeitplan folgt erst nach
einem überprüften Probelauf und einem konkreten Einrichtungsauftrag.

## Arbeitsstand

- Projektgerüst und Mac-Inventar vorhanden.
- Automatisierte Tests: siehe [Validierung](docs/validation.md).
- Echter Mac-Pilot: **offen**.
- Nächster Schritt: erste lokale Erfassung und manuelle Ergänzungen dokumentieren.
- Ubuntu, Datenträger und wiederkehrende Läufe: spätere Ausbaustufen.
