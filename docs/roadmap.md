# Ausbau und Rhythmus

| Stufe | Inhalt | Freigabekriterium |
| --- | --- | --- |
| 0.1 | Regeln, drei Prompts, Berichtsvorlagen, Mac-Inventar, Tests | Projektprüfungen bestanden; echter Mac-Pilot noch offen |
| 0.2 | Mac-Pilot und bewertete Vergleichsbasis; strukturierter Vergleich | Fehler/Lücken bewertet, Datenschutz kontrolliert |
| 0.3 | Ubuntu-Inventar und Dienste-/SSH-Metadatenprüfung | Eigener Ubuntu-Probelauf mit künstlichen Tests |
| 0.4 | Externe Datenträger mit Werkzeug- und Scanabdeckungsbericht | Keine automatische Löschung; verschlüsselte/übersprungene Bereiche sichtbar |
| 0.5 | Lokale wiederkehrende Erfassung und Monatsübersicht | Zeitplan, Energiebedarf, Zugriffsrechte und Datenhaltung festgelegt |
| separat | iPhone-Checkliste und gegebenenfalls fachkundige MVT-Analyse | Eigener Untersuchungsauftrag und geschütztes Backup |

Vorschlag, **noch nicht eingerichtet**: wöchentliche kurze Änderungskontrolle,
monatliche Befundbewertung, zusätzliche Prüfung bei neuen Datenträgern oder
konkreten Hinweisen, vierteljährliche Kontrolle von Konten und Wiederherstellung.

Spätere lokale Automatisierung kann unter macOS über launchd und unter Ubuntu
über systemd-Timer erfolgen. Für den Start keine Self-hosted GitHub Runner auf
Alltagsgeräten. GitHub-Automatisierung darf zunächst nur den Projektcode testen.
GitHub-gehostete Runner haben nicht automatisch Zugriff auf persönliche Geräte.

Codeänderungen später über nachvollziehbare Commits/Reviews; fremde Actions auf
konkrete geprüfte Commit-SHAs festlegen, Rechte minimieren. Sicherheitsfunktionen
des privaten Repositorys nur nach Prüfung der tatsächlichen Verfügbarkeit planen.

## Offene Arbeitspakete

- [ ] Echter Mac-Pilot anhand `docs/macos-pilot.md`.
- [ ] Abweichungen und legitime Hintergrunddienste fachlich zuordnen.
- [ ] Ausgabe-Schema nach Pilot stabilisieren und Vergleich implementieren.
- [ ] Export ausschließlich geprüfter Zusammenfassungen entwerfen.
- [ ] Ubuntu und externe Datenträger getrennt implementieren und testen.
- [ ] Rhythmus erst nach Pilot festlegen und technisch aktivieren.
