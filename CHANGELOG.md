# Changelog

## 0.4.32 – Neues Design - VirusTotal-Check und Upload nach Zustimmung
- Hauptoberfläche im Graphit-/Violett-Stil überarbeitet: kompaktere Navigation, klarere Kopfzeile und stärker hervorgehobene Profilwahl.
- Profil-Auswahl dauerhaft oben rechts integriert: Eigenes Profil, Standard (Empfohlen), Hoher Schutz und Maximaler Schutz.
- Scanprofile werden gespeichert. „Profil verwalten …“ führt direkt zu den ClamAV-Scanoptionen.
- Bestehende Sicherheitsmodule, Scanfenster, Quarantäne- und Tray-Funktionen bleiben erhalten.
- Wenn ein SHA-256-Hash bei VirusTotal unbekannt ist, fragt LunaSecurity jetzt ausdrücklich, ob die Datei zur Analyse hochgeladen werden soll.
- Der Upload erfolgt nur nach ausdrücklicher Zustimmung; bei Ablehnung bleibt die Datei lokal.
- Nach dem Upload wird der Analysefortschritt abgefragt und anschließend der Datei-Bericht mit Erkennungszahlen sowie den meldenden Anbietern angezeigt.
- Direkter Upload derzeit bis 32 MB. Vertrauliche oder personenbezogene Dateien nicht hochladen: VirusTotal kann übermittelte Dateien und Indikatoren in seinen Datensatz aufnehmen.
- Bei erkannten Dateien wird jetzt neben dem Dateipfad auch die genaue ClamAV-Signatur bzw. Erkennungsart angezeigt – sowohl im Live-Scanfenster als auch im Haupt-Scanprotokoll.
- Globale Einstellung unter „Einstellungen → ClamAV – Scanoptionen“ ergänzt: ClamAV-Meldungen `Heuristics.Limits.Exceeded.MaxFileSize` können ein- oder ausgeschaltet als Bedrohung gezählt werden.
- Standardmäßig aktiv: Größenlimit-Überschreitungen werden als „nicht vollständig geprüft“ separat gezählt und nicht in die Bedrohungs-/Sicherheitsereignisliste übernommen. Andere ClamAV-Erkennungen bleiben unverändert aktiv.
- Bei deaktivierter Option werden diese Meldungen wieder wie normale Bedrohungsfunde gezählt und protokolliert. Die Einstellung gilt global für alle Scanprofile.
- YARA-Regelupdate: temporäres Download-/Entpackverzeichnis liegt jetzt auf demselben Dateisystem wie `/etc/lunasecurity/yara-rules`; Wiederherstellung eines Sicherungsstands nach abgebrochenem Update ergänzt.
- Echtzeitschutz-Karte korrigiert: Überschrift und Symbol sind nun an die tatsächliche Statusabfrage gebunden; bewährte systemctl-is-active-Abfrage aus 0.4.31 wiederverwendet.
- Echtzeitschutz-Anzeige nach Aktivieren/Deaktivieren anhand von systemd `ActiveState` verifiziert; Statuspunkt, Beschriftung und Schaltfläche werden gemeinsam aktualisiert.
- Netzwerkseite um eine zweite Schaltflächenreihe für temporäre Port-Sperren, dauerhaftes Speichern und das Aufheben eigener LunaSecurity-Sperren ergänzt.
- Eigenes Profil verwendet ausschließlich die individuell gespeicherten ClamAV-Optionen (PUP, Heuristik, versteckte Dateien, Dateigröße und Unterordner).
- Versteckte Dateien und Verzeichnisse werden auch bei privilegierten Systemscans ausgeschlossen, wenn die Option deaktiviert ist.
- Explizit ausgewählte versteckte Einzeldateien werden bei deaktivierter Option ebenfalls übersprungen.
- Scan-Auswahl vereinfacht: Die separaten Schaltflächen „Datei / Ordner scannen“ und „Home-Verzeichnis“ in der oberen Modusleiste entfernt.
- Die beiden verbleibenden Aktionen heißen jetzt „Home-Verzeichnis“ und „Vollständiger Systemscan“.
- Beide Scanaktionen verwenden immer das oben ausgewählte Profil (Eigenes Profil, Standard, Hoher Schutz oder Maximaler Schutz); kein Scanmodus überschreibt die Profiloptionen.
- Der zentrale Button „Scan starten“ für die gezielte Datei-/Ordnerauswahl bleibt erhalten.

## Version 0.4.31
- Manuelle ClamAV-Scans unterdrücken zeitgleich ausgelöste ClamOnAcc-Zugriffsmeldungen einschließlich kurzer Nachlaufzeit; nur der manuelle Scanbericht meldet den Fund. Das Echtzeit-Fenster bleibt echten, unabhängigen On-Access-Funden vorbehalten.
- Neues gemeinsames Fundfenster: Jeder neu protokollierte ClamOnAcc-Echtzeitfund öffnet automatisch den Prüfbericht „Echtzeitschutz – Bedrohung erkannt“; Wiederherstellungsprüfungen verwenden dieselbe Bezeichnung.
- Quarantäne-Wiederherstellung schreibt die Datei am ursprünglichen Ort neu statt sie nur zu verschieben; anschließend wird sie zusätzlich direkt mit clamdscan geprüft und ein erneuter Fund als Sicherheitsereignis gemeldet.
- Versionsnummer für den geprüften Echtzeitschutz-Fix auf 0.4.31 angehoben.
- Enthält die Korrekturen aus 0.4.30: erneute Meldung neu auftauchender Echtzeitfunde, zurückgesetzte Fundpfad-Merkliste bei neuen Scans und zuverlässiges Warnbanner.

## Version 0.4.30
- Echtzeitschutz: Neue ClamOnAcc-Funde werden nicht mehr durch die Merkliste bereits bereinigter Pfade unterdrückt; erneut auftauchende Dateien lösen wieder Warnung und Ereignis aus.
- Erledigte Fundpfade werden zu Beginn eines neuen Scans zurückgesetzt, damit erneut auftauchende Testdateien wieder Warnbanner und Sicherheitsereignis auslösen.
- Warnbanner für gespeicherte Sicherheitsfunde wird beim Laden und nach neuen Funden zuverlässig anhand des Ereignisprotokolls eingeblendet.
- Hinweisbanner verweist jetzt auf den tatsächlich so benannten Tab „Virenschutz“; die Meldung ist sprachabhängig übersetzt.
- Echtzeitschutz-Schaltfläche, Statusanzeige und Statuspunkt wieder in die bestehende Aktionszeile integriert; keine zusätzliche Zeile.
- Beschriftung „Vollständiger Systemscan“ zu „Systemscan“ verkürzt, damit die Aktionszeile besser passt.

- Echtzeitschutz-Anzeige beim Sprachwechsel stabilisiert: Status und Schaltfläche werden aus dem bestätigten Dienstzustand neu aufgebaut, nicht aus übersetzten Beschriftungen abgeleitet.
- Echtzeitschutz erhält eine eigene Bedienzeile; Statusmeldung und Statuspunkt werden nicht mehr von den Scan-/Update-Schaltflächen zusammengedrückt.
- Während einer Statusabfrage oder Aktivierung/Deaktivierung bleibt die Schaltfläche gesperrt und zeigt den passenden Prüf- bzw. Hintergrundstatus.
- Scan-Dialog: Schaltfläche „Schließen“ wird auch bei nachträglichem Einblenden korrekt übersetzt.
- Echtzeitschutz: Status, Aktivieren/Deaktivieren, Hintergrundstatus und Tooltips folgen der gewählten Sprache.
- Virenschutz-Hauptseite: Signaturstatus und Meldung bei leerer Ereignisliste werden ebenfalls übersetzt.

