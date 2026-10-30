# Erster Mac-Probelauf

## Vor dem Start

- Prüfe, dass du am tatsächlichen Mac arbeitest, nicht in einer Cloud-Umgebung.
- Bei konkreter Infektion: [Vorfallsablauf](incident-response.md), keine einzige
  Sicherungskopie anschließen und keine Bereinigung beginnen.
- Repo-Code und AGENTS.md lesen. Vorhandene Python-Version ab 3.9 kontrollieren.
- Als normaler Benutzer arbeiten; kein `sudo`, kein Festplattenvollzugriff für
  diese erste Stufe und keine Abschaltung von Schutzmechanismen erforderlich.
- Genügend Speicher für zwei kleine Metadatenberichte vorhalten. Standardausgabe
  liegt in der lokalen Benutzerbibliothek; nicht in einem synchronisierten Ordner.

```sh
python3 --version
python3 -B -m unittest discover -s tests -v
python3 -B scripts/macos_inventory.py --device-id mac-m1
```

`python3 --version` führt das bereits vorhandene Python aus. Keine Installation
bestätigen, falls macOS stattdessen einen Installationsdialog anbietet.

## Exakter automatisierter Umfang

Fest definierte, lesende Abfragen (je 15 Sekunden Zeitlimit):

| Programm | Argumente | Zweck |
| --- | --- | --- |
| `/usr/bin/sw_vers` | keine | macOS-Produktversion/Build |
| `/usr/bin/csrutil` | `status` | angezeigter SIP-Zustand |
| `/usr/sbin/spctl` | `--status` | angezeigter Gatekeeper-Zustand |
| `/usr/bin/fdesetup` | `status` | angezeigter FileVault-Zustand |
| `/usr/libexec/ApplicationFirewall/socketfilterfw` | `--getglobalstate` | angezeigter Firewall-Zustand |

Ein Rückgabecode ungleich null ist ein Erfassungsproblem, kein Sicherheitsurteil.
Das Skript interpretiert unbekannte Ausgaben nicht als „aktiv“ oder „sicher“.

App-Bundles in `/Applications`, `/System/Applications` und `~/Applications`:
Name, gekürzter Pfad, Bundle-ID, Version, Build. Maximal zwei Unterordnerebenen,
keine Symlink-Ziele, maximal 2000 betrachtete Einträge pro Wurzel.

Plists direkt in `/Library/LaunchAgents`, `/Library/LaunchDaemons` und
`~/Library/LaunchAgents`: Label, Programmpfad bzw. erstes ProgramArguments-Element,
Argumentanzahl, RunAtLoad, Vorhandensein einer KeepAlive-Konfiguration. Keine
Argumentinhalte oder Umgebungswerte. Plists maximal 1 MiB, nur reguläre Dateien.

Das Skript **führt keine Plist-Einträge aus**, verändert keine Dienste und liest
keine vollständigen Benutzer-, Browser- oder Schlüsselbunddaten aus.

## Manuelle Ergänzungen

- [ ] Softwareupdate: installierter Stand und angebotene Sicherheitsupdates.
- [ ] Allgemein > Anmeldeobjekte & Erweiterungen: sichtbare Einträge zuordnen.
- [ ] Datenschutz & Sicherheit: Bedienungshilfen, Eingabeüberwachung,
      Bildschirmaufnahme und Festplattenvollzugriff prüfen.
- [ ] Geräteverwaltung/Profile und bekannte Arbeitgeberkonfiguration zuordnen.
- [ ] VPN/Proxy und Fernzugriff prüfen; legitim eingerichtete Zugriffe dokumentieren.
- [ ] Browsererweiterungen und wichtige Kontositzungen durchsehen.
- [ ] Vorhandene Schutzsoftware und Hinweise von XProtect prüfen, ohne aus einer
      einzelnen Versionsnummer eine Aktualitätsgarantie abzuleiten.

## Abnahmekriterien

- [ ] `inventory.json` und `summary.md` liegen nur im neuen lokalen Ordner.
- [ ] Gerätekennung, UTC-Zeit, Skriptversion und Skripthash stimmen.
- [ ] Ausgaben passen zur realen macOS-Version und wurden verstanden.
- [ ] Alle `partial`, `error`, fehlenden Ordner und Auslassungen wurden bewertet.
- [ ] Ein zweiter Lauf überschreibt den ersten nicht.
- [ ] Manuelle Prüfbereiche und nicht geprüfte Bereiche sind dokumentiert.
- [ ] Keine sensiblen Daten im Git-Staging-Bereich oder Git-Verlauf.
- [ ] Zusammenfassung anhand `templates/report.md` erstellt und geprüft.

Erst danach entscheiden, welche lokalen Prüfungen sich regelmäßig wiederholen
lassen. Eine neue Vergleichsbasis wird begründet bestätigt; Unterschiede allein
beweisen keine Infektion. Kein automatisches Einstufen bekannter Pfade als sicher.
