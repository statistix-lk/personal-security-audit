# Datenhaltung und Veröffentlichung

## Lokal und vertraulich

Inventare, ungefilterte Fehlermeldungen, Plists, Prozess-/Netzwerklisten,
Gerätenamen, Seriennummern, Nutzernamen, persönliche Pfade, Kontodaten und
Smartphone-Backups gehören nicht in das Repository. Patienten- und
Forschungsinhalte dürfen weder erfasst noch hochgeladen werden.

Die Standardausgabe des Inventars liegt außerhalb von Git. Berichtordner haben
0700, Dateien 0600. Das begrenzt den Dateizugriff, ersetzt aber keine
Datenträgerverschlüsselung und keinen Schutz vor anderen Prozessen desselben
Benutzers oder Administratoren. FileVault und sichere Backups gesondert bewerten.

Das Skript erfasst keine Hostnamen, Seriennummern, IP-Adressen oder Kontoschlüssel.
Home-Pfade werden gekürzt. **App-Namen, Bundle-IDs, Labels und Programmpfade
können dennoch sensible Metadaten sein.** Die Ausgabe ist nicht anonymisiert und
nicht automatisch zum Teilen freigegeben.

## Was ins Repository darf

Code, synthetische Testfälle, allgemeine Quellen, Prompts und leere Vorlagen.
Später kontrollierte Zusammenfassungen mit neutraler Gerätekennung, Datum,
Prüfmethoden, Anzahl/Art offener Befunde und nächsten Schritten. Inhalte mit
Personen- oder Institutionsbezug und private Pfade vorher entfernen.

Der Export erfolgt **nicht automatisch**. Neue Berichte werden einzeln geprüft
und gezielt hinzugefügt; dafür muss die bewusste Sperre in `.gitignore` angepasst
werden. Keine Uploads über Issues, Actions-Artefakte, Drittanbieter oder öffentliche
Hash-Dienste. Git speichert frühere Versionen; nachträgliches Löschen aus dem
Arbeitsverzeichnis entfernt keine bereits übertragenen Geheimnisse.

## Zusätzliche Barrieren

- `.gitignore` sperrt häufige Rohdatenformate und den Berichtsordner.
- `scripts/check_repository.py` prüft den Arbeitsbaum gegen erlaubte Quellpfade
  und einige eindeutige Geheimnismuster. Es ist kein vollständiger Secret-Scanner.
- Keine Fernzugänge, gespeicherten Tokens oder Drittanbieter-Abhängigkeiten.
- Vor jedem Commit ausschließlich konkrete geprüfte Quellpfade auswählen.
- Falls ein echtes Geheimnis veröffentlicht wurde: weitere Veröffentlichung
  stoppen, Geheimnis über den zuständigen Dienst widerrufen/rotieren und den
  Git-Verlauf separat behandeln. Nicht nur die sichtbare Datei löschen.

## Aufbewahrung

Zunächst keine automatische Löschfrist oder Bereinigung. Nach dem Pilotlauf einen
passenden Aufbewahrungszeitraum festlegen. Bei Verdacht auf einen Vorfall relevante
Berichte erhalten und forensische Anforderungen klären.