- Virenschutz als ersten Hauptnavigationspunkt benannt und die englischen Texte der Scan-Zielauswahl sowie der leeren Ereignisliste vervollständigt.
- Verwaiste, indeterminierte Fortschrittsanzeige im Hauptfenster deaktiviert; der Fortschritt bleibt ausschließlich im jeweiligen Prüfungsdialog sichtbar.
- Englische Oberfläche vervollständigt: dynamische ClamAV-Scanfenster, Scan-Zielauswahl, Fortschrittsdialoge und fail2ban-Statusmeldungen werden ebenfalls übersetzt.
- Fehler beim Start mit QGroupBox in der Sprachumschaltung behoben (Gruppentitel werden korrekt über title()/setTitle() verarbeitet).
- Sprachwahl Deutsch/Englisch mit dauerhaft gespeicherter Einstellung ergänzt.
- Helles Luna-Design zusätzlich zum dunklen Graphit-Design ergänzt; Wechsel ohne Neustart.
- Virensignatur-Aktualisierung läuft im Hintergrund; die Oberfläche bleibt bedienbar.
- Kein blockierender Ergebnisdialog nach der Aktualisierung; vollständige Ausgabe und Status bleiben im LunaSecurity-Protokoll.
- Die vorhandene Option für automatische Aktualisierung vor Scans bleibt unverändert.


## Version 0.4.29
- Signalübergabe im gemeinsamen Prüfungsfenster korrigiert: Der Worker sendet Titel und Ergebnis; das Fenster übernimmt jetzt ausdrücklich das zweite Signalargument.
- Vollständige Prüfberichte bleiben nach Abschluss im gemeinsamen Fenster sichtbar.


## Version 0.4.28
- Doppelte Ergebnisfenster für Hintergrundprüfungen entfernt.
- Das gemeinsame Prüfungsfenster zeigt den vollständigen Abschlussbericht; Lynis, Rootkit, fail2ban und Netzwerkprüfung öffnen kein zweites Ergebnisfenster.
- Versionsnummer in der Anwendung, im DEB-Build, README und CHANGELOG synchronisiert.


## Version 0.4.27
- Separate alte Ergebnis- und Informationsfenster nach Sicherheitsprüfungen entfernt.
- Das neue Prüfungsfenster zeigt nach Abschluss direkt das vollständige Ergebnis und bleibt das einzige Ergebnisfenster.
- Rootkit-, fail2ban-, Lynis- und Netzwerkprüfungen öffnen keine zusätzlichen Ergebnisdialoge mehr.


## Version 0.4.26
- Eigenes Prüfungsfenster für alle Nicht-ClamAV-Hintergrundprüfungen ergänzt.
- Laufende Kommandoausgaben werden fortlaufend im Fenster angezeigt.
- Abbrechen, Ergebnis kopieren und Schließen nach Abschluss ergänzt.
- ClamAV zeigt Prozentfortschritt auf Basis exakt derselben vorbereiteten Dateiliste, die anschließend gescannt wird.
- Nicht-ClamAV-Prüfungen zeigen laufende Kommandoausgaben; solange das jeweilige Prüfprogramm keine verlässlichen Einzeldatei-Zähler liefert, bleibt ihr Balken bewusst im Aktivitätsmodus.
- Das bestehende ClamAV-Fenster bleibt erhalten; seine Fortschrittsanzeige wurde um den echten Dateiumfang ergänzt.

# Änderungsprotokoll

## 0.4.25
- Fehlenden Import des Python-Moduls `re` ergänzt. Dadurch kann die Scanabschluss-Auswertung ohne NameError ausgeführt werden.

# Änderungsprotokoll

## 0.4.24
- Scanumfang-Zeile wird aus dem Scanfenster ins Hauptprotokoll übernommen.
- Falls die Zeile oder das Scanfenster fehlt, erscheint eine eindeutige Fehlermeldung im Hauptprotokoll.

# Änderungsprotokoll – LunaSecurity

## Version 0.4.10
- Im Scanfenster die Meldung beim angeforderten Abbruch direkt auf „Scan wurde erfolgreich abgebrochen.“ geändert. Keine Änderung an Scan- oder Abbruchlogik.

## Version 0.3.99
- ClamAV-Ausgabe wird blockweise an die Oberfläche übergeben, damit sehr ausführliche Scans die GUI nicht durch tausende Einzelsignale ausbremsen.
- Live-Protokoll wird effizient blockweise eingefügt und auf die letzten 5.000 Zeilen begrenzt; die vollständige Ausgabe bleibt für die Ergebnis- und Fundauswertung erhalten.
- „Nicht lesbar“ zählt fehlgeschlagene Lesezugriffe wie `fmap_readpage: pread fail/error` pro betroffener Datei nur einmal.
- „Übersprungen“ zählt ausschließlich explizite Skip-/Exclude-Meldungen und wird nicht aus Lesefehlern abgeleitet.
- Geprüfte Dateien werden je Pfad dedupliziert, damit `Scanning`- und `: OK`-Zeilen nicht doppelt zählen.


## Version 0.3.97

- Der Schließen-Button ist während des laufenden Scans wieder sichtbar, bleibt aber grau und deaktiviert.
- Die bewährte Abschlusslogik aus 0.3.96 bleibt erhalten: Sobald „Abgeschlossen“ oder „Abgebrochen“ gesetzt wird, wird derselbe Button aktiviert und blau.

## Version 0.3.96

- Das Einblenden des Schließen-Buttons ist direkt an dieselbe Code-Stelle gekoppelt, die den Status „Abgeschlossen“ bzw. „Abgebrochen“ setzt.
- Der Button wird unmittelbar beim Setzen des Endstatus eingeblendet, bevor Protokoll- und Berichtsnachbearbeitung läuft.

## Version 0.3.95

- Der blaue Schließen-Button wird nach regulärem Scanabschluss zusätzlich verzögert über den Qt-Ereigniszyklus eingeblendet und sein Sichtbarkeitszustand erneut gesetzt.
- Nach Scanabbruch bleibt die sofortige Einblendung erhalten.

## Version 0.3.94

- Nach Klick auf „Scan abbrechen“ wird der blaue, aktivierte „Schließen“-Button unmittelbar eingeblendet, während der bestehende Abbruchaufruf den ClamAV-Prozess beendet.
- Nach regulärem Scanende wird derselbe Button ebenfalls eingeblendet.
- Die Funktion des Abbruchbuttons bleibt erhalten.

## Version 0.3.82

- Einheitliches Live-Fenster für Datei-, Ordner-, Home- und vollständige Systemscans mit aktuellem ClamAV-Ausgabeprotokoll, Statuszählern und Laufzeitanzeige.
- Vollständiger Systemscan startet jetzt ausdrücklich das Wurzelverzeichnis `/` über `pkexec`; LunaSecurity selbst läuft weiterhin ohne Root-Rechte.
- ClamAV-Ausgabe wird während des Scans fortlaufend an die Oberfläche übergeben.

## Version 0.3.81

- PDF-Export korrigiert: QTextOption wird mit der PySide6-kompatiblen Standardkonstruktion erstellt und der Zeilenumbruch anschließend gesetzt.
- Behebt den gemeldeten TypeError beim Speichern des PDF-Berichts.

# LunaSecurity – Änderungsprotokoll

## Version 0.3.80

