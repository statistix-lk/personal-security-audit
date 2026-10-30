# Validierung der Version 0.1.0

Datum: 30.10.2026. Umgebung: isolierte Linux-Arbeitsumgebung mit Python 3.12.
**Kein Zugriff auf den persönlichen Mac, kein Gerätebefund.**

## Automatisierte Tests

`python3 -B -m unittest discover -s tests -v`: **28 Tests bestanden**.

Abgedeckt werden unter anderem:

- Beschädigte, binäre, übergroße und nicht als Dictionary vorliegende Plists.
- Verweigerte Zugriffe, fehlende Verzeichnisse und explizite Prüflücken.
- Symlinks (auch in Elternpfaden), FIFO-Dateien, Ordner-/Eintragslimits.
- Keine Ausführung von Befehlen aus ProgramArguments oder Plist-Inhalten.
- Keine Übernahme von Argumentinhalten oder Umgebungswerten in Berichte.
- Feste Befehlsliste, deaktivierte Shell, Zeitlimit und Rückgabecodebehandlung.
- Fehlende Befehle, abgebrochene Abfragen und gekürzte Ausgaben als Fehler/Lücke.
- Schutz vor Ausgabe innerhalb von Git-Repositorys einschließlich Symlink-Zielen.
- Neue Ausgabeordner, beschränkte Dateirechte und kein Überschreiben alter Berichte.
- Abbruch vor Erfassung bei Linux oder root-Aufruf.
- Abweisung unerwünschter Rohdatenpfade und ausgewählter Geheimnismuster.

Der Projektcheck `python3 -B scripts/check_repository.py` ergänzt die Tests.
Er ist kein vollständiger Secret-Scanner und ersetzt nicht die manuelle Kontrolle
der zum Commit ausgewählten Dateien.

## Noch nicht validiert

- Tatsächliche Ausgaben/Verfügbarkeit der fünf Statusbefehle auf dem persönlichen Mac.
- Verhalten bei dessen konkreter macOS-Version und vorhandenen Programmen.
- Manuelle Ergänzungen, Interpretation der Befunde und erste Vergleichsbasis.
- Python-Versionen außer der hier verwendeten 3.12; Codeziel ist Python ab 3.9.
- Sicherheitszustand des Macs oder anderer Geräte.

Die Abnahmekriterien für den echten Pilotlauf stehen in `docs/macos-pilot.md`.
Weitere Geräte und Zeitpläne werden erst nach diesem Schritt umgesetzt.