- Korrigierter PySide6-Import: `QMarginsF` wird aus `QtCore` geladen, damit LunaSecurity auch mit der Debian-/PySide6-Installation startet.
- PDF-Export aus 0.3.79 bleibt erhalten.

# LunaSecurity – Änderungsprotokoll

## Version 0.3.79

- PDF-Export robuster gemacht: A4-Seitenlayout wird explizit gesetzt.
- Fehlgeschlagene PDF-Erstellung wird mit einer verständlichen Fehlermeldung angezeigt.
- PDF-Datei und Dateigröße werden nach dem Export kontrolliert.

## Version 0.3.78

- PDF-Berichte verwenden ein festes A4-Seitenlayout mit passenden Seitenrändern und gut lesbarer 9-Punkt-Schrift.
- Lange Protokollzeilen werden innerhalb der bedruckbaren Seitenbreite umgebrochen und bei Bedarf auf mehrere Seiten verteilt.

## Version 0.3.77

- HTML- und PDF-Sicherheitsberichte exportieren jetzt den vollständigen sichtbaren Inhalt des großen Protokollfensters.
- Der Bericht enthält damit die angezeigten Scanmeldungen und Ergebnisse statt des separaten Dashboard-Textes.
- HTML und PDF verwenden dieselbe Berichtsvorlage.

## Version 0.3.76

- Beschriftung der Schaltfläche zur Signaturaktualisierung vereinheitlicht: „Virensignatur aktualisieren“.

## Version 0.3.75

- Beim Verschieben oder Löschen eines Fundes werden alle zu derselben Datei gehörenden doppelten Ereigniseinträge entfernt; Funde anderer Dateien bleiben erhalten.
- Verspätet eintreffende Echtzeitschutz-Protokollzeilen können den gerade erledigten Fund in derselben Sitzung nicht erneut in die Liste aufnehmen.
- Die Fundliste wird nach erfolgreicher Dateiaktion aktualisiert; bei Fehlern bleibt der Eintrag sichtbar.

## Version 0.3.74

- Nach erfolgreichem Verschieben eines ausgewählten Fundes in Quarantäne wird nur dessen Ereigniseintrag aus der Fundliste entfernt.
- Nach erfolgreichem Löschen einer ausgewählten Datei wird nur deren Ereigniseintrag entfernt.
- Andere Funde bleiben erhalten; bei fehlgeschlagener Dateiaktion bleibt der Eintrag sichtbar.

## Version 0.3.73
- Überflüssige Wörter in den Beschreibungen der Kacheln „Systemschutz“ und „Netzwerk“ entfernt.
- Versionsanzeige auf 0.3.73 aktualisiert.

## Version 0.3.72
- Der vorhandene globale Button „Scan abbrechen“ funktioniert jetzt auch für alle drei Prüfungen unter Systemschutz: Rootkit, AIDE und System-Audit.
- Rootkit-Prüfung bricht laufende rkhunter-/chkrootkit-Prozesse mit Administratorrechten ab.
- System-Audit führt die Teilprüfungen einzeln aus und stoppt zwischen den Befehlen sofort bei Abbruch.
- Abbruchstatus und Schaltflächenzustand werden nach Abschluss zurückgesetzt.

## Version 0.3.71
- Lynis-Prüfung und fail2ban-Statusabfrage können über „Prüfung abbrechen“ beendet werden.
- Gemeinsamer abbrechbarer Prozess-Runner mit Prozessgruppen-Signal und Zeitlimit.
- Abbruchschaltfläche wird nach Abschluss wieder zurückgesetzt.
- Versionsanzeige auf 0.3.71 aktualisiert.

# LunaSecurity – Änderungsprotokoll

## Version 0.3.70
- fail2ban-Statusprüfung läuft über einen einzelnen pkexec-Aufruf mit Administratorrechten.
- Verbindungsstatus, Gesamtstatus und SSH-Jail werden rein lesend abgefragt; keine Regeln oder Dienste werden verändert.
- Fehler, Abbruch und Zeitüberschreitung der Abfrage werden verständlich angezeigt.
- Versionsanzeige der Anwendung auf 0.3.70 aktualisiert.

# LunaSecurity – Änderungsprotokoll

## Version 0.3.69
- Grundschrift der gesamten Anwendungsoberfläche von 11 pt auf 12 pt erhöht.
- Fenstergröße und Seitenleistenbreite bleiben unverändert.
- Versionsanzeige in der Anwendung auf 0.3.69 aktualisiert.

# LunaSecurity – Änderungsprotokoll

## Version 0.3.68
- Grundschrift der gesamten Anwendungsoberfläche von 10 pt auf 11 pt erhöht (eine Stufe größer).
- Schaltflächen, Navigation, Statusanzeigen und übrige Texte übernehmen die größere Grundschrift; Fenstergröße und Layoutbreite bleiben unverändert.
- Versionsanzeige in der Anwendung auf 0.3.68 aktualisiert.

# LunaSecurity – Änderungsprotokoll

## Version 0.3.67
- Sichtbares `\\n\n## Version 0.4.12\n- Ordner innerhalb des persönlichen Home-Verzeichnisses werden ohne Root-Rechte gescannt.\n- Bei jedem ausgewählten Ordner außerhalb des Home-Verzeichnisses fragt LunaSecurity vor dem Scan, ob Root-Rechte über pkexec verwendet werden sollen.\n- Die Regel gilt unabhängig von den aktuell gesetzten Zugriffsbits; Scan- und Abbruchlogik bleiben unverändert.\n\n` im LunaSecurity-Seitenleistenkopf durch echten Zeilenumbruch ersetzt.
- Linke Seitenleiste um rund 4 cm auf 356 Qt-Pixel verbreitert; Gesamtfenstergröße bleibt unverändert.
- Deutlich sichtbare Statusleuchte ergänzt: grün bei aktivem Echtzeitschutz, rot bei ausgeschaltetem Schutz, gelb bei unbekanntem Status.
- Versionsanzeige in der Anwendung auf 0.3.67 aktualisiert.

# LunaSecurity – Änderungsprotokoll

## Version 0.3.66
- Systemscan-Abbruch verwendet jetzt direkt `pkexec pkill -TERM -x clamscan`, entsprechend dem manuell bestätigten funktionierenden Terminalbefehl.
- Der Scan-Worker erkennt das Ende nach einem Abbruch als „vom Benutzer abgebrochen“ statt als normalen Scanabschluss.
- Versionsanzeige der Anwendung auf 0.3.66 aktualisiert.

# LunaSecurity – Änderungsprotokoll\n\n## Version 0.3.65\n- Versionsanzeige in der Anwendung auf 0.3.65 korrigiert (Paketversion und GUI-Version waren zuvor unterschiedlich).\n- Systemscan-Abbruch korrigiert: pkexec wird nicht mehr fälschlich als eigentlicher Scanner-Prozess behandelt. Ein Root-Abbruchhelfer beendet die vom Systemscan gestartete ClamAV-Prozessgruppe zuverlässig.\n- Abbruchstatus wird an den Scan-Worker weitergereicht; die GUI wartet nicht mehr blockierend auf den Scanner.\n\n# LunaSecurity – Änderungsprotokoll

## Version 0.3.64
- Abbruchlogik für alle ClamAV-Aufgaben verbessert: laufende Prozessgruppen werden beendet und eingesammelt.
- Dateisuche während der Vorbereitung reagiert jetzt ebenfalls auf Abbruch.
- Systemscan nutzt einen Root-Helfer mit Signalbehandlung, der den eigentlichen ClamAV-Prozess zuverlässig beendet.
- Signaturaktualisierung und normale Datei-/Ordnerscans verwenden denselben abbrechbaren Prozessmanager.

# LunaSecurity – Änderungsprotokoll

## Version 0.3.63
- Signaturaktualisierung öffnet ein eigenes Ergebnisfenster statt des Datei-/Ordnerscan-Dialogs.
- Systembereiche werden mit pkexec und Administratorrechten direkt durch ClamAV geprüft; geschützte Dateien werden dadurch nicht mehr wegen fehlender Benutzerrechte ausgelassen.

# LunaSecurity – Änderungsprotokoll

## Version 0.3.62
- Anordnung der Virenschutz-Aktionszeile angepasst: „Systembereiche scannen“, „Virensignaturen jetzt aktualisieren“ und „Echtzeitschutz aktivieren/deaktivieren“ stehen links nebeneinander.
- Die Statusanzeige des Echtzeitschutzes steht jetzt rechts außen in derselben Zeile.

## Version 0.3.61
- Neuer Button „Systembereiche scannen“ direkt links neben „Virensignaturen jetzt aktualisieren“.
- Systemscan prüft wichtige Linux-Verzeichnisse (`/etc`, `/usr/bin`, `/usr/sbin`, `/usr/lib`, `/boot`, `/opt`, `/var/lib`, `/var/log`); virtuelle Dateisysteme und symbolische Verzeichnislinks werden nicht verfolgt.
- Scanprofile nach Prüftiefe umgesetzt: „Eigenes Profil“ verwendet unverändert die gespeicherten ClamAV-Einstellungen, „Schnellscan“ reduziert PUP-/Heuristikprüfung, versteckte Dateien, große Dateien und Rekursion, „Komplettscan“ aktiviert diese Optionen samt 2-GB-Grenzen.
- Profil „Home-Scan“ aus der Profilauswahl entfernt; die separate Home-Verzeichnis-Schaltfläche bleibt erhalten.

# Änderungsprotokoll

## 0.3.58
- Hauptfenster neu strukturiert: feste Navigation links statt der bisherigen mittleren Tableiste.
- Navigationspunkte schalten direkt die vorhandenen Funktionsseiten um; bestehende Seiten und Aktionen bleiben erhalten.
- Linke Seitenleiste im Graphit-/Violett-Blau-Design mit eigens gezeichneter, skalierbarer Mond- und Berglandschaft am unteren Rand.
- Ergebnisdialoge und deren bisherige Darstellung bleiben unverändert.

# LunaSecurity – Änderungsprotokoll

## Version 0.3.58
- Reparaturhilfe aus dem Rootkit-Ergebnisfenster wird synchron geöffnet: Hauptfenster sichtbar machen, Reparatur-Tab auswählen und aktivieren, erst danach Ergebnisfenster schließen.
- Tab „Sicherheitsereignisse“ steht jetzt ganz links an erster Position.

## Version 0.3.54
- YARA-Regelverwaltung ergänzt: Aktualisierungsschaltfläche lädt den öffentlichen Regelsatz von Neo23x0/signature-base.
- Installation erfolgt mit gezielter pkexec-Administratorabfrage nach `/etc/lunasecurity/yara-rules`; vorhandene Regeln werden bei erfolgreichem Download atomar ersetzt.
- Anzeige der installierten YARA-Regeldateien und verständlicher Hinweis, wenn noch keine Regeln vorhanden sind.
- YARA-Scan meldet Regelsatzgröße und Scan-Ziel; bestehende separate Ergebnisfenster bleiben erhalten.

## Version 0.3.52
- AIDE-Abbruchhelfer wird im Hintergrund zuverlässig mit `wait()` eingesammelt.
- Verhindert einen zurückbleibenden Zombie-Prozess `aide-cancel-helper`, ohne die Oberfläche während der PolicyKit-Abfrage zu blockieren.

## Version 0.3.51
- AIDE-Abbruch korrigiert: Der Debian-/bin/sh-`kill`-Aufruf verwendete eine nicht unterstützte `--`-Option, wodurch das Signal nie an die negative Prozessgruppen-ID gesendet wurde.
- TERM/KILL und die Gruppenprüfung verwenden jetzt die von dash unterstützte Syntax; damit wird die gesamte AIDE-Session einschließlich `31_aide_apt` adressiert.
- Vorhandener Abbrechen-Button und separate Root-Helfer bleiben erhalten.

## Version 0.3.50
- AIDE-Prozessgruppen-Fix: Die Prozessgruppen-ID wird jetzt innerhalb der neuen Session geschrieben und entspricht dadurch zuverlässig der tatsächlichen PGID.
- Der Abbrechen-Helfer wartet kontrolliert auf das Ende der gesamten Gruppe und beendet bei Bedarf verbliebene Kindprozesse.
- Der vorhandene Abbrechen-Button bleibt unverändert; keine zusätzliche Schaltfläche.

## Version 0.3.49
- AIDE-Abbruch korrigiert: dedizierte Root-Prozessgruppe mit PID-Datei unter /run.
- Der vorhandene Abbrechen-Button beendet den gesamten AIDE-Prozessbaum einschließlich Debian-Hilfsskripten wie 31_aide_apt.
- Kein zusätzlicher Button; LunaSecurity selbst läuft weiterhin ohne Root-Rechte.

# Änderungsprotokoll LunaSecurity

## 0.3.48
- AIDE-Abbruch beendet jetzt zusätzlich den root-eigenen `aide`-Prozess über eine gezielte PolicyKit-Aktion (`pkexec pkill -TERM -x aide`).
- Der vorhandene Abbrechen-Button bleibt die einzige Abbruchbedienung; die Oberfläche erhält danach das reguläre Worker-Ergebnis.

## 0.3.47
- Der vorhandene Abbrechen-Button neben dem Fortschrittsbalken wird während der AIDE-Prüfung aktiviert.
- Beendet den pkexec/AIDE-Prozessbaum kontrolliert; abgebrochene Läufe werden als unvollständig gekennzeichnet.

# Änderungsprotokoll

## Version 0.3.46
- AIDE-Systemintegritätsprüfung über einen dedizierten Root-Helfer gestartet: Beim Klick auf die AIDE-Prüfung fordert `pkexec` die Administratorfreigabe an.
- Nur der AIDE-Prüfprozess erhält Root-Rechte; die LunaSecurity-Oberfläche wird weiterhin normal als Benutzer ausgeführt.
- Fehler bei abgebrochener PolicyKit-Abfrage, fehlender AIDE-Konfiguration und fehlender Referenzdatenbank werden verständlicher ausgegeben.


## Version 0.3.45
- Programmversion, Debian-Paketversion und README auf 0.3.45 vereinheitlicht.
- README-Installations- und Build-Anweisungen auf die tatsächlichen Paket- und Archivnamen aktualisiert.
- AIDE-Voraussetzungen präzisiert: `sudo aideinit` ist eine einmalige, bewusst manuelle Initialisierung nach Prüfung des Systemzustands; ohne aktivierte Referenzdatenbank ist kein aussagekräftiger Integritätsvergleich möglich.
- Abhängigkeiten für Lynis, fail2ban und Qt PrintSupport sowie die bewusst manuelle fail2ban-Aktivierung verständlich dokumentiert.

## Version 0.3.44
- AIDE-Prüfung unter Debian auf `aide.wrapper --check` umgestellt, damit die Debian-Konfiguration automatisch verwendet wird.
- Fallback auf eine vorhandene AIDE-Konfigurationsdatei ergänzt, falls kein Debian-Wrapper vorhanden ist.
- Fehlende AIDE-Konfiguration bzw. Referenzdatenbank wird verständlicher erklärt; eine fehlende Datenbank wird nicht als Integritätsfund dargestellt.
- README um den korrekten Debian-AIDE-Ablauf ergänzt.

## 0.3.43
- DEB-Abhängigkeiten ergänzt: `lynis` und `fail2ban` werden bei der Paketinstallation durch APT mitinstalliert.
- README auf Version 0.3.43 aktualisiert und Installationsanweisungen, Funktionsumfang sowie Voraussetzungen der neuen Sicherheitsfunktionen berichtigt.
- Dokumentiert, dass LunaSecurity fail2ban überwacht, aber dessen Jails und Sperrregeln nicht automatisch konfiguriert oder verändert.
- Qt PrintSupport als Voraussetzung für den PDF-Export ausdrücklich dokumentiert; das entsprechende Python-Paket ist bereits als DEB-Abhängigkeit enthalten.

## 0.3.42
- Sicherheitsstatus-Dashboard ergänzt: Status von ClamAV, LunaSecurity-Echtzeitschutz und fail2ban kann zentral aktualisiert werden. Ein aktiver Dienst wird ausdrücklich nicht als Malware-Freiheitsnachweis dargestellt.
- Optionale Lynis-Systemprüfung ergänzt; das Werkzeug wird nur gestartet, wenn Lynis installiert ist. Die Prüfung nimmt keine automatischen Härtungsänderungen vor.
- Scanprofile ergänzt: Schnellscan, Home-Scan und Komplettscan sowie weiterhin frei konfigurierbare Einstellungen.
- Sicherheitsberichte können als HTML und PDF exportiert werden. Sie enthalten den zuletzt angezeigten Diagnose-/Dashboard-Text und die jüngsten Sicherheitsereignisse.
- fail2ban-Überwachung ergänzt: Dienst-Ping, Gesamtstatus und – sofern eingerichtet – Status des SSH-Jails werden lesend abgefragt.
- Paketprüfungs-Abbruch verbessert: dpkg-Ausgabe wird zeitlich begrenzt abgefragt, damit ein Abbruch während des laufenden Prozesses erkannt und die gestartete Prozessgruppe beendet werden kann. Es wird weiterhin kein dpkg-query-Aufruf pro Datei gestartet.
- Version und Debian-Paketmetadaten auf 0.3.42 angehoben.

## 0.3.40
- Einheitlicher sicherer Abbruch für ClamAV-Datei-/Ordnerscans und die installierte Paketprüfung: gestartete Prozessgruppen erhalten zuerst SIGTERM und werden nur nach einer kurzen Wartefrist nötigenfalls mit SIGKILL beendet.
- Temporäre ClamAV-Dateilisten werden auch bei Abbruch zuverlässig entfernt.
- Abgebrochene Scans werden ausdrücklich als unvollständig protokolliert und nicht als erfolgreicher Scan gewertet; Teilergebnisse werden nicht als abgeschlossene Befunde übernommen.
- Paketprüfung bleibt rein lesend; ein Abbruch verändert keine installierten Dateien.
- Rootkit- und Netzwerkprüfungen, deren Prüfwerkzeuge derzeit als nicht abbrechbare Funktionsaufrufe laufen, werden nicht fälschlich als abbrechbar ausgewiesen.

## 0.3.39
- Paketzuordnung nach `dpkg --verify` beschleunigt: Die installierten Dateilisten unter `/var/lib/dpkg/info/*.list` werden einmalig eingelesen; pro Fund wird kein separater `dpkg-query -S`-Prozess mehr gestartet.
- Paketprüfung bleibt in einem Hintergrund-Thread und zeigt jetzt den aktuellen Arbeitsschritt sowie die verstrichene Laufzeit.
- Neue Schaltfläche zum Abbrechen der laufenden Prüfung; der Worker beendet den gestarteten dpkg-Prozess kontrolliert.
- Die Prüfung bleibt rein lesend; keine Paketdateien werden dabei verändert.

## 0.3.37
- Fehler behoben, bei dem „Installierte Pakete auf Dateiänderungen prüfen“ die Oberfläche blockierte: `dpkg --verify` und Paketzuordnung laufen jetzt in einem QThread im Hintergrund.
- Während der Prüfung zeigt die Oberfläche einen Aktivitätsindikator; der Startknopf wird gegen parallele Prüfungen gesperrt und nach Abschluss wieder freigegeben.
- Zeitüberschreitung und Fehler werden im Reparaturprotokoll angezeigt; die Prüfung bleibt rein lesend.

## 0.3.36
- Reparatur- und Wiederherstellungsbereich neu strukturiert: getrennte Gruppen für Benutzer-Autostart, Debian-Paketprüfung/-reparatur und Wiederherstellung.
- Schaltflächen und Paket-Auswahl erhalten eine einheitliche, responsive Anordnung; Ergebnisse und Protokoll sind in einem eigenen Bereich zusammengefasst.
- Reparatur-Tab in einen Scrollbereich gelegt, damit Bedienelemente auch bei kleineren Fenstergrößen erreichbar bleiben.

# Änderungsprotokoll

## Version 0.3.45
- Programmversion, Debian-Paketversion und README auf 0.3.45 vereinheitlicht.
- README-Installations- und Build-Anweisungen auf die tatsächlichen Paket- und Archivnamen aktualisiert.
- AIDE-Voraussetzungen präzisiert: `sudo aideinit` ist eine einmalige, bewusst manuelle Initialisierung nach Prüfung des Systemzustands; ohne aktivierte Referenzdatenbank ist kein aussagekräftiger Integritätsvergleich möglich.
- Abhängigkeiten für Lynis, fail2ban und Qt PrintSupport sowie die bewusst manuelle fail2ban-Aktivierung verständlich dokumentiert.

## 0.3.35
- Paketprüfung erweitert: Abweichungen aus `dpkg --verify` werden soweit möglich installierten Paketen zugeordnet.
- Für einzeln ausgewählte Pakete wird vor der Reparatur ein APT-Simulationslauf ausgeführt; Reparaturen werden abgebrochen, wenn APT Pakete entfernen würde.
- Paket-Neuinstallation über `apt-get install --reinstall --no-remove`; zuvor abweichende reguläre Dateien werden im Benutzerprofil gesichert und können über eine bestätigte Rollback-Funktion zurückgespielt werden.
- Netzwerkprüfung erweitert um Schnittstellen/IP-Adressen, IPv4-/IPv6-Routen sowie DNS-Konfiguration (`resolvectl` oder `/etc/resolv.conf`).
- Netzwerkprüfung bleibt lesend; keine Firewall-Regeln oder Netzwerkeinstellungen werden automatisch verändert.
- Grenzen der Sicherung und Prüfung werden in der Oberfläche bzw. Dokumentation erläutert.


## 0.3.34
- Neuen Reiter „Reparatur & Wiederherstellung“ ergänzt.
- Benutzer-Autostart-Einträge können nach ausdrücklicher Bestätigung in ein nur für den Benutzer zugängliches Sicherungsverzeichnis verschoben und später wiederhergestellt werden.
- Vorhandene Dateien am Wiederherstellungsziel werden niemals überschrieben; Sicherungen bleiben erhalten, bis sie ausdrücklich wiederhergestellt werden.
- Reparatur- und Rollback-Aktionen werden im Sicherheitsereignisprotokoll dokumentiert.
- Debian-Paketprüfung über `dpkg --verify` als rein lesende Diagnose ergänzt; die Oberfläche weist ausdrücklich auf deren Grenzen hin.
- Keine automatische Bereinigung von Rootkit-Funden und keine Änderungen an Systemdateien.


## 0.3.33
- ClamAV-Scanoptionen im Reiter „Einstellungen“ ergänzt: PUP-Erkennung, heuristische Erkennung, versteckte Dateien, große Dateien bis 2 GB und rekursive Unterordnersuche.
- Vorhandene Option zur automatischen Signaturaktualisierung in den ClamAV-Optionsbereich einsortiert.
- Scanoptionen dauerhaft in QSettings gespeichert und bei Datei-/Ordnerscans an clamscan übergeben.
- Ordnerscans erstellen abhängig von den Optionen eine Dateiliste; versteckte Einträge und Unterordner werden entsprechend berücksichtigt.
- Allgemeine Einstellungen für Tray, Autostart und Audio bleiben erhalten.
\n\n## 0.3.32\n- Reiter „Alarm & Audio“ in einen scrollbaren Bereich eingebettet, damit alle Audio-Einstellungen und Schaltflächen auch bei kleiner Fensterhöhe erreichbar sind.\n

## 0.3.31
- Den Bereich unterhalb der Reiter nochmals um ca. 1 cm nach oben erweitert: mittleres Nachrichtenprotokoll auf 152 logische Pixel festgelegt.
- Hauptfenster, Reiterinhalt und untere Aktionsschaltflächen unverändert gelassen.


## 0.3.30
- Den markierten Bereich unterhalb der Reiter um ca. 1 cm nach oben erweitert, indem ausschließlich das mittlere Nachrichtenprotokoll von mindestens 230 auf fest 190 logische Pixel verkleinert wurde.
- Hauptfenstergröße, Reiterinhalt und untere Aktionsschaltflächen unverändert gelassen.


## 0.3.29
- Inhaltsbereich unterhalb der Reiter auf mindestens 205 Pixel vergrößert.
- Reiterbereich erhält mehr verfügbaren Layout-Platz (Dehnungsfaktor 2), damit Tabellen und Ereignislisten besser nutzbar sind.


## 0.3.28
- Alle aktivierbaren Kontrollkästchen aus der Hauptoberfläche in den neuen Reiter „Einstellungen“ verschoben.
- Optionen für automatische Signaturaktualisierung, Tray-Verhalten, Start im Tray, Desktop-Autostart und akustischen Alarm bleiben mit ihren bisherigen QSettings-Schlüsseln und Funktionen erhalten.
- Mittleres Nachrichten- und Ereignisprotokoll deutlich vergrößert; Mindesthöhe auf 230 Pixel erhöht und flexible Layout-Dehnung aktiviert.


## 0.3.27
- Mittleres Informations- und Ereignisprotokoll vergrößert, damit Meldungen besser lesbar sind.
- Rootkit-Prüfergebnisse werden in einem eigenen großen Berichtfenster statt im kleinen Hauptprotokoll angezeigt.
- Bericht enthält eine vorsichtige Einordnung, konkrete nächste Schritte und die vollständige Ausgabe von rkhunter und chkrootkit.
- Bericht kann in die Zwischenablage kopiert werden; es werden keine Funde automatisch gelöscht oder verändert.


## 0.3.26
- Datei- und Ordnerauswahl verwenden dieselbe Qt-Dialogansicht; nur der Auswahlmodus unterscheidet sich.
- Ordnerdialog zeigt keine englischen Qt-Standardbeschriftungen mehr: Beschriftungen werden über Qt-Dialoglabels und während der gesamten Dialoganzeige direkt an den Widgets auf Deutsch gehalten.
- „Choose“ wird zu „Ordner auswählen“ bzw. „Datei auswählen“, „Cancel“ zu „Abbrechen“.


## 0.3.25
- Englische Beschriftungen der Qt-Datei- und Ordnerdialoge durch direkte Übersetzung der sichtbaren Widgets korrigiert.
- „Look in“, „Directory“, „Files of type“, „Choose“, „Cancel“ und „Directories“ werden deutsch angezeigt.


## 0.3.24
- Dateiauswahl- und Ordnerdialoge auf ausdrücklich deutsche Qt-Dialoge umgestellt.
- Beschriftungen für Suchort, Verzeichnis/Dateiname, Dateityp sowie Auswählen und Abbrechen fest vorgegeben.
- Veraltete native Dateidialog-Aufrufe durch zentral konfigurierte Dialoge ersetzt.


## 0.3.23
- QMessageBox-Standardbuttons erhalten jetzt unabhängig von der Desktop- und Qt-Plattformsprache explizite deutsche Beschriftungen.
- OK-, Ja-, Nein-, Abbrechen- und weitere Standardbuttons werden beim Öffnen sichtbar beschriftet; irreführende reine Symbolbuttons werden entfernt.
- Unbekannte Qt-Übersetzungstexte bleiben unverändert, damit die Übersetzung keine leeren Beschriftungen erzeugt.


## 0.3.22
- Eingebaute Qt-Dialoge der Anwendung erhalten eine zentrale deutsche Übersetzung (u. a. Ja/Nein/Abbrechen sowie Datei- und Ordnerdialoge).
- Native Plattformdialoge werden deaktiviert, damit Datei- und Auswahlfenster die Spracheinstellung von LunaSecurity verwenden.
- Die deutsche Gebietseinstellung wird innerhalb der Anwendung gesetzt; die Systemsprache bleibt unverändert.

## 0.3.21
- Fehler beim Erstellen des Autostart-Eintrags behoben: Die `.desktop`-Datei erhält jetzt echte Zeilenumbrüche und wird vom Desktop korrekt eingelesen.
- Der Autostart verwendet weiterhin den installierten Programmstarter `/usr/bin/lunasecurity` und berücksichtigt die Einstellung für den Start im Tray.

# Änderungsprotokoll

## Version 0.3.45
- Programmversion, Debian-Paketversion und README auf 0.3.45 vereinheitlicht.
- README-Installations- und Build-Anweisungen auf die tatsächlichen Paket- und Archivnamen aktualisiert.
- AIDE-Voraussetzungen präzisiert: `sudo aideinit` ist eine einmalige, bewusst manuelle Initialisierung nach Prüfung des Systemzustands; ohne aktivierte Referenzdatenbank ist kein aussagekräftiger Integritätsvergleich möglich.
- Abhängigkeiten für Lynis, fail2ban und Qt PrintSupport sowie die bewusst manuelle fail2ban-Aktivierung verständlich dokumentiert.

## 0.3.35
- Paketprüfung erweitert: Abweichungen aus `dpkg --verify` werden soweit möglich installierten Paketen zugeordnet.
- Für einzeln ausgewählte Pakete wird vor der Reparatur ein APT-Simulationslauf ausgeführt; Reparaturen werden abgebrochen, wenn APT Pakete entfernen würde.
- Paket-Neuinstallation über `apt-get install --reinstall --no-remove`; zuvor abweichende reguläre Dateien werden im Benutzerprofil gesichert und können über eine bestätigte Rollback-Funktion zurückgespielt werden.
- Netzwerkprüfung erweitert um Schnittstellen/IP-Adressen, IPv4-/IPv6-Routen sowie DNS-Konfiguration (`resolvectl` oder `/etc/resolv.conf`).
- Netzwerkprüfung bleibt lesend; keine Firewall-Regeln oder Netzwerkeinstellungen werden automatisch verändert.
- Grenzen der Sicherung und Prüfung werden in der Oberfläche bzw. Dokumentation erläutert.


## 0.3.19
- Startfehler behoben: Die Versionsdatei `lunasecurity/__init__.py` enthält wieder einen echten Zeilenumbruch statt der wörtlichen Zeichenfolge `\n`.
- Versionsnummer für Fehlerkorrektur auf 0.3.19 erhöht.

## 0.3.18
- Fehlerhafte Escape-Zeichenfolge in der Versionsdatei korrigiert.
- Temporäre Firewall-Testregeln können nach ausdrücklicher Bestätigung dauerhaft gespeichert werden.
- Eigener systemd-Dienst lädt ausschließlich die gespeicherten LunaSecurity-Firewallregeln beim Systemstart.
- Rücknahme deaktiviert diesen Firewall-Regel-Autostart und entfernt ausschließlich die LunaSecurity-eigene Regeltabelle.


## 0.3.15
- Einstellung „Beim Schließen im Infobereich weiterlaufen“ wird beim Ändern sofort dauerhaft gespeichert und beim Schließen zusätzlich synchronisiert.
- Der gespeicherte Zustand bleibt nach einem Neustart erhalten.


## 0.3.14
- Option „Beim Start direkt im Infobereich starten“ ergänzt; Einstellung wird dauerhaft gespeichert.
- Autostart bei der Desktop-Anmeldung über einen benutzerspezifischen Eintrag unter `~/.config/autostart/` aktivierbar und deaktivierbar.
- Autostart-Eintrag berücksichtigt, ob LunaSecurity beim Start sichtbar oder minimiert im System-Tray geöffnet werden soll.
- Verhalten beim Schließen („Im Infobereich weiterlaufen“) wird jetzt ebenfalls dauerhaft gespeichert.


## 0.3.13
- Firewall-Ergebnis als eigenes, deutlich größeres Fenster umgesetzt (900 × 680 Pixel; Mindestgröße 720 × 520).
- Der vollständige Prüfbericht ist sofort sichtbar und muss nicht mehr über „Details anzeigen“ aufgeklappt werden.
- Englische Qt-Standardaktionen „Hide Details…“ und „OK“ durch eine eindeutig deutsche Schaltfläche „Schließen“ ersetzt.

## 0.3.12
- System-Tray-Menüpunkt „LunaSecurity beenden“ beendet jetzt die Qt-Anwendung und den GTK-Tray-Thread vollständig.
- Beim Beenden werden das Qt-Tray-Icon und die Echtzeit-Logüberwachung explizit gestoppt.
- In den Audioeinstellungen kann nach Auswahl einer eigenen WAV-Datei jederzeit wieder der eingebaute LunaSecurity-Alarm aktiviert werden.
- Die aktive Alarmquelle wird in der Oberfläche eindeutig angezeigt.

# Änderungsprotokoll

## Version 0.3.45
- Programmversion, Debian-Paketversion und README auf 0.3.45 vereinheitlicht.
- README-Installations- und Build-Anweisungen auf die tatsächlichen Paket- und Archivnamen aktualisiert.
- AIDE-Voraussetzungen präzisiert: `sudo aideinit` ist eine einmalige, bewusst manuelle Initialisierung nach Prüfung des Systemzustands; ohne aktivierte Referenzdatenbank ist kein aussagekräftiger Integritätsvergleich möglich.
- Abhängigkeiten für Lynis, fail2ban und Qt PrintSupport sowie die bewusst manuelle fail2ban-Aktivierung verständlich dokumentiert.

## 0.3.35
- Paketprüfung erweitert: Abweichungen aus `dpkg --verify` werden soweit möglich installierten Paketen zugeordnet.
- Für einzeln ausgewählte Pakete wird vor der Reparatur ein APT-Simulationslauf ausgeführt; Reparaturen werden abgebrochen, wenn APT Pakete entfernen würde.
- Paket-Neuinstallation über `apt-get install --reinstall --no-remove`; zuvor abweichende reguläre Dateien werden im Benutzerprofil gesichert und können über eine bestätigte Rollback-Funktion zurückgespielt werden.
- Netzwerkprüfung erweitert um Schnittstellen/IP-Adressen, IPv4-/IPv6-Routen sowie DNS-Konfiguration (`resolvectl` oder `/etc/resolv.conf`).
- Netzwerkprüfung bleibt lesend; keine Firewall-Regeln oder Netzwerkeinstellungen werden automatisch verändert.
- Grenzen der Sicherung und Prüfung werden in der Oberfläche bzw. Dokumentation erläutert.


## Version 0.3.11 – Angenehmerer Alarmton
- Den eingebauten Alarmton durch einen kurzen, weich ein- und ausgeblendeten Dreiklang mit Sinuswellen ersetzt.
- Das harte Rechtecksignal entfernt, das auf Lautsprechern als Knacken wahrgenommen werden konnte.
- WAV-Auswahl, Audio-Backends, Gerätewahl und Lautstärkeeinstellung bleiben unverändert.

## Version 0.3.9 – Fenster breiter

- Standardbreite des Hauptfensters von 1040 auf 1116 logische Pixel erhöht (ca. 2 cm bei 96 DPI).
- Höhe und Mindestgröße bleiben unverändert.

# Änderungsprotokoll

## Version 0.3.45
- Programmversion, Debian-Paketversion und README auf 0.3.45 vereinheitlicht.
- README-Installations- und Build-Anweisungen auf die tatsächlichen Paket- und Archivnamen aktualisiert.
- AIDE-Voraussetzungen präzisiert: `sudo aideinit` ist eine einmalige, bewusst manuelle Initialisierung nach Prüfung des Systemzustands; ohne aktivierte Referenzdatenbank ist kein aussagekräftiger Integritätsvergleich möglich.
- Abhängigkeiten für Lynis, fail2ban und Qt PrintSupport sowie die bewusst manuelle fail2ban-Aktivierung verständlich dokumentiert.

## 0.3.35
- Paketprüfung erweitert: Abweichungen aus `dpkg --verify` werden soweit möglich installierten Paketen zugeordnet.
- Für einzeln ausgewählte Pakete wird vor der Reparatur ein APT-Simulationslauf ausgeführt; Reparaturen werden abgebrochen, wenn APT Pakete entfernen würde.
- Paket-Neuinstallation über `apt-get install --reinstall --no-remove`; zuvor abweichende reguläre Dateien werden im Benutzerprofil gesichert und können über eine bestätigte Rollback-Funktion zurückgespielt werden.
- Netzwerkprüfung erweitert um Schnittstellen/IP-Adressen, IPv4-/IPv6-Routen sowie DNS-Konfiguration (`resolvectl` oder `/etc/resolv.conf`).
- Netzwerkprüfung bleibt lesend; keine Firewall-Regeln oder Netzwerkeinstellungen werden automatisch verändert.
- Grenzen der Sicherung und Prüfung werden in der Oberfläche bzw. Dokumentation erläutert.


## Version 0.3.8 – Erkennungen zuverlässig anzeigen
- Fehlende Methode `report_detections()` ergänzt, die ClamAV-`FOUND`-Meldungen aus Scan-Ausgaben und Echtzeitprotokollen erkennt.
- Erkannte Dateifunde werden mit Zeitstempel dauerhaft in `security-events.json` gespeichert und im Tab „Sicherheitsereignisse“ angezeigt.
- Ereignisliste wird nach jedem Scan aktualisiert; erkannte Dateipfade stehen für Quarantäne und Löschen zur Verfügung.
- Zeilenumbrüche in Ereigniseinträgen korrigiert.

- Das Ergebnisfenster zeigt eine verständliche Gesamtbewertung; vollständige Rohdaten sind aufklappbar.
- Die Bewertung berücksichtigt alle erkannten nftables-Eingangsketten und meldet gemischte oder unklare Richtlinien nicht fälschlich als sicher.
- „Quarantäne anzeigen“ öffnet jetzt den Quarantäne-Tab und aktualisiert dessen Inhalt.

## Version 0.3.6

- Netzwerk- und Firewall-Prüfung fordert für `ss -tulpen` und `nft list ruleset` jeweils ausdrücklich Administratorrechte über PolicyKit (`pkexec`) an.
- Ergebnisbewertung ergänzt: lauschende Sockets, allgemein gebundene Netzwerkadressen, erkannte nftables-Eingangsketten sowie verständliche Statusmeldungen (Gut, Warnung oder nicht vollständig prüfbar).
- Die Prüfung bleibt strikt lesend und verändert keine Firewall-Regeln.
- Grenzen der Prüfung werden im Ergebnis erläutert; eine lokale Regelprüfung wird nicht als Garantie externer Sicherheit dargestellt.

# Änderungsprotokoll

## Version 0.3.45
- Programmversion, Debian-Paketversion und README auf 0.3.45 vereinheitlicht.
- README-Installations- und Build-Anweisungen auf die tatsächlichen Paket- und Archivnamen aktualisiert.
- AIDE-Voraussetzungen präzisiert: `sudo aideinit` ist eine einmalige, bewusst manuelle Initialisierung nach Prüfung des Systemzustands; ohne aktivierte Referenzdatenbank ist kein aussagekräftiger Integritätsvergleich möglich.
- Abhängigkeiten für Lynis, fail2ban und Qt PrintSupport sowie die bewusst manuelle fail2ban-Aktivierung verständlich dokumentiert.

## 0.3.35
- Paketprüfung erweitert: Abweichungen aus `dpkg --verify` werden soweit möglich installierten Paketen zugeordnet.
- Für einzeln ausgewählte Pakete wird vor der Reparatur ein APT-Simulationslauf ausgeführt; Reparaturen werden abgebrochen, wenn APT Pakete entfernen würde.
- Paket-Neuinstallation über `apt-get install --reinstall --no-remove`; zuvor abweichende reguläre Dateien werden im Benutzerprofil gesichert und können über eine bestätigte Rollback-Funktion zurückgespielt werden.
- Netzwerkprüfung erweitert um Schnittstellen/IP-Adressen, IPv4-/IPv6-Routen sowie DNS-Konfiguration (`resolvectl` oder `/etc/resolv.conf`).
- Netzwerkprüfung bleibt lesend; keine Firewall-Regeln oder Netzwerkeinstellungen werden automatisch verändert.
- Grenzen der Sicherung und Prüfung werden in der Oberfläche bzw. Dokumentation erläutert.


## 0.3.5
- Erkannte ClamAV-Funde im Tab „Sicherheitsereignisse“ auswählbar gemacht.
- Aktionen zum bestätigten Verschieben eines erkannten Fundes in Quarantäne und zum endgültigen Löschen ergänzt.
- Eigenen Quarantäne-Tab mit Aktualisieren, Wiederherstellen und endgültigem Löschen ergänzt.
- Quarantäne-Datenbank und Verzeichnis werden zuverlässig angelegt; Dateipfade werden vor Aktionen geprüft.
- SHA-256 wird dateispeichernd berechnet, statt die gesamte Datei in den Arbeitsspeicher zu laden.


## 0.3.4
- README ergänzt: tatsächliche Gruppenzuweisung der Echtzeit-Protokolldatei mit `stat` prüfen.
- Reparatur dokumentiert, falls die Datei `root:root` statt `root:adm` gehört (`chown root:adm`, Modus `0640`).
- Versions- und Installationsangaben auf 0.3.4 aktualisiert.


## 0.3.3
- Startfehler behoben: `QTimer` wird aus `PySide6.QtCore` importiert.


## 0.3.2
- README ergänzt: Einrichtung der Gruppenmitgliedschaft `adm`, Ab- und erneute Anmeldung sowie Prüfung mit `id -nG` für das Lesen der Echtzeitprotokolle dokumentiert.


## 0.3.1
- Echtzeit-Funde aus `lunasecurity-onaccess.log` werden im Hintergrund geprüft und als Sicherheitsereignisse gespeichert.
- Echtzeitfunde lösen einen roten Hinweis in LunaSecurity und eine Desktop-Benachrichtigung aus.
- Rootkit-, AIDE-, System-Audit-, Netzwerk- und YARA-Prüfungen laufen in einem separaten QThread; die GUI bleibt bedienbar.
- On-Access-Protokoll wird mit Gruppe `adm` und Modus 0640 angelegt.
- Sicherheitsereignisse werden im eigenen Tab angezeigt und können dort bewusst gelöscht werden.
- Dashboard-Karten benennen die vorhandenen Prüfmodule korrekt.

## 0.3.0
- Manuelle ClamAV-Funde werden in der Oberfläche hervorgehoben und gespeichert.
- Sicherheitsereignis-Protokoll ergänzt.

## 0.3.10
- Audio-Einstellungen mit automatischer Backend-Erkennung für PipeWire, PulseAudio und ALSA ergänzt.
- Auswahl einer WAV-Alarmdatei, Lautstärkeregelung und Testalarm hinzugefügt.
- Bei neu erkannten ClamAV-Funden wird eine Desktop-Traymeldung ausgelöst und – sofern aktiviert – ein akustischer Alarm abgespielt.
- Audioeinstellungen werden dauerhaft über QSettings gespeichert.

## Version 0.3.20 – Dokumentation überarbeitet

- README vollständig als Installations-, Bedienungs- und Referenzdokument neu aufgebaut.
- Versionshistorie bleibt im CHANGELOG.md; die README beschreibt Funktionen, Voraussetzungen, Datenpfade, Sicherheitsgrenzen und Fehlerdiagnose.
- README und CHANGELOG werden mit dem Debian-Paket unter `/usr/share/doc/lunasecurity/` installiert.

## 0.3.38
- Tray-Symbol startet jetzt neutral mit dem Sicherheitsstatus-Symbol statt dauerhaft mit einem gelben Warn-Dreieck.
- Bei gespeicherten Sicherheitsfunden wechselt das Tray-Symbol auf Warnung; nach dem Leeren bzw. Entfernen aller Ereignisse wird es wieder neutral.
- Tooltip des Tray-Symbols zeigt den aktuellen Warnstatus.
- GTK-Tray-Aktualisierung erfolgt thread-sicher über GLib.


## 0.3.59
- Importfehler beim Start behoben: `QPoint` wird korrekt aus `PySide6.QtCore` importiert.


## 0.3.60
- Die Schaltflächen „Virensignaturen jetzt aktualisieren“ und „Echtzeitschutz aktivieren/deaktivieren“ stehen jetzt nebeneinander in einer gemeinsamen Zeile.


## 0.4.32 – VirusTotal-Abgleich fertiggestellt
- Dashboard-Schaltfläche „VirusTotal-Check“ ergänzt.
- Datei auswählen, SHA-256 lokal berechnen und vorhandenen VirusTotal-Bericht über API v3 abrufen.
- Anzeige von Erkennungen, verdächtigen Treffern, nicht erkannten und unauffälligen Anbietern.
- API-Schlüssel wird aus den Einstellungen verwendet; Datei-Upload findet nicht statt.
- Fehlerbehandlung für ungültigen Schlüssel, fehlende Berechtigung, unbekannten Hash und API-Limit.
