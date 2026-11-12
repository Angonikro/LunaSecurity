from __future__ import annotations
import os, shutil, subprocess, sys, threading, time, json, wave, tempfile, struct, math, signal, re, hashlib, urllib.request, urllib.error, urllib.parse
from pathlib import Path
from PySide6.QtCore import QObject, Signal, Slot, QThread, QSettings, QTimer, QTranslator, QLocale, Qt, QEvent, QPoint, QMarginsF, QRectF
from PySide6.QtGui import QAction, QIcon, QTextDocument, QTextOption, QFont, QPainter, QLinearGradient, QRadialGradient, QColor, QPolygon, QPen, QBrush, QTextCursor, QPainterPath
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtGui import QPageSize, QPageLayout
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QDialog,
    QLabel, QPushButton, QTextEdit, QProgressBar, QCheckBox, QMessageBox, QFrame, QFileDialog, QTabWidget, QGroupBox, QScrollArea, QSystemTrayIcon, QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QComboBox, QSlider, QSpinBox, QStyle, QInputDialog, QSizePolicy, QStackedWidget, QLineEdit)

def _german_file_dialog(parent, title, start_dir, directory_mode=False, file_filter="Alle Dateien (*)"):
    """Einheitlicher Qt-Dateidialog für Datei- und Ordnerauswahl, vollständig deutsch."""
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QLabel, QPushButton, QComboBox

    dialog = QFileDialog(parent, title, str(start_dir))
    dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
    dialog.setFileMode(QFileDialog.FileMode.Directory if directory_mode else QFileDialog.FileMode.ExistingFile)
    # Gleiche Dialogansicht für Datei- und Ordnerauswahl; nur der Auswahlmodus ändert sich.
    dialog.setOption(QFileDialog.Option.ShowDirsOnly, False)
    labels = ("Look in:", "Directory:" if directory_mode else "File name:", "File type:",
              "Choose folder" if directory_mode else "Choose file", "Cancel") if APP_LANGUAGE == "en" else (
              "Suchen in:", "Verzeichnis:" if directory_mode else "Dateiname:", "Dateityp:",
              "Ordner auswählen" if directory_mode else "Datei auswählen", "Abbrechen")
    dialog.setLabelText(QFileDialog.DialogLabel.LookIn, labels[0])
    dialog.setLabelText(QFileDialog.DialogLabel.FileName, labels[1])
    dialog.setLabelText(QFileDialog.DialogLabel.FileType, labels[2])
    dialog.setLabelText(QFileDialog.DialogLabel.Accept, labels[3])
    dialog.setLabelText(QFileDialog.DialogLabel.Reject, labels[4])
    dialog.setNameFilter("Verzeichnisse (*)" if directory_mode else file_filter)

    def translate_widgets():
        if APP_LANGUAGE == "en":
            return
        for label in dialog.findChildren(QLabel):
            value = label.text().replace("&", "").strip().rstrip(":")
            mapping = {
                "Look in": "Suchen in:",
                "Directory": "Verzeichnis:",
                "File name": "Dateiname:",
                "Files of type": "Dateityp:",
            }
            if value in mapping:
                label.setText(mapping[value])
        for button in dialog.findChildren(QPushButton):
            value = button.text().replace("&", "").strip()
            if value in ("Choose", "Select", "Open"):
                button.setText("Ordner auswählen" if directory_mode else "Datei auswählen")
            elif value == "Cancel":
                button.setText("Abbrechen")
        for combo in dialog.findChildren(QComboBox):
            for index in range(combo.count()):
                if combo.itemText(index).strip() == "Directories":
                    combo.setItemText(index, "Verzeichnisse")
                elif combo.itemText(index).strip() == "All files (*)":
                    combo.setItemText(index, "Alle Dateien (*)")

        # Nach Qt-internem Neuaufbau die Beschriftungen erneut setzen.
        dialog.setLabelText(QFileDialog.DialogLabel.LookIn, "Suchen in:")
        dialog.setLabelText(QFileDialog.DialogLabel.FileName,
                            "Verzeichnis:" if directory_mode else "Dateiname:")
        dialog.setLabelText(QFileDialog.DialogLabel.FileType, "Dateityp:")
        dialog.setLabelText(QFileDialog.DialogLabel.Accept,
                            "Ordner auswählen" if directory_mode else "Datei auswählen")
        dialog.setLabelText(QFileDialog.DialogLabel.Reject, "Abbrechen")

    timer = QTimer(dialog)
    timer.setInterval(75)
    timer.timeout.connect(translate_widgets)
    dialog.finished.connect(timer.stop)
    timer.start()
    QTimer.singleShot(0, translate_widgets)
    return dialog


def _choose_file(parent, title, start_dir, file_filter="Alle Dateien (*)"):
    dialog = _german_file_dialog(parent, title, start_dir, False, file_filter)
    if dialog.exec() == QFileDialog.DialogCode.Accepted:
        files = dialog.selectedFiles()
        return (files[0], dialog.selectedNameFilter()) if files else ("", "")
    return "", ""


def _choose_directory(parent, title, start_dir):
    dialog = _german_file_dialog(parent, title, start_dir, True)
    if dialog.exec() == QFileDialog.DialogCode.Accepted:
        files = dialog.selectedFiles()
        return files[0] if files else ""
    return ""

from . import __version__
from .tray import GtkStatusTray
from . import security_modules as sec


def _clamav_detection_type(detail):
    """Return the ClamAV signature name from a '<path>: <signature> FOUND' line."""
    line = str(detail).strip()
    if not (line.endswith("FOUND") or " FOUND " in line):
        return ""
    prefix = line.rsplit("FOUND", 1)[0].rstrip()
    if ": " not in prefix:
        return ""
    return prefix.rsplit(": ", 1)[-1].strip()


class GermanQtTranslator(QTranslator):
    """Übersetzt die eingebauten Qt-Dialoge unabhängig von der Systemsprache."""
    _translations = {
        "Yes": "Ja", "&Yes": "&Ja", "No": "Nein", "&No": "&Nein",
        "OK": "OK", "Ok": "OK", "Cancel": "Abbrechen", "&Cancel": "&Abbrechen",
        "Close": "Schließen", "&Close": "&Schließen", "Apply": "Übernehmen",
        "Save": "Speichern", "&Save": "&Speichern", "Open": "Öffnen",
        "&Open": "&Öffnen", "Discard": "Verwerfen", "Retry": "Erneut versuchen",
        "Ignore": "Ignorieren", "Abort": "Abbrechen", "Help": "Hilfe",
        "Don't Save": "Nicht speichern", "&Don't Save": "&Nicht speichern",
        "Show Details...": "Details anzeigen...", "Hide Details...": "Details ausblenden...",
        "Look in:": "Suchen in:", "File name:": "Dateiname:",
        "Files of type:": "Dateityp:", "Name": "Name", "Size": "Größe",
        "Type": "Typ", "Date Modified": "Änderungsdatum", "Date:": "Datum:",
        "All Files (*)": "Alle Dateien (*)", "Back": "Zurück", "Forward": "Vorwärts",
        "Parent Directory": "Übergeordnetes Verzeichnis", "Create New Folder": "Neuen Ordner erstellen",
        "Folder": "Ordner", "File": "Datei", "Select": "Auswählen",
        "Enter a name": "Namen eingeben", "Enter a value": "Wert eingeben",
    }

    def translate(self, context, sourceText, disambiguation=None, n=-1):
        source = str(sourceText or "")
        # Unbekannte Qt-Texte unverändert lassen, niemals versehentlich leere
        # Beschriftungen erzeugen.
        return self._translations.get(source, source)



class EnglishMessageBoxFix(QObject):
    """Translates application message boxes when English is selected."""
    def eventFilter(self, watched, event):
        if isinstance(watched, QMessageBox) and event.type() == QEvent.Type.Show and APP_LANGUAGE == "en":
            mapping = EN_TRANSLATIONS
            title = watched.windowTitle()
            text = watched.text()
            info = watched.informativeText()
            details = watched.detailedText()
            if title: watched.setWindowTitle(mapping.get(title, title))
            if text: watched.setText(mapping.get(text, text))
            if info: watched.setInformativeText(mapping.get(info, info))
            if details: watched.setDetailedText(mapping.get(details, details))
        return super().eventFilter(watched, event)

class GermanDialogButtonFix(QObject):
    """Erzwingt sichtbare deutsche Beschriftungen auf allen QMessageBox-Buttons."""
    _labels = {
        QMessageBox.StandardButton.Ok: "OK",
        QMessageBox.StandardButton.Yes: "Ja",
        QMessageBox.StandardButton.No: "Nein",
        QMessageBox.StandardButton.Cancel: "Abbrechen",
        QMessageBox.StandardButton.Close: "Schließen",
        QMessageBox.StandardButton.Save: "Speichern",
        QMessageBox.StandardButton.Open: "Öffnen",
        QMessageBox.StandardButton.Apply: "Übernehmen",
        QMessageBox.StandardButton.Discard: "Verwerfen",
        QMessageBox.StandardButton.Retry: "Erneut versuchen",
        QMessageBox.StandardButton.Ignore: "Ignorieren",
        QMessageBox.StandardButton.Abort: "Abbrechen",
        QMessageBox.StandardButton.Help: "Hilfe",
        QMessageBox.StandardButton.Reset: "Zurücksetzen",
        QMessageBox.StandardButton.RestoreDefaults: "Standard wiederherstellen",
    }

    def eventFilter(self, watched, event):
        if isinstance(watched, QMessageBox) and event.type() == QEvent.Type.Show:
            for standard_button, label in self._labels.items():
                button = watched.button(standard_button)
                if button is not None:
                    button.setText(label)
                    button.setIcon(QIcon())
                    button.setMinimumWidth(max(76, button.fontMetrics().horizontalAdvance(label) + 28))
        return super().eventFilter(watched, event)

APP_LANGUAGE = "de"
APP_QT_TRANSLATOR = None
APP_DIALOG_BUTTON_FIX = None
APP_EN_DIALOG_FIX = None
EN_TRANSLATIONS = {'Sicherheitsübersicht für dein Linux-System': 'Security overview for your Linux system', 'Dateien / Ordner scannen': 'Scan files / folders', 'Home-Verzeichnis prüfen': 'Scan home directory', 'Eigenes Profil': 'Custom profile', 'Standard (Empfohlen)': 'Standard (Recommended)', 'Hoher Schutz': 'High protection', 'Maximaler Schutz': 'Maximum protection', 'Profil verwalten …': 'Manage profiles …', 'Übersicht': 'Overview', 'Systemschutz – Übersicht': 'System protection – Overview', 'Sicherheitsprüfung': 'Security scan', 'Protokoll leeren': 'Clear log', 'Jetzt aktualisieren': 'Update now', 'System-Informationen': 'System information', 'Firewall-Bericht': 'Firewall report', 'Schnellscan': 'Quick scan', 'Komplettscan': 'Full scan', '⌂  Home-Verzeichnis': '⌂  Home directory', '▣  Vollständiger Systemscan': '▣  Full system scan', 'Vor jedem Scan automatisch Virensignaturen mit freshclam aktualisieren': 'Automatically update virus signatures with freshclam before each scan', 'Virensignatur aktualisieren': 'Update virus signatures', 'Systemscan': 'System scan', 'Echtzeitschutz aktivieren': 'Enable real-time protection', 'Echtzeitschutz deaktivieren': 'Disable real-time protection', 'Echtzeitschutz: Status wird geprüft …': 'Real-time protection: checking status …', 'Beim Schließen im Infobereich weiterlaufen': 'Keep running in the system tray when closed', 'Beim Start direkt im Infobereich starten': 'Start directly in the system tray', 'LunaSecurity automatisch bei der Anmeldung starten': 'Start LunaSecurity automatically at login', 'Erweiterte Sicherheit': 'Advanced security', 'Sicherheitsereignisse': 'Security events', '⚠ {count} gespeicherte Sicherheitsereignisse – Details im Tab „Virenschutz“': '⚠ {count} saved security events – see the “Virus protection” tab', 'Quarantäne': 'Quarantine', 'Systemschutz': 'System protection', 'Reparatur & Wiederherstellung': 'Repair & recovery', 'Netzwerk': 'Network', 'Dateiwerkzeuge': 'File tools', 'Alarm & Audio': 'Alerts & audio', 'Einstellungen': 'Settings', 'Allgemeine Programmoptionen': 'General application options', 'ClamAV – Scanoptionen': 'ClamAV – scan options', 'VirusTotal – API': 'VirusTotal – API', 'VirusTotal-API-Schlüssel': 'VirusTotal API key', 'API-Schlüssel wird lokal in deinen LunaSecurity-Einstellungen gespeichert und bei der Abfrage verwendet.': 'The API key is stored locally in your LunaSecurity settings and used for lookups.', 'ClamAV-Größenlimit-Überschreitungen nicht als Bedrohung zählen': 'Do not count ClamAV file-size limit exceedances as threats', 'Größenlimit': 'Size limit', 'Diese Optionen werden bei Datei- und Ordnerscans an ClamAV übergeben.': 'These options are passed to ClamAV during file and folder scans.', 'Potenziell unerwünschte Programme (PUP) erkennen': 'Detect potentially unwanted programs (PUPs)', 'Heuristische Erkennung verwenden': 'Use heuristic detection', 'Versteckte Dateien und Ordner untersuchen': 'Scan hidden files and folders', 'Dateien größer als 20 MB untersuchen (bis 2 GB)': 'Scan files larger than 20 MB (up to 2 GB)', 'Unterordner rekursiv durchsuchen': 'Scan subfolders recursively', 'Hier findest du alle aktivierbaren Optionen der Hauptoberfläche.': 'Here you can find all configurable options for the main interface.', 'Akustischen Alarm aktivieren': 'Enable audible alarm', 'WAV auswählen': 'Select WAV', 'Eingebauten Sound verwenden': 'Use built-in sound', 'Testalarm abspielen': 'Play test alarm', 'Audio-Ausgabe': 'Audio output', 'Ausgabegerät': 'Output device', 'Lautstärke': 'Volume', 'Datei auswählen und in Quarantäne verschieben': 'Select file and move to quarantine', 'Quarantäne anzeigen': 'Show quarantine', 'YARA-Regeln aktualisieren': 'Update YARA rules', 'Dashboard aktualisieren': 'Refresh dashboard', 'Bericht kopieren': 'Copy report', 'Vollständige Scanner-Ausgabe': 'Full scanner output', 'Empfohlene nächste Schritte': 'Recommended next steps', 'Liste aktualisieren': 'Refresh list', 'Sichern & deaktivieren': 'Back up & disable', 'Eintrag wiederherstellen': 'Restore entry', 'Paket sichern & reparieren': 'Back up & repair package', 'Gesicherte Paketdateien wiederherstellen': 'Restore backed-up package files', 'Installierte Pakete auf Dateiänderungen prüfen': 'Check installed packages for file changes', 'Datei endgültig löschen': 'Delete file permanently', 'In Quarantäne verschieben': 'Move to quarantine', 'Alarm bei erkannten Bedrohungen': 'Alert when threats are detected', 'Rootkit-Prüfung starten (rkhunter + chkrootkit)': 'Run rootkit check (rkhunter + chkrootkit)', 'Systemintegrität prüfen (AIDE)': 'Check system integrity (AIDE)', 'System-Audit (Autostart, Dienste, Cron, SSH)': 'System audit (autostart, services, cron, SSH)', 'Benutzer-Autostart': 'User autostart', 'Paket neu installieren': 'Reinstall package', 'Schließen': 'Close', 'Wiederherstellen': 'Restore', 'Prüfung abbrechen': 'Cancel check', 'Scan abbrechen': 'Cancel scan', 'Ergebnis kopieren': 'Copy result', 'Scan-Protokoll': 'Scan log', 'Verstrichene Zeit: 00:00': 'Elapsed time: 00:00', '● Aktiv': '● Active', 'Prüfung wird vorbereitet …': 'Preparing check …', 'ClamAV-Scan läuft': 'ClamAV scan running', 'Keine Paketsicherungen gefunden.': 'No package backups found.'}

EN_TRANSLATIONS.update({
    "Echtzeitschutz – Bedrohung erkannt": "Real-time protection – Threat detected",
    "LunaSecurity – Echtzeitschutz: Bedrohung erkannt": "LunaSecurity – Real-time protection: Threat detected",
    "Der Echtzeitschutz hat eine Bedrohung gefunden": "Real-time protection detected a threat",
    "Bedrohung erkannt – Details stehen im Prüfbericht.": "Threat detected – see the scan report for details.",
})
EN_TRANSLATIONS.update({
    'Installierte Virensignaturen:': 'Installed virus signatures:',
    'Echtzeitschutz:': 'Real-time protection:',
    'Echtzeitschutz: Hintergrundauftrag läuft …': 'Real-time protection: background task running …',
    'Aktiv': 'Active',
    'Aus': 'Off',
    'Status unklar': 'Status unknown',
    'Echtzeitschutz ist aktiv': 'Real-time protection is active',
    'Echtzeitschutz ist ausgeschaltet': 'Real-time protection is disabled',
    'Status des Echtzeitschutzes konnte nicht ermittelt werden': 'Could not determine real-time protection status',
    'FEHLER: Der Scanumfang konnte nicht aus dem Scanfenster übernommen werden. Bitte das Scan-Protokoll im Scanfenster prüfen.': 'ERROR: The scan scope could not be retrieved from the scan window. Please check the scan log in the scan window.',
    'FEHLER: Das Scanfenster ist nicht verfügbar; der Scanumfang konnte nicht ins Hauptprotokoll übernommen werden.': 'ERROR: The scan window is unavailable; the scan scope could not be copied to the main log.',
    'Noch keine erkannten Bedrohungen gespeichert.': 'No detected threats have been saved yet.',
    '⚠ BEDROHUNG ERKANNT – Details siehe Sicherheitsereignisse': '⚠ THREAT DETECTED – see Security events for details',
    'Echtzeitschutz wird im Hintergrund aktiviert …': 'Real-time protection is being enabled in the background …',
    'Echtzeitschutz wird im Hintergrund deaktiviert …': 'Real-time protection is being disabled in the background …',
    'Hinweis: Der Dienststatus konnte nicht sicher bestätigt werden.': 'Note: The service status could not be confirmed.',
})
EN_TRANSLATIONS.update({'Virenschutz': 'Virus protection', 'ClamAV-Scanner und Echtzeitschutz': 'ClamAV scanner and real-time protection', 'Systemschutz': 'System protection', 'Rootkit-, AIDE- und System-Audit': 'Rootkit, AIDE and system audit', 'Ports und Firewall-Regeln': 'Ports and firewall rules', 'Noch keine erkannten Bedrohungen gespeichert.': 'No detected threats have been saved yet.', 'Ordner auswählen': 'Select folder', 'Datei auswählen': 'Select file', 'Sicherheitsereignisse': 'Security events'})

EN_TRANSLATIONS.update({'Was möchtest du scannen?': 'What would you like to scan?', 'Datei zum Scannen auswählen': 'Select file to scan', 'Ordner zum Scannen auswählen': 'Select folder to scan', 'Scanbereich:': 'Scan area:', 'Root-Rechte werden nur für geschützte Systembereiche benötigt.': 'Administrator privileges are only required for protected system areas.', 'Geprüfte Dateien': 'Files checked', 'Bedrohungen': 'Threats', 'Nicht lesbar': 'Unreadable', 'Übersprungen': 'Skipped', 'Aktuelle Datei:': 'Current file:', 'Verstrichene Zeit:': 'Elapsed time:', 'Scan läuft …': 'Scan running …', 'Abbruch läuft …': 'Cancelling …', 'Der Scan wird abgebrochen …': 'Cancelling the scan …', 'Abgebrochen': 'Cancelled', 'Abgeschlossen': 'Completed', 'Scan abgebrochen. Das bisherige Ergebnis steht im Scan-Protokoll.': 'Scan cancelled. The results so far are available in the scan log.', 'Scan abgeschlossen. Das vollständige Ergebnis steht im Scan-Protokoll.': 'Scan completed. The full result is available in the scan log.', 'fail2ban-Status prüfen': 'Check fail2ban status', 'fail2ban-Verbindung:': 'fail2ban connection:', 'Gesamtstatus:': 'Overall status:', 'SSH-Jail:': 'SSH jail:'})
EN_TRANSLATIONS.update({'Darstellung & Sprache': 'Appearance & language', 'Sprache / Language': 'Language', 'Design / Theme': 'Theme', 'Dunkel – Graphit': 'Dark – Graphite', 'Hell – Luna': 'Light – Luna', 'Allgemeine Programmoptionen': 'General application options', 'Zusätzliche Systemhärtungsprüfung und Überwachung. Diese Funktionen lesen den Systemstatus und ändern keine Sicherheitsregeln.': 'Additional system-hardening checks and monitoring. These functions read system status and do not change security rules.', 'Erkannte Dateien auswählen, um sie zu isolieren oder zu löschen.': 'Select detected files to quarantine or delete.', 'Ausgewählten Fund in Quarantäne': 'Quarantine selected detection', 'Gefundene Datei löschen': 'Delete detected file', 'Ereignisprotokoll leeren': 'Clear event log', 'Aktualisieren': 'Refresh', 'Endgültig löschen': 'Delete permanently', 'Prüft installierte Paketdateien. Bei Abweichungen kannst du das betroffene Paket über APT neu installieren.': 'Checks installed package files. If differences are found, you can reinstall the affected package through APT.', 'Netzwerk- und Firewall-Sicherheitscheck (mit Admin-Abfrage)': 'Network and firewall security check (administrator authentication required)', 'Datei/Ordner für YARA auswählen': 'Select file/folder for YARA', 'Quarantäne anzeigen': 'Show quarantine', 'Hier findest du alle aktivierbaren Optionen der Hauptoberfläche.': 'Here you can find all configurable options for the main interface.', 'Aktiviert ClamAVs Erkennung potenziell unerwünschter Anwendungen. Kann zusätzliche Treffer liefern.': 'Enables ClamAV detection of potentially unwanted applications. May produce additional detections.', 'Aktiviert oder deaktiviert ClamAVs heuristische Erkennung.': 'Enables or disables ClamAV heuristic detection.', 'Bezieht bei Ordnerscans auch Einträge ein, deren Name mit einem Punkt beginnt.': 'Includes entries whose names begin with a dot when scanning folders.', 'Erhöht die ClamAV-Grenzen für Dateigröße und entpackte Scanmenge auf bis zu 2 GB. Das kann deutlich länger dauern.': 'Raises ClamAV file-size and extracted-scan limits to 2 GB. This can take considerably longer.', 'Wenn deaktiviert, werden bei einem Ordnerscan nur Dateien direkt im ausgewählten Ordner geprüft.': 'When disabled, only files directly inside the selected folder are scanned.', 'LunaSecurity führt Prüfungen nachvollziehbar aus. Rootkit- und Integritätsprüfungen können Administratorrechte benötigen. Funde werden nicht automatisch gelöscht.': 'LunaSecurity performs traceable checks. Rootkit and integrity checks may require administrator privileges. Detections are not deleted automatically.', 'Beim Schließen im Infobereich weiterlaufen': 'Keep running in the system tray when closed', 'Beim Start direkt im Infobereich starten': 'Start directly in the system tray', 'LunaSecurity automatisch bei der Anmeldung starten': 'Start LunaSecurity automatically at login', 'Root-Rechte werden nur für geschützte Systembereiche benötigt.': 'Administrator privileges are only required for protected system areas.', 'Bericht kopieren': 'Copy report', 'PDF-Bericht konnte nicht gespeichert werden': 'Could not save PDF report', 'Prüfung wird vorbereitet …': 'Preparing check …', 'Aktuelle Datei: wird vorbereitet …': 'Current file: preparing …', 'Scan-Ziel auswählen': 'Select scan target', 'Port gezielt sperren': 'Block a specific port'})
EN_TRANSLATIONS.update({'0\nBedrohungen': '0\nThreats', '0\nGeprüfte Dateien': '0\nFiles checked', '0\nNicht lesbar': '0\nUnreadable', '0\nÜbersprungen': '0\nSkipped', 'Debian-Paketintegrität und Reparatur': 'Debian package integrity and repair', 'Einträge dieses Benutzerkontos anzeigen, reversibel deaktivieren oder zurückholen.': 'View entries for this user account, disable them reversibly, or restore them.', 'Ergebnisse von rkhunter und chkrootkit. Warnungen können Fehlalarme sein und müssen einzeln bewertet werden.': 'Results from rkhunter and chkrootkit. Warnings may be false positives and must be assessed individually.', 'Kein Scan-Ziel ausgewählt': 'No scan target selected', 'LunaSecurity – ClamAV-Systemprüfung': 'LunaSecurity – ClamAV system scan', 'LunaSecurity – Linux Security Suite': 'LunaSecurity – Linux Security Suite', 'LunaSecurity – Rootkit-Prüfbericht': 'LunaSecurity – rootkit report', 'Lynis-Sicherheitsprüfung starten': 'Run Lynis security check', 'PipeWire-, PulseAudio- und ALSA-Ausgabe werden automatisch erkannt. Geräteauswahl wird bei unterstützten Backends angewendet.': 'PipeWire, PulseAudio and ALSA outputs are detected automatically. Device selection is applied for supported backends.', 'Prüfergebnisse und Reparaturprotokoll': 'Check results and repair log', 'Reparaturen nur nach deiner Bestätigung. Vor Änderungen werden Sicherungen angelegt. Systemdateien und Rootkit-Funde werden nicht blind verändert.': 'Repairs are performed only after your confirmation. Backups are created before changes. System files and rootkit detections are never modified blindly.', 'Reparaturhilfe öffnen': 'Open repair help', 'Scan-Ergebnis kopieren': 'Copy scan result', 'Sicherheitsbericht als HTML speichern': 'Save security report as HTML', 'Sicherheitsbericht als PDF speichern': 'Save security report as PDF', 'Vorherige Sicherungen auswählen und zurückspielen. Bereits vorhandene Dateien werden nicht überschrieben.': 'Select and restore previous backups. Existing files will not be overwritten.', 'Wiederherstellung': 'Recovery', 'fail2ban-Status prüfen': 'Check fail2ban status'})
EN_TRANSLATIONS.update({'Es läuft bereits eine Sicherheitsaufgabe.': 'A security task is already running.', 'Es läuft bereits eine Sicherheitsprüfung.': 'A security check is already running.', 'Bitte zuerst eine Datei auswählen.': 'Please select a file first.', 'Bitte zuerst einen Fund mit erkannter Dateiangabe auswählen.': 'Please select a detection with an identified file path first.', 'pkexec ist nicht installiert.': 'pkexec is not installed.', 'Keine gesicherten Autostart-Einträge vorhanden.': 'No backed-up autostart entries found.', 'Keine Paketsicherungen gefunden.': 'No package backups found.', 'Das Reparatur-Hilfsprogramm fehlt.': 'The repair helper is missing.', 'Das Wiederherstellungsprogramm fehlt.': 'The recovery helper is missing.', 'Der PDF-Drucker konnte nicht initialisiert werden.': 'The PDF printer could not be initialized.', 'PDF-Bericht konnte nicht gespeichert werden': 'Could not save PDF report', 'Quarantäne fehlgeschlagen': 'Quarantine failed', 'Löschen fehlgeschlagen': 'Delete failed', 'Wiederherstellung fehlgeschlagen': 'Recovery failed', 'Reparatur fehlgeschlagen': 'Repair failed', 'Dateiauswahl abgebrochen; kein Scan gestartet.': 'File selection cancelled; scan not started.', 'Ordnerauswahl abgebrochen; kein Scan gestartet.': 'Folder selection cancelled; scan not started.', 'Die Signaturen konnten nicht aktualisiert werden. Prüfe die Berechtigungen oder ob bereits der freshclam-Dienst läuft.': 'The signatures could not be updated. Check permissions or whether the freshclam service is already running.', 'Der Dienst clamav-freshclam läuft bereits. Er aktualisiert die Signaturen selbst; ein paralleler manueller Aufruf wurde vermieden.': 'The clamav-freshclam service is already running and updates signatures itself; a parallel manual update was avoided.', 'Die neue Signaturversion wurde übernommen.': 'The new signature version has been installed.', 'Die Signaturversion ist unverändert (Datenbank war möglicherweise bereits aktuell).': 'The signature version is unchanged (the database may already have been up to date).', 'Signaturaktualisierung abgeschlossen.': 'Signature update completed.', 'Signaturaktualisierung im Hintergrund beendet.': 'Background signature update finished.', 'Status geprüft.': 'Status checked.', 'Echtzeitschutz aktiviert.': 'Real-time protection enabled.', 'Echtzeitschutz deaktiviert.': 'Real-time protection disabled.', 'Prüfung abgeschlossen': 'Check completed', 'Prüfung abgebrochen': 'Check cancelled', 'Scan abgeschlossen. Das vollständige Ergebnis steht im Scan-Protokoll.': 'Scan completed. The full result is available in the scan log.', 'Scan abgebrochen. Das bisherige Ergebnis steht im Scan-Protokoll.': 'Scan cancelled. The results so far are available in the scan log.', 'Keine erreichbaren Systemverzeichnisse für den Scan gefunden.': 'No accessible system directories found for scanning.', 'Keines der ausgewählten Systemverzeichnisse ist vorhanden.': 'None of the selected system directories exists.'})

APP_DIR = Path.home() / ".config" / "LunaSecurity"
EVENTS_FILE = Path.home() / ".local" / "share" / "LunaSecurity" / "security-events.json"

def record_security_event(kind, detail):
    EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        events = json.loads(EVENTS_FILE.read_text()) if EVENTS_FILE.exists() else []
        if not isinstance(events, list):
            events = []
    except Exception:
        events = []
    from datetime import datetime
    events.insert(0, {"time": datetime.now().astimezone().isoformat(timespec="seconds"),
                      "kind": kind, "detail": detail})
    EVENTS_FILE.write_text(json.dumps(events[:200], ensure_ascii=False, indent=2))
    try:
        EVENTS_FILE.chmod(0o600)
    except OSError:
        pass
    return events[:200]
CLAMAV_DB_DIRS = (Path("/var/lib/clamav"), Path("/var/lib/clamav") / "")

def signature_database_versions():
    """Liest die installierten ClamAV-Signaturversionen über sigtool aus."""
    sigtool = shutil.which("sigtool")
    if not sigtool:
        return "Nicht verfügbar (sigtool nicht installiert)"
    entries = []
    db_dir = Path("/var/lib/clamav")
    for label, names in (("Daily", ("daily.cvd", "daily.cld")),
                         ("Main", ("main.cvd", "main.cld")),
                         ("Bytecode", ("bytecode.cvd", "bytecode.cld"))):
        db_file = next((db_dir / name for name in names if (db_dir / name).is_file()), None)
        if not db_file:
            continue
        try:
            info = subprocess.run([sigtool, "--info", str(db_file)], capture_output=True, text=True, timeout=15)
            output = info.stdout + "\n" + info.stderr
            version = next((line.split(":", 1)[1].strip() for line in output.splitlines()
                            if line.strip().lower().startswith("version:")), "unbekannt")
            build = next((line.split(":", 1)[1].strip() for line in output.splitlines()
                          if line.strip().lower().startswith("built:") or line.strip().lower().startswith("build time:")), "")
            entries.append(f"{label}: v{version}" + (f" ({build})" if build else ""))
        except (OSError, subprocess.SubprocessError):
            entries.append(f"{label}: nicht lesbar")
    return " · ".join(entries) if entries else "Keine ClamAV-Signaturdatenbank gefunden"

class Bridge(QObject):
    show_window = Signal()
    quit_app = Signal()
    scan_result = Signal(str)

_background_workers = set()

class RealtimeWorker(QThread):
    """Führt systemctl-Aufrufe außerhalb des GUI-Threads aus."""
    result = Signal(str, bool, bool)  # Meldung, aktiv, Statusabfrage erfolgreich

    def __init__(self, action="status"):
        super().__init__()
        self.action = action

    def run(self):
        systemctl = shutil.which("systemctl") or "/usr/bin/systemctl"
        try:
            if self.action == "status":
                p = subprocess.run([systemctl, "is-active", "--quiet", "lunasecurity-realtime.service"],
                                   capture_output=True, text=True, timeout=10)
                self.result.emit("Status geprüft.", p.returncode == 0, True)
                return
            pkexec = shutil.which("pkexec")
            if not pkexec:
                self.result.emit("pkexec fehlt. Installiere policykit-1.", False, False)
                return
            if self.action == "enable":
                # Die ClamAV-Konfiguration wird außerhalb des systemd-Startvorgangs
                # eingerichtet. ExecStartPre darf keinen verschachtelten systemctl-Aufruf auslösen.
                configure = "/usr/lib/lunasecurity/configure-realtime"
                setup = subprocess.run([pkexec, configure], capture_output=True, text=True, timeout=180)
                detail = "\n".join(x for x in (setup.stdout.strip(), setup.stderr.strip()) if x)
                if setup.returncode:
                    self.result.emit(detail or f"ClamAV-Konfiguration fehlgeschlagen (Exit-Code {setup.returncode}).", False, False)
                    return
                args = [pkexec, systemctl, "enable", "--now", "lunasecurity-realtime.service"]
            else:
                args = [pkexec, systemctl, "disable", "--now", "lunasecurity-realtime.service"]
                detail = ""
            p = subprocess.run(args, capture_output=True, text=True, timeout=180)
            detail = "\n".join(x for x in (detail, p.stdout.strip(), p.stderr.strip()) if x)
            if p.returncode:
                self.result.emit(detail or f"systemctl ist mit Exit-Code {p.returncode} fehlgeschlagen.", False, False)
                return
            # Bewährte Statusabfrage aus LunaSecurity 0.4.31 beibehalten.
            status = subprocess.run([systemctl, "is-active", "--quiet", "lunasecurity-realtime.service"],
                                    capture_output=True, timeout=10)
            active = status.returncode == 0
            self.result.emit(detail or ("Echtzeitschutz aktiviert." if active else "Echtzeitschutz deaktiviert."), active, True)
        except subprocess.TimeoutExpired:
            self.result.emit("Zeitüberschreitung beim Hintergrundauftrag. Die Oberfläche bleibt bedienbar; bitte Dienststatus prüfen.", False, False)
        except Exception as exc:
            self.result.emit(f"Echtzeitschutz-Auftrag fehlgeschlagen: {exc}", False, False)

class RestoredFileScanWorker(QThread):
    """Prüft eine wiederhergestellte Datei sofort über den laufenden ClamAV-Daemon."""
    result = Signal(str, str, int)  # Pfad, vollständige Ausgabe, Exit-Code

    def __init__(self, path):
        super().__init__()
        self.path = str(path)

    def run(self):
        scanner = shutil.which("clamdscan") or "/usr/bin/clamdscan"
        try:
            process = subprocess.run(
                [scanner, "--fdpass", "--no-summary", self.path],
                capture_output=True, text=True, timeout=90,
            )
            output = "\n".join(
                part.strip() for part in (process.stdout, process.stderr) if part.strip()
            )
            self.result.emit(self.path, output, process.returncode)
        except subprocess.TimeoutExpired:
            self.result.emit(self.path, "Zeitüberschreitung bei der ClamAV-Prüfung der wiederhergestellten Datei.", 2)
        except Exception as exc:
            self.result.emit(self.path, f"ClamAV-Prüfung der wiederhergestellten Datei fehlgeschlagen: {exc}", 2)

class ModuleWorker(QThread):
    result = Signal(str, str)
    output = Signal(str)
    def __init__(self, title, function, cancellable=False):
        super().__init__()
        self.title = title
        self.function = function
        self.cancellable = cancellable
        self._cancel_event = threading.Event()
        self._process = None
        self._process_lock = threading.Lock()
        self._cancel_helper_process = None

    def set_process(self, process):
        with self._process_lock:
            self._process = process
        if self._cancel_event.is_set() and process.poll() is None:
            self._terminate_process(process)

    @staticmethod
    def _terminate_process(process):
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=4)
        except subprocess.TimeoutExpired:
            try: os.killpg(process.pid, signal.SIGKILL)
            except OSError: pass
            try: process.wait(timeout=2)
            except Exception: pass
        except OSError:
            pass

    @staticmethod
    def _reap_cancel_helper(process):
        try:
            process.wait()
        except Exception:
            pass

    def cancel(self):
        self._cancel_event.set()
        # AIDE läuft im Root-Kontext. Der dedizierte Root-Helfer beendet die
        # komplette, von LunaSecurity gestartete Prozessgruppe (inkl. 31_aide_apt).
        try:
            pkexec = shutil.which("pkexec") if self.title in ("Systemintegrität", "Rootkit-Prüfung") else None
            if pkexec and self.title == "Rootkit-Prüfung":
                for scanner_name in ("rkhunter", "chkrootkit"):
                    try:
                        cancel_proc = subprocess.Popen(
                            [pkexec, shutil.which("pkill") or "/usr/bin/pkill", "-TERM", "-x", scanner_name],
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, start_new_session=True)
                        threading.Thread(target=self._reap_cancel_helper, args=(cancel_proc,),
                                         daemon=True).start()
                    except OSError:
                        pass
            helper = "/usr/lib/lunasecurity/aide-cancel-helper"
            if not os.path.isfile(helper):
                helper = str(Path(__file__).resolve().parent.parent / "scripts" / "aide-cancel-helper")
            if self.title == "Systemintegrität" and pkexec and os.path.isfile(helper):
                cancel_proc = subprocess.Popen(
                    [pkexec, helper], stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                # pkexec startet den Root-Helfer als Kindprozess. Den pkexec-
                # Prozess ausdrücklich einsammeln, damit kein Zombie
                # aide-cancel-helper zurückbleibt. wait() läuft separat,
                # damit die GUI beim PolicyKit-Dialog nicht blockiert.
                self._cancel_helper_process = cancel_proc
                threading.Thread(
                    target=self._reap_cancel_helper,
                    args=(cancel_proc,),
                    name="aide-cancel-reaper",
                    daemon=True,
                ).start()
        except OSError:
            pass
        with self._process_lock:
            process = self._process
        if process is not None and process.poll() is None:
            self._terminate_process(process)

    def run_command(self, args, timeout):
        if self._cancel_event.is_set():
            return "Prüfung vom Benutzer abgebrochen."
        try:
            process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       text=True, bufsize=1, start_new_session=True)
            self.set_process(process)
            lines = []
            started = time.monotonic()
            try:
                import select
                while True:
                    if self._cancel_event.is_set():
                        self._terminate_process(process)
                        break
                    if time.monotonic() - started > timeout:
                        self._terminate_process(process)
                        return f"Zeitüberschreitung nach {timeout} Sekunden. Prüfung beendet.\n" + "".join(lines)
                    ready, _, _ = select.select([process.stdout], [], [], 0.15)
                    if ready:
                        line = process.stdout.readline()
                        if line:
                            lines.append(line)
                            self.output.emit(line.rstrip("\r\n"))
                        elif process.poll() is not None:
                            break
                    elif process.poll() is not None:
                        # Restliche gepufferte Ausgabe übernehmen.
                        rest = process.stdout.read() or ""
                        if rest:
                            lines.append(rest)
                            for item in rest.splitlines():
                                self.output.emit(item)
                        break
                process.wait()
            finally:
                try: process.stdout.close()
                except Exception: pass
                with self._process_lock:
                    if self._process is process:
                        self._process = None
            if self._cancel_event.is_set():
                return "Prüfung vom Benutzer abgebrochen.\n" + "".join(lines)
            return "".join(lines).strip() or f"Exit-Code {process.returncode}"
        except OSError as exc:
            return f"Prüfung fehlgeschlagen: {exc}"

    def run(self):
        try:
            result = self.function(self) if self.cancellable else self.function()
            self.result.emit(self.title, str(result))
        except Exception as exc:
            self.result.emit(self.title, f"Fehler: {exc}")

class ScanWorker(QThread):
    result = Signal(str)
    progress = Signal(str)
    total_files = Signal(int)
    progress_batch = Signal(object)
    def __init__(self, target=None, update_signatures=False, update_only=False, scan_options=None, elevated=False):
        super().__init__()
        self.target = target
        self.update_signatures = update_signatures
        self.update_only = update_only
        self.scan_options = scan_options or {}
        self.elevated = elevated
        self._process = None
        self._process_lock = threading.Lock()
        self._cancelled = False

    def cancel(self):
        self._cancelled = True
        # Beim Systemscan läuft clamscan unter Root-Rechten hinter pkexec.
        # Deshalb exakt den vom Nutzer getesteten Befehl über pkexec ausführen.
        if self.elevated:
            pkexec = shutil.which("pkexec")
            pkill = shutil.which("pkill")
            if pkexec and pkill:
                try:
                    cancel_proc = subprocess.Popen(
                        [pkexec, pkill, "-TERM", "-x", "clamscan"],
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True,
                    )
                    self._cancel_helper_process = cancel_proc
                    threading.Thread(
                        target=lambda: cancel_proc.wait(),
                        name="LunaSecurity-ClamAV-Cancel",
                        daemon=True,
                    ).start()
                except OSError:
                    pass
        with self._process_lock:
            proc = self._process
        if proc and proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except OSError:
                pass

    def _run_process(self, args, timeout):
        if self._cancelled or self.isInterruptionRequested():
            raise InterruptedError("Scan abgebrochen.")
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                bufsize=1, start_new_session=True)
        with self._process_lock:
            self._process = proc
        started = time.monotonic()
        output = []
        batch = []
        last_emit = time.monotonic()
        try:
            # Ausgabe puffern: ein Signal pro Block statt eines Qt-Signals je Zeile.
            # Das verhindert GUI-Staus bei sehr ausführlichen /sys-Scans.
            while True:
                if self._cancelled or self.isInterruptionRequested():
                    try: os.killpg(proc.pid, signal.SIGTERM)
                    except OSError: pass
                    try: proc.wait(timeout=4)
                    except subprocess.TimeoutExpired:
                        try: os.killpg(proc.pid, signal.SIGKILL)
                        except OSError: pass
                        proc.wait()
                    raise InterruptedError("Scan vom Benutzer abgebrochen.")
                if time.monotonic() - started > timeout:
                    proc.kill(); proc.wait()
                    raise TimeoutError("Zeitüberschreitung beim Scan.")
                line = proc.stdout.readline()
                if line:
                    line = line.rstrip("\r\n")
                    output.append(line)
                    if line:
                        batch.append(line)
                    now = time.monotonic()
                    if len(batch) >= 100 or (batch and now - last_emit >= 0.15):
                        self.progress_batch.emit(batch)
                        batch = []
                        last_emit = now
                elif proc.poll() is not None:
                    break
                else:
                    if batch and time.monotonic() - last_emit >= 0.15:
                        self.progress_batch.emit(batch)
                        batch = []
                        last_emit = time.monotonic()
                    time.sleep(0.025)
            if batch:
                self.progress_batch.emit(batch)
            return subprocess.CompletedProcess(args, proc.returncode, "\n".join(output), "")
        finally:
            try: proc.stdout.close()
            except Exception: pass
            with self._process_lock:
                self._process = None

    def run(self):
        messages = []
        if self.update_signatures or self.update_only:
            old_versions = signature_database_versions()
            messages.append("Installierte Signaturen vorher: " + old_versions)
            updater = shutil.which("freshclam")
            if not updater:
                self.result.emit("freshclam ist nicht installiert. Installiere clamav-freshclam.")
                return
            try:
                # Debian commonly runs freshclam as a daemon. Do not start a
                # competing updater while that service owns the database lock.
                systemctl = shutil.which("systemctl")
                if systemctl:
                    service = subprocess.run([systemctl, "is-active", "--quiet", "clamav-freshclam"],
                                             capture_output=True, timeout=10)
                    if service.returncode == 0:
                        messages.append("Der Dienst clamav-freshclam läuft bereits. Er aktualisiert die Signaturen selbst; ein paralleler manueller Aufruf wurde vermieden.")
                        if self.update_only:
                            self.result.emit("\n\n".join(messages))
                            return
                        # Continue with the scan using the currently installed signatures.
                        update = None
                    else:
                        update = None
                else:
                    update = None
                if update is None and not (systemctl and service.returncode == 0):
                    pkexec = shutil.which("pkexec")
                    if not pkexec:
                        self.result.emit("\n\n".join(messages + ["Für die Signaturaktualisierung werden Administratorrechte benötigt. Installiere policykit-1, damit LunaSecurity pkexec mit Passwortabfrage verwenden kann."]))
                        return
                    update = self._run_process([pkexec, updater], timeout=1800)
                if update is None:
                    update_text = "Aktualisierung wird durch den laufenden ClamAV-Dienst verwaltet."
                    update_returncode = 0
                else:
                    update_text = (update.stdout + "\n" + update.stderr).strip()
                    update_returncode = update.returncode
                messages.append("Signaturaktualisierung:\n" + (update_text or f"freshclam beendet (Exit-Code {update.returncode})."))
                new_versions = signature_database_versions()
                messages.append("Installierte Signaturen danach: " + new_versions)
                if update_returncode == 0 and new_versions == old_versions:
                    messages.append("Die Signaturversion ist unverändert (Datenbank war möglicherweise bereits aktuell).")
                elif update_returncode == 0 and new_versions != old_versions:
                    messages.append("Die neue Signaturversion wurde übernommen.")
                if update_returncode != 0:
                    messages.append("Die Signaturen konnten nicht aktualisiert werden. Prüfe die Berechtigungen oder ob bereits der freshclam-Dienst läuft.")
                    if self.update_only:
                        self.result.emit("\n\n".join(messages))
                        return
            except Exception as exc:
                self.result.emit(f"freshclam konnte nicht ausgeführt werden: {exc}")
                return

        if self.update_only:
            self.result.emit("\n\n".join(messages) or "Signaturaktualisierung abgeschlossen.")
            return

        scanner = shutil.which("clamscan")
        if not scanner:
            self.result.emit("\n\n".join(messages + ["ClamAV ist nicht installiert. Installiere clamav."]))
            return
        file_list_path = None
        try:
            args = [scanner, "--verbose", "--infected", "--no-summary",
                    "--detect-pua=" + ("yes" if self.scan_options.get("detect_pua", False) else "no"),
                    "--heuristic-alerts=" + ("yes" if self.scan_options.get("heuristics", True) else "no"),
                    "--alert-exceeds-max=yes"]
            include_large = self.scan_options.get("large_files", False)
            args += ["--max-filesize=" + ("2G" if include_large else "20M"),
                     "--max-scansize=" + ("2G" if include_large else "400M")]
            raw_targets = self.target if isinstance(self.target, (list, tuple, set)) else [self.target]
            target_paths = [Path(item) for item in raw_targets]
            include_hidden = self.scan_options.get("hidden_files", False)
            recursive = self.scan_options.get("recursive", True)
            if self.elevated:
                # Systemverzeichnisse direkt an clamscan übergeben. Die Dateisuche
                # erfolgt dann mit Root-Rechten und scheitert nicht an /etc-Rechten.
                pkexec = shutil.which("pkexec")
                if not pkexec:
                    self.result.emit("\\n\\n".join(messages + ["Systemscan benötigt pkexec (Paket policykit-1)."]))
                    return
                existing_targets = [str(p) for p in target_paths if p.exists() and not p.is_symlink()]
                if not existing_targets:
                    self.result.emit("\\n\\n".join(messages + ["Keine erreichbaren Systemverzeichnisse gefunden."]))
                    return
                args.append("--recursive=yes" if recursive else "--recursive=no")
                if not include_hidden:
                    # ClamAV läuft hier mit Root-Rechten direkt über Verzeichnisse.
                    # Deshalb müssen versteckte Dateien und Verzeichnisse auch dort
                    # explizit ausgeschlossen werden (nicht nur beim Python-Dateilisten-Scan).
                    args.append(r"--exclude=(^|/)\\.[^/]+$")
                    args.append(r"--exclude-dir=(^|/)\\.[^/]+(/|$)")
                args.extend(existing_targets)
                messages.append("Systemscan mit Administratorrechten; geprüfte Verzeichnisse: " + ", ".join(existing_targets))
                helper = "/usr/lib/lunasecurity/clamav-scan-helper"
                if not os.path.isfile(helper):
                    helper = str(Path(__file__).resolve().parent.parent / "scripts" / "clamav-scan-helper")
                p = self._run_process([pkexec, helper, "scan"] + args[1:], timeout=86400)
                output = (p.stdout + "\\n" + p.stderr).strip()
                messages.append(output or f"Systemscan beendet (Exit-Code {p.returncode}).")
                self.result.emit("\\n\\n".join(messages))
                return
            candidates = []
            for target_path in target_paths:
                if target_path.is_dir():
                    if recursive:
                        for current, dirs, files in os.walk(target_path, followlinks=False):
                            if self._cancelled or self.isInterruptionRequested():
                                raise InterruptedError("Scan vom Benutzer abgebrochen.")
                            dirs[:] = [d for d in dirs if not (Path(current) / d).is_symlink()]
                            if not include_hidden:
                                dirs[:] = [d for d in dirs if not d.startswith(".")]
                            for name in files:
                                if self._cancelled or self.isInterruptionRequested():
                                    raise InterruptedError("Scan vom Benutzer abgebrochen.")
                                candidate = Path(current) / name
                                if candidate.is_file() and not candidate.is_symlink() and (include_hidden or not name.startswith(".")):
                                    candidates.append(str(candidate))
                    else:
                        for entry in target_path.iterdir():
                            if self._cancelled or self.isInterruptionRequested():
                                raise InterruptedError("Scan vom Benutzer abgebrochen.")
                            if entry.is_file() and not entry.is_symlink() and (include_hidden or not entry.name.startswith(".")):
                                candidates.append(str(entry))
                elif target_path.is_file() and not target_path.is_symlink():
                    if include_hidden or not target_path.name.startswith("."):
                        candidates.append(str(target_path))
            candidates = list(dict.fromkeys(candidates))
            if not candidates:
                self.total_files.emit(0)
                self.result.emit("\n\n".join(messages + ["Keine Dateien passend zu den gewählten Scanoptionen gefunden."]))
                return
            # Die Dateiliste ist exakt dieselbe Liste, die clamscan anschließend prüft.
            self.total_files.emit(len(candidates))
            handle = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False,
                                                 prefix="lunasecurity-scan-", suffix=".list")
            file_list_path = handle.name
            try:
                handle.write("\n".join(candidates) + "\n")
            finally:
                handle.close()
            args.append("--file-list=" + file_list_path)
            messages.append(f"Scanumfang: {len(candidates)} Dateien; geprüfte Verzeichnisse: {len(target_paths)}; Unterordner: {'ja' if recursive else 'nein'}; versteckte Dateien: {'ja' if include_hidden else 'nein'}.")
            p = self._run_process(args, timeout=86400)
            output = (p.stdout + "\n" + p.stderr).strip()
            messages.append(output or f"Scan beendet (Exit-Code {p.returncode}).")
            self.result.emit("\n\n".join(messages))
        except InterruptedError:
            self.result.emit("Scan wurde vom Benutzer abgebrochen.")
        except Exception as exc:
            self.result.emit(f"Scan konnte nicht ausgeführt werden: {exc}")
        finally:
            if file_list_path:
                try:
                    os.unlink(file_list_path)
                except OSError:
                    pass


class PackageVerifyWorker(QThread):
    """Prüft Paketdateien im Hintergrund und ordnet Abweichungen lokal zu."""
    completed = Signal(str, object, str)
    status = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._process = None
        self._cancel_requested = False
        self._process_lock = threading.Lock()

    def cancel(self):
        self._cancel_requested = True
        with self._process_lock:
            proc = self._process
        if proc is not None and proc.poll() is None:
            self._terminate_process_group(proc)

    @staticmethod
    def _terminate_process_group(proc):
        if proc.poll() is not None: return
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            try: proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait(timeout=3)
        except (OSError, subprocess.TimeoutExpired):
            try: proc.kill(); proc.wait(timeout=2)
            except Exception: pass

    def run(self):
        dpkg = shutil.which("dpkg")
        if not dpkg:
            self.completed.emit("", {}, "dpkg wurde nicht gefunden.")
            return
        try:
            self.status.emit("dpkg prüft die installierten Paketdateien …")
            proc = subprocess.Popen([dpkg, "--verify"], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True, bufsize=1,
                                    start_new_session=True)
            with self._process_lock:
                self._process = proc
            while True:
                try:
                    stdout, stderr = proc.communicate(timeout=0.25)
                    break
                except subprocess.TimeoutExpired:
                    if self._cancel_requested:
                        self._terminate_process_group(proc)
                        stdout, stderr = proc.communicate()
                        break
            if self._cancel_requested:
                self.completed.emit("", {}, "Paketprüfung wurde auf deinen Wunsch abgebrochen. Es wurden keine Dateien verändert.")
                return
            output = (stdout + "\n" + stderr).strip()
            paths = []
            seen = set()
            for line in stdout.splitlines():
                parts = line.split()
                if parts:
                    candidate = parts[-1]
                    if candidate.startswith("/") and candidate not in seen:
                        seen.add(candidate)
                        paths.append(candidate)

            packages = {}
            if paths:
                self.status.emit(f"{len(paths)} Abweichung(en) gefunden – Paketzuordnung wird einmalig aus der dpkg-Dateiliste aufgebaut …")
                # Einmaliger Index aus /var/lib/dpkg/info/*.list statt eines dpkg-query-Aufrufs pro Fund.
                ownership = {}
                info_dir = Path("/var/lib/dpkg/info")
                for list_file in info_dir.glob("*.list"):
                    if self._cancel_requested:
                        self.completed.emit("", {}, "Paketprüfung wurde auf deinen Wunsch abgebrochen. Es wurden keine Dateien verändert.")
                        return
                    filename = list_file.name[:-5]
                    package = filename
                    # Multiarch-Paketnamen wie libc6:arm64.list bleiben erhalten.
                    try:
                        with list_file.open("r", encoding="utf-8", errors="replace") as handle:
                            for entry in handle:
                                entry = entry.rstrip("\n")
                                if entry.startswith("/"):
                                    ownership[entry] = package
                    except OSError:
                        continue
                for path in paths:
                    pkg = ownership.get(path)
                    if pkg:
                        packages[pkg] = packages.get(pkg, 0) + 1
            if self._process.returncode not in (0, 1):
                self.completed.emit(output, packages, f"dpkg --verify endete mit Exit-Code {self._process.returncode}.")
            else:
                self.completed.emit(output, packages, "")
        except (OSError, subprocess.SubprocessError) as exc:
            self.completed.emit("", {}, f"Paketprüfung fehlgeschlagen: {exc}")
        finally:
            with self._process_lock:
                self._process = None



class DashboardIcon(QWidget):
    """Kompakte, farbige Vektor-Symbole für die Dashboard-Kategorien."""
    def __init__(self, kind, accent, parent=None):
        super().__init__(parent)
        self.kind = kind
        self.accent = QColor(accent)
        self.setFixedSize(46, 46)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.scale(self.width() / 48.0, self.height() / 48.0)
        glow = QColor(self.accent); glow.setAlpha(55)
        pen = QPen(glow, 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
        self._draw_symbol(p)
        pen = QPen(self.accent, 2.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
        self._draw_symbol(p)
        p.end()

    def _draw_symbol(self, p):
        path = QPainterPath()
        if self.kind == "shield":
            path.moveTo(24, 4); path.lineTo(41, 11); path.lineTo(39, 28)
            path.quadTo(37, 39, 24, 45); path.quadTo(11, 39, 9, 28)
            path.lineTo(7, 11); path.closeSubpath()
            p.drawPath(path)
            check = QPainterPath(); check.moveTo(15, 24); check.lineTo(21, 30); check.lineTo(33, 17)
            p.drawPath(check)
        elif self.kind == "layers":
            p.drawPolygon(QPolygon([QPoint(24, 5), QPoint(43, 15), QPoint(24, 25), QPoint(5, 15)]))
            p.drawPolyline(QPolygon([QPoint(7, 24), QPoint(24, 34), QPoint(41, 24)]))
            p.drawPolyline(QPolygon([QPoint(7, 32), QPoint(24, 42), QPoint(41, 32)]))
        elif self.kind == "wifi":
            p.drawArc(QRectF(5, 7, 38, 34), 35 * 16, 110 * 16)
            p.drawArc(QRectF(12, 16, 24, 23), 35 * 16, 110 * 16)
            p.drawArc(QRectF(19, 25, 10, 13), 35 * 16, 110 * 16)
            p.setBrush(self.accent); p.drawEllipse(QRectF(21, 39, 6, 6))
        elif self.kind == "monitor":
            p.drawRoundedRect(QRectF(5, 5, 38, 27), 3, 3)
            pulse = QPainterPath(); pulse.moveTo(9, 19); pulse.lineTo(17, 19)
            pulse.lineTo(21, 12); pulse.lineTo(26, 25); pulse.lineTo(30, 16); pulse.lineTo(33, 19); pulse.lineTo(39, 19)
            p.drawPath(pulse)
            p.drawLine(24, 32, 24, 39); p.drawLine(16, 42, 32, 42)


class MoonArtwork(QWidget):
    """Leichte, skalierbare Mondlandschaft für die linke LunaSecurity-Navigation."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(150)
        self.setMaximumHeight(190)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        # Sanfter violetter Horizont
        glow = QRadialGradient(w * .52, h * .58, h * .78)
        glow.setColorAt(0.0, QColor(104, 55, 211, 105))
        glow.setColorAt(1.0, QColor(15, 18, 43, 0))
        p.fillRect(self.rect(), glow)
        # Mondschein
        d = min(w * .43, h * .62)
        cx, cy = w * .53, h * .43
        moon = QRadialGradient(cx - d*.16, cy - d*.18, d*.72)
        moon.setColorAt(0.0, QColor(255, 250, 255))
        moon.setColorAt(.42, QColor(220, 195, 255))
        moon.setColorAt(.78, QColor(151, 105, 238))
        moon.setColorAt(1.0, QColor(103, 62, 191))
        p.setPen(QPen(QColor(224, 198, 255, 210), 1.4))
        p.setBrush(QBrush(moon))
        p.drawEllipse(int(cx-d/2), int(cy-d/2), int(d), int(d))
        # dezente Mondkrater
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(112, 76, 177, 55))
        for x, y, r in [(-.18,-.10,.10),(.12,-.20,.07),(.20,.08,.11),(-.12,.20,.06)]:
            p.drawEllipse(int(cx+x*d-r*d/2), int(cy+y*d-r*d/2), int(d*r), int(d*r))
        # Mehrere Bergsilhouetten
        def ridge(points, color):
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(color))
            poly = QPolygon([QPoint(int(x*w), int(y*h)) for x,y in points] +
                             [QPoint(w, h), QPoint(0, h)])
            p.drawPolygon(poly)
        ridge([(0,.73),(.13,.61),(.23,.72),(.37,.57),(.52,.73),(.67,.60),(.82,.72),(.94,.62),(1,.70)],
              "#30205f")
        ridge([(0,.83),(.18,.69),(.31,.82),(.49,.68),(.64,.84),(.82,.70),(1,.82)],
              "#1c1744")
        ridge([(0,.92),(.20,.81),(.36,.90),(.55,.79),(.74,.91),(.90,.81),(1,.89)],
              "#11152f")
        # Lichtspur am unteren Rand
        grad = QLinearGradient(0, h*.84, 0, h)
        grad.setColorAt(0, QColor(162, 105, 255, 0))
        grad.setColorAt(1, QColor(130, 76, 255, 90))
        p.fillRect(0, int(h*.84), w, int(h*.16), grad)
        p.end()


def _ui_text(value):
    """Übersetzt auch Texte in zur Laufzeit erzeugten Dialogen und Statusmeldungen."""
    value = str(value)
    if APP_LANGUAGE != "en":
        return value
    translated = EN_TRANSLATIONS.get(value)
    if translated is not None:
        return translated
    # Häufige dynamische Meldungen und zusammengesetzte Statuszeilen.
    replacements = (
        ("fail2ban-Überwachung", "fail2ban monitoring"),
        (" läuft", " running"),
        (" gestartet.", " started."),
        (" beendet.", " finished."),
        ("fail2ban-Verbindung:", "fail2ban connection:"),
        ("Gesamtstatus:", "Overall status:"),
        ("SSH-Jail:", "SSH jail:"),
        ("Prüfung abgeschlossen", "Check completed"),
        ("Prüfung abgebrochen", "Check cancelled"),
        ("Prüfung wird vorbereitet …", "Preparing check …"),
        ("Prüfung läuft …", "Check running …"),
        ("Prüfung abbrechen", "Cancel check"),
        ("Abbruch läuft …", "Cancelling …"),
        ("Die Prüfung wird abgebrochen …", "Cancelling the check …"),
        ("Ergebnis kopieren", "Copy result"),
        ("Ausgaben der laufenden Prüfung erscheinen hier.", "Output from the running check will appear here."),
        ("Was möchtest du scannen?", "What would you like to scan?"),
        ("Datei zum Scannen auswählen", "Select file to scan"),
        ("Ordner zum Scannen auswählen", "Select folder to scan"),
        ("Dateiauswahl abgebrochen; kein Scan gestartet.", "File selection cancelled; no scan started."),
        ("Ordnerauswahl abgebrochen; kein Scan gestartet.", "Folder selection cancelled; no scan started."),
        ("Scan abgebrochen; kein Scan-Ziel ausgewählt.", "Scan cancelled; no scan target selected."),
        ("fail2ban-client ist nicht installiert.", "fail2ban-client is not installed."),
        ("Für die fail2ban-Statusabfrage wird pkexec benötigt (policykit-1).", "pkexec (policykit-1) is required to query fail2ban status."),
        ("Der LunaSecurity-Helfer für fail2ban fehlt.", "The LunaSecurity fail2ban helper is missing."),
    )
    for source, target in replacements:
        value = value.replace(source, target)
    return value


class ModuleProgressDialog(QDialog):
    """Fortschrittsfenster für Sicherheitsprüfungen außerhalb von ClamAV."""
    def __init__(self, title, cancel_callback, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_ui_text(f"LunaSecurity – {title}"))
        self.setMinimumSize(700, 480)
        self.resize(860, 600)
        self.setModal(False)
        self._finished = False
        self.setStyleSheet(parent.styleSheet() if parent else "")
        layout = QVBoxLayout(self)
        heading = QLabel(_ui_text(f"{title} läuft"))
        heading.setStyleSheet("font-size:17pt;font-weight:800")
        layout.addWidget(heading)
        self.status = QLabel(_ui_text("Prüfung wird vorbereitet …"))
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.bar = QProgressBar()
        self.bar.setRange(0, 0)
        self.bar.setFormat(_ui_text("Prüfung läuft …"))
        layout.addWidget(self.bar)
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.output.document().setMaximumBlockCount(10000)
        self.output.setPlaceholderText(_ui_text("Ausgaben der laufenden Prüfung erscheinen hier."))
        layout.addWidget(self.output, 1)
        buttons = QHBoxLayout()
        self.cancel_button = QPushButton(_ui_text("Prüfung abbrechen"))
        self.cancel_button.clicked.connect(self._cancel)
        self._cancel_callback = cancel_callback
        buttons.addWidget(self.cancel_button)
        self.copy_button = QPushButton(_ui_text("Ergebnis kopieren"))
        self.copy_button.clicked.connect(lambda: QApplication.clipboard().setText(self.output.toPlainText()))
        buttons.addWidget(self.copy_button)
        buttons.addStretch(1)
        self.close_button = QPushButton(_ui_text("Schließen"))
        self.close_button.setEnabled(False)
        self.close_button.clicked.connect(self.accept)
        buttons.addWidget(self.close_button)
        layout.addLayout(buttons)

    def _cancel(self):
        self.cancel_button.setEnabled(False)
        self.cancel_button.setText(_ui_text("Abbruch läuft …"))
        self.status.setText(_ui_text("Die Prüfung wird abgebrochen …"))
        self._cancel_callback()

    def append_output(self, line):
        if line:
            self.output.append(_ui_text(line))
            self.status.setText(_ui_text(line)[:500])

    def finish(self, title, result):
        self._finished = True
        result = str(result or "")
        if result.strip():
            self.output.setPlainText(_ui_text(result))
            self.output.moveCursor(QTextCursor.MoveOperation.Start)
        cancelled = any(token in result.lower() for token in ("abgebrochen", "abbruch", "cancelled"))
        self.status.setText(_ui_text("Prüfung abgebrochen" if cancelled else "Prüfung abgeschlossen"))
        self.bar.setRange(0, 1)
        self.bar.setValue(0 if cancelled else 1)
        self.bar.setFormat(_ui_text("Abgebrochen") if cancelled else "100 %")
        self.cancel_button.setEnabled(False)
        self.close_button.setEnabled(True)

    def closeEvent(self, event):
        if not self._finished:
            event.ignore()
            return
        super().closeEvent(event)


class ClamScanMonitor(QDialog):
    """Einheitliche Live-Ansicht für sämtliche ClamAV-Scans."""
    def __init__(self, target, parent=None, cancel_callback=None, ignore_max_filesize=True):
        super().__init__(parent)
        self.ignore_max_filesize = bool(ignore_max_filesize)
        self.cancel_callback = cancel_callback
        self.setWindowTitle(_ui_text("LunaSecurity – ClamAV-Systemprüfung"))
        self.setMinimumSize(760, 560)
        self.setModal(False)
        self.started = time.monotonic()
        self.checked = 0
        self.total_files = 0
        self._checked_paths = set()
        self.threats = 0
        self.size_limit_count = 0
        self.unreadable = 0
        self.skipped = 0
        self._current_scan_path = ""
        self._unreadable_paths = set()
        self._skipped_paths = set()
        self._unreadable_fallback = set()
        self._skipped_fallback = set()
        root = QVBoxLayout(self)
        head = QHBoxLayout()
        title = QLabel(_ui_text("ClamAV-Scan läuft"))
        title.setStyleSheet("font-size:19pt;font-weight:800")
        self.state = QLabel(_ui_text("● Aktiv"))
        self.state.setStyleSheet("color:#35d46a;font-weight:700")
        head.addWidget(title); head.addStretch(1); head.addWidget(self.state)
        root.addLayout(head)
        self.target_label = QLabel(_ui_text("Scanbereich:") + f" {target}")
        self.target_label.setWordWrap(True)
        root.addWidget(self.target_label)
        self.note = QLabel(_ui_text("Root-Rechte werden nur für geschützte Systembereiche benötigt."))
        self.note.setObjectName("muted")
        root.addWidget(self.note)
        self.bar = QProgressBar(); self.bar.setRange(0, 0)
        root.addWidget(self.bar)
        stats = QHBoxLayout()
        self.checked_label = QLabel("0\n" + _ui_text("Geprüfte Dateien"))
        self.threat_label = QLabel("0\n" + _ui_text("Bedrohungen"))
        self.size_limit_label = QLabel("0\n" + _ui_text("Größenlimit"))
        self.unreadable_label = QLabel("0\n" + _ui_text("Nicht lesbar"))
        self.skipped_label = QLabel("0\n" + _ui_text("Übersprungen"))
        for label in (self.checked_label, self.threat_label, self.size_limit_label, self.unreadable_label, self.skipped_label):
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("QLabel{background:#292b3b;border:1px solid #555875;border-radius:9px;padding:12px;font-size:12pt;font-weight:700}")
            stats.addWidget(label)
        root.addLayout(stats)
        self.current = QLabel(_ui_text("Aktuelle Datei: wird vorbereitet …"))
        self.current.setWordWrap(True)
        root.addWidget(self.current)
        log_title = QLabel(_ui_text("Scan-Protokoll"))
        log_title.setStyleSheet("font-size:13pt;font-weight:700")
        root.addWidget(log_title)
        self.log = QTextEdit(); self.log.setReadOnly(True)
        self.log.document().setMaximumBlockCount(5000)
        root.addWidget(self.log, 1)
        self.elapsed = QLabel(_ui_text("Verstrichene Zeit:") + " 00:00")
        root.addWidget(self.elapsed)
        actions = QHBoxLayout()
        self.actions_layout = actions
        self.cancel_button = QPushButton(_ui_text("Scan abbrechen"))
        self.cancel_button.clicked.connect(self.cancel_scan)
        actions.addWidget(self.cancel_button)
        self.copy_button = QPushButton(_ui_text("Scan-Ergebnis kopieren"))
        self.copy_button.clicked.connect(self.copy_result)
        actions.addWidget(self.copy_button)
        actions.addStretch(1)
        # Der Button existiert von Anfang an im Layout, ist aber während
        # des Scans vollständig verborgen. Im Abschluss-Slot wird er eingeblendet.
        self.close_button = QPushButton(_ui_text("Schließen"))
        self.close_button.setMinimumWidth(108)
        self.close_button.setEnabled(False)
        self.close_button.setStyleSheet(
            "QPushButton { background-color:#2860df; color:white; "
            "border:1px solid #5685ff; border-radius:8px; "
            "padding:10px 22px; font-weight:700; }"
            "QPushButton:hover { background-color:#3974f2; }"
            "QPushButton:pressed { background-color:#1e49b8; }"
            "QPushButton:disabled { background-color:#3b465f; color:#9aa3b8; "
            "border:1px solid #56617a; }"
        )
        self.close_button.clicked.connect(self.accept)
        self.close_button.show()
        actions.addWidget(self.close_button)
        root.addLayout(actions)
        self.clock = QTimer(self); self.clock.setInterval(1000)
        self.clock.timeout.connect(self.update_elapsed); self.clock.start()

    def set_total_files(self, total):
        self.total_files = max(0, int(total))
        if self.total_files > 0:
            self.bar.setRange(0, self.total_files)
            self.bar.setValue(min(self.checked, self.total_files))
            self.bar.setFormat("%p%")
        else:
            self.bar.setRange(0, 0)
            self.bar.setFormat(_ui_text("Scan läuft …"))

    def update_elapsed(self):
        seconds = int(time.monotonic() - self.started)
        self.elapsed.setText(_ui_text("Verstrichene Zeit:") + f" {seconds//3600:02d}:{(seconds//60)%60:02d}:{seconds%60:02d}")

    def add_line(self, line):
        """Kompatibler Einzelzeilen-Einstieg; produktiv kommen Zeilen blockweise."""
        self.add_lines([line])

    def add_lines(self, lines):
        """Wertet einen Ausgabeblock aus und aktualisiert die Oberfläche nur einmal."""
        cleaned = []
        for raw in lines or []:
            text = str(raw).strip()
            if not text:
                continue
            cleaned.append(text)
            upper = text.upper()
            if (self.ignore_max_filesize and "HEURISTICS.LIMITS.EXCEEDED.MAXFILESIZE" in upper
                    and (upper.endswith("FOUND") or " FOUND " in upper)):
                cleaned.append("  → Nicht vollständig geprüft (ClamAV-Dateigrößenlimit überschritten; kein Malware-Fund).")
            if upper.startswith("SCANNING "):
                self._current_scan_path = text[9:].strip()
                if self._current_scan_path not in self._checked_paths:
                    self._checked_paths.add(self._current_scan_path)
                    self.checked += 1
            elif upper.endswith(": OK") or "\tOK" in upper:
                # OK-Zeilen nur ergänzend zählen, falls kein SCANNING-Pfad kam.
                result_path = text.rsplit(":", 1)[0].strip()
                if result_path and result_path not in self._checked_paths:
                    self._checked_paths.add(result_path)
                    self.checked += 1
            is_max_filesize = "HEURISTICS.LIMITS.EXCEEDED.MAXFILESIZE" in upper
            if is_max_filesize:
                self.size_limit_count += 1
                if not self.ignore_max_filesize:
                    self.threats += 1
            elif " FOUND" in upper or "INFECTED" in upper:
                self.threats += 1

            path = self._current_scan_path
            is_read_error = any(token in upper for token in (
                "FMAP_READPAGE: PREAD FAIL", "FMAP_READPAGE: PREAD ERROR",
                "ACCESS DENIED", "PERMISSION DENIED", "CAN'T OPEN",
                "CANNOT OPEN", "FAILED TO OPEN", "INPUT/OUTPUT ERROR", "I/O ERROR"
            ))
            if is_read_error:
                key = path or upper
                if key not in self._unreadable_paths and key not in self._unreadable_fallback:
                    if path:
                        self._unreadable_paths.add(key)
                    else:
                        self._unreadable_fallback.add(key)
                    self.unreadable += 1

            # Übersprungen ist eine eigene ClamAV-Aussage, kein Synonym für Lesefehler.
            is_skipped = any(token in upper for token in (
                "SKIPPING ", "SKIPPED", "EXCLUDED", "WILL NOT BE SCANNED"
            ))
            if is_skipped:
                key = path or upper
                if key not in self._skipped_paths and key not in self._skipped_fallback:
                    if path:
                        self._skipped_paths.add(key)
                    else:
                        self._skipped_fallback.add(key)
                    self.skipped += 1

        if not cleaned:
            return
        self.log.setUpdatesEnabled(False)
        try:
            self.log.moveCursor(QTextCursor.MoveOperation.End)
            self.log.insertPlainText("\n".join(cleaned) + "\n")
        finally:
            self.log.setUpdatesEnabled(True)
        self.current.setText(_ui_text("Aktuelle Datei:") + " " + (self._current_scan_path or cleaned[-1])[:500])
        self.checked_label.setText(f"{self.checked:,}\n" + _ui_text("Geprüfte Dateien").replace(",", "."))
        if self.total_files > 0:
            self.bar.setValue(min(self.checked, self.total_files))
        self.threat_label.setText(f"{self.threats}\n" + _ui_text("Bedrohungen"))
        self.size_limit_label.setText(f"{self.size_limit_count}\n" + _ui_text("Größenlimit"))
        self.unreadable_label.setText(f"{self.unreadable}\n" + _ui_text("Nicht lesbar"))
        self.skipped_label.setText(f"{self.skipped}\n" + _ui_text("Übersprungen"))

    def cancel_scan(self):
        if self.cancel_callback:
            self.cancel_button.setEnabled(False)
            self.cancel_button.setText(_ui_text("Abbruch läuft …"))
            self.note.setText(_ui_text("Der Scan wird abgebrochen …"))
            self.cancel_callback()
            # Sofort die Schließen-Aktion anbieten; der Worker beendet parallel ClamAV.
            self._replace_close_button()

    def copy_result(self):
        QApplication.clipboard().setText(self.log.toPlainText())

    def _replace_close_button(self):
        # Kompatibler Name; der Button ist bereits im Layout und wird nur gezeigt.
        self.cancel_button.setEnabled(False)
        self.cancel_button.setText(_ui_text("Scan abbrechen"))
        self.close_button.setEnabled(True)
        self.close_button.setVisible(True)
        self.close_button.show()
        self.close_button.raise_()
        self.close_button.update()
        self.close_button.repaint()

    def finish(self, result):
        self.clock.stop()
        cancelled = (
            "benutzer abgebrochen" in str(result).lower()
            or "exit-code -15" in str(result).lower()
            or "abbruch" in str(result).lower()
        )
        self.bar.setRange(0, 1)
        self.bar.setValue(0 if cancelled else 1)
        self.bar.setFormat(_ui_text("Abgebrochen") if cancelled else "100 %")
        self.state.setText("● " + (_ui_text("Abgebrochen") if cancelled else _ui_text("Abgeschlossen")))
        # This is the authoritative terminal-state command. Reveal the close
        # button immediately here, rather than waiting for later report/log work.
        self._replace_close_button()
        self.state.setStyleSheet("color:#35d46a;font-weight:700")
        self.note.setText(
            _ui_text("Scan abgebrochen. Das bisherige Ergebnis steht im Scan-Protokoll.")
            if cancelled else
            _ui_text("Scan abgeschlossen. Das vollständige Ergebnis steht im Scan-Protokoll.")
        )
        if result:
            # Nur kompakte Status-/Zusammenfassungszeilen ergänzen. Die vollständige
            # Ausgabe wurde vom Worker verarbeitet und darf nicht nochmals als ein
            # riesiger QTextEdit-Block in die GUI kopiert werden.
            summary_lines = []
            for raw in str(result).splitlines():
                line = raw.strip()
                if line.startswith(("Scanumfang:", "Systemscan mit Administratorrechten", "Scanned files:",
                                    "Infected files:", "Data scanned:", "Time:", "Scan beendet", "Systemscan beendet")):
                    summary_lines.append(line)
            if summary_lines:
                self.log.append("\n" + "\n".join(summary_lines[-20:]))
            # Am Ende des Scanfensters die vollständigen Fundpfade gesammelt
            # anzeigen – parallel zur Fundliste im Haupt-Protokollfeld.
            found_items = []
            for raw in str(result).splitlines():
                line = raw.strip()
                if line.endswith("FOUND") or " FOUND " in line:
                    if (self.ignore_max_filesize
                            and "HEURISTICS.LIMITS.EXCEEDED.MAXFILESIZE" in line.upper()):
                        continue
                    found_path = sec.detection_path(line)
                    detection_type = _clamav_detection_type(line)
                    item = (found_path, detection_type)
                    if found_path and item not in found_items:
                        found_items.append(item)
            if found_items:
                self.log.append("\\nGefundene Datei(en):")
                for found_path, detection_type in found_items:
                    self.log.append("Datei: " + found_path)
                    if detection_type:
                        self.log.append("Art der Bedrohung: " + detection_type)

            summary = re.search(r"Scanned files:\s*(\d+)", str(result), re.IGNORECASE)
            if summary:
                self.checked = int(summary.group(1))
                self.checked_label.setText(f"{self.checked:,}\nGeprüfte Dateien".replace(",", "."))
        self._replace_close_button()
        # Normaler Abschluss: Sichtbarkeit nach dem Qt-Signal nochmals anwenden.
        QTimer.singleShot(0, self._replace_close_button)
        QTimer.singleShot(150, self._replace_close_button)



class VirusTotalLookupWorker(QThread):
    finished_report = Signal(object)

    def __init__(self, file_path, api_key, parent=None, upload_unknown=False):
        super().__init__(parent)
        self.file_path = str(file_path)
        self.api_key = api_key
        self.upload_unknown = bool(upload_unknown)

    def _request_json(self, url, method="GET", data=None, headers=None, timeout=35):
        request_headers = {"x-apikey": self.api_key, "Accept": "application/json"}
        if headers:
            request_headers.update(headers)
        request = urllib.request.Request(url, data=data, headers=request_headers, method=method)
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
        return json.loads(raw.decode("utf-8")) if raw else {}

    def _upload_file(self, file_hash):
        size = os.path.getsize(self.file_path)
        if size > 32 * 1024 * 1024:
            raise ValueError(
                "Diese Datei ist größer als 32 MB. Der einfache Upload ist deshalb nicht möglich. "
                "Bitte wähle eine kleinere Datei."
            )
        boundary = "----LunaSecurityVirusTotalBoundary7MA4YWxk"
        filename = os.path.basename(self.file_path).replace('"', '_')
        with open(self.file_path, "rb") as stream:
            content = stream.read()
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            "Content-Type: application/octet-stream\r\n\r\n"
        ).encode("utf-8") + content + f"\r\n--{boundary}--\r\n".encode("ascii")
        payload = self._request_json(
            "https://www.virustotal.com/api/v3/files",
            method="POST", data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            timeout=120,
        )
        analysis_id = payload.get("data", {}).get("id")
        if not analysis_id:
            raise RuntimeError("VirusTotal hat keine Analyse-ID zurückgegeben.")
        analysis_url = "https://www.virustotal.com/api/v3/analyses/" + urllib.parse.quote(analysis_id, safe="")
        # Analyse-Status in kurzen Abständen prüfen, ohne die Oberfläche zu blockieren.
        for _ in range(18):
            time.sleep(5)
            analysis = self._request_json(analysis_url, timeout=35)
            attrs = analysis.get("data", {}).get("attributes", {})
            if attrs.get("status") == "completed":
                break
        else:
            return {
                "status": "pending", "hash": file_hash, "path": self.file_path,
                "analysis_id": analysis_id,
                "analysis_url": f"https://www.virustotal.com/gui/file/{file_hash}",
            }
        # Nach abgeschlossener Analyse den vollständigen Datei-Bericht laden.
        return self._get_file_report(file_hash, self.file_path, uploaded=True)

    def _get_file_report(self, file_hash, file_path, uploaded=False):
        payload = self._request_json(f"https://www.virustotal.com/api/v3/files/{file_hash}")
        attrs = payload.get("data", {}).get("attributes", {})
        stats = attrs.get("last_analysis_stats", {})
        results = attrs.get("last_analysis_results", {}) or {}
        detections = []
        for vendor, item in results.items():
            category = str(item.get("category", "")).lower()
            if category in ("malicious", "suspicious"):
                detections.append({
                    "vendor": vendor,
                    "category": category,
                    "result": item.get("result") or "Keine Bezeichnung",
                })
        return {
            "status": "ok", "hash": file_hash, "path": file_path,
            "malicious": int(stats.get("malicious", 0)),
            "suspicious": int(stats.get("suspicious", 0)),
            "undetected": int(stats.get("undetected", 0)),
            "harmless": int(stats.get("harmless", 0)),
            "total": sum(int(v or 0) for v in stats.values()),
            "detections": detections[:30],
            "permalink": f"https://www.virustotal.com/gui/file/{file_hash}",
            "uploaded": uploaded,
        }

    def run(self):
        try:
            digest = hashlib.sha256()
            with open(self.file_path, "rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            file_hash = digest.hexdigest()
            try:
                result = self._get_file_report(file_hash, self.file_path)
                self.finished_report.emit(result)
                return
            except urllib.error.HTTPError as exc:
                if exc.code != 404:
                    raise
            if self.upload_unknown:
                self.finished_report.emit(self._upload_file(file_hash))
            else:
                self.finished_report.emit({
                    "status": "unknown", "hash": file_hash, "path": self.file_path,
                    "size": os.path.getsize(self.file_path),
                })
        except urllib.error.HTTPError as exc:
            if exc.code == 401:
                message = "VirusTotal hat den API-Schlüssel abgelehnt (HTTP 401)."
            elif exc.code == 403:
                message = "Der API-Schlüssel hat keine Berechtigung (HTTP 403)."
            elif exc.code == 429:
                message = "VirusTotal-Anfragelimit erreicht (HTTP 429). Bitte später erneut versuchen."
            else:
                message = f"VirusTotal meldet HTTP {exc.code}: {exc.reason}"
            self.finished_report.emit({"status": "error", "message": message})
        except Exception as exc:
            self.finished_report.emit({"status": "error", "message": f"VirusTotal-Prüfung fehlgeschlagen: {exc}"})


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LunaSecurity – Linux Security Suite")
        self.resize(1547, 900)  # Weitere 0,5 cm breiter; Version bleibt 0.4.33
        self.setMinimumSize(980, 680)
        self.bridge = Bridge()
        self.bridge.show_window.connect(self.show_from_tray)
        self.bridge.quit_app.connect(self.quit_application)
        self.bridge.scan_result.connect(self.scan_finished)
        self.tray = None
        self.worker = None
        self.scan_monitor = None
        self.realtime_worker = None
        self.settings = QSettings("LunaSecurity", "LunaSecurity")
        global APP_LANGUAGE
        APP_LANGUAGE = self.settings.value("language", "de")
        self._build_ui()
        self.refresh_security_dashboard()
        self._qt_tray = QSystemTrayIcon(self)
        self._qt_tray.setIcon(QIcon.fromTheme("security-high", QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)))
        self._qt_tray.setToolTip("LunaSecurity – Keine offenen Warnungen")
        if QSystemTrayIcon.isSystemTrayAvailable():
            self._qt_tray.show()
        self.module_worker = None
        self.package_verify_worker = None
        self.package_verify_started = 0.0
        self._realtime_log_path = Path("/var/log/clamav/lunasecurity-onaccess.log")
        self._realtime_log_offset = self._realtime_log_path.stat().st_size if self._realtime_log_path.exists() else 0
        self._realtime_log_timer = QTimer(self)
        self._realtime_log_timer.timeout.connect(self.check_realtime_log)
        self._realtime_log_timer.start(2000)
        self._start_tray()
        self._sync_tray_status()

    def _build_ui(self):
        self.apply_theme(self.settings.value("theme", "dark"))
        root = QWidget(); self.setCentralWidget(root)
        shell = QHBoxLayout(root); shell.setContentsMargins(0, 0, 0, 0); shell.setSpacing(0)
        sidebar = QWidget(); sidebar.setObjectName("sidebar"); sidebar.setFixedWidth(292)
        side_layout = QVBoxLayout(sidebar); side_layout.setContentsMargins(12, 16, 12, 10); side_layout.setSpacing(9)
        brand = QLabel("◈  LunaSecurity\n     Linux Security Suite")
        self.brand_label = brand
        brand.setStyleSheet("font-size:16pt;font-weight:700;color:#ffffff;padding:10px 5px 22px 5px")
        side_layout.addWidget(brand)
        self.side_nav = QListWidget(); self.side_nav.setObjectName("sideNav"); self.side_nav.setSpacing(2)
        side_layout.addWidget(self.side_nav, 1)
        side_layout.addWidget(MoonArtwork(sidebar))
        shell.addWidget(sidebar)

        content = QWidget(); shell.addWidget(content, 1)
        layout = QVBoxLayout(content); layout.setContentsMargins(16, 12, 16, 12); layout.setSpacing(9)
        header = QHBoxLayout()
        title = QLabel("LunaSecurity"); title.setObjectName("title"); header.addWidget(title)
        header.addStretch()
        profile_label = QLabel("Profil:"); profile_label.setObjectName("muted"); header.addWidget(profile_label)
        self.scan_profile = QComboBox()
        self.scan_profile.addItem("Eigenes Profil", "custom")
        self.scan_profile.addItem("Standard (Empfohlen)", "standard")
        self.scan_profile.addItem("Hoher Schutz", "high")
        self.scan_profile.addItem("Maximaler Schutz", "maximum")
        self.scan_profile.addItem("Profil verwalten …", "manage")
        saved_profile = self.settings.value("scan_profile", "custom")
        # Ältere 0.4.32-Teststände speicherten den sichtbaren Profilnamen.
        legacy_profiles = {"Eigenes Profil": "custom", "Standard (Empfohlen)": "standard",
                           "Hoher Schutz": "high", "Maximaler Schutz": "maximum"}
        saved_profile = legacy_profiles.get(saved_profile, saved_profile)
        idx = self.scan_profile.findData(saved_profile)
        if idx >= 0: self.scan_profile.setCurrentIndex(idx)
        self.scan_profile.setMinimumWidth(220)
        self.scan_profile.setToolTip("Legt das Sicherheitsniveau für Datei- und Ordnerscans fest.")
        self.scan_profile.activated.connect(self._profile_selected)
        header.addWidget(self.scan_profile)
        version = QLabel(f"LINUX SECURITY SUITE  ·  {__version__}"); version.setObjectName("muted"); header.addSpacing(12); header.addWidget(version)
        layout.addLayout(header)

        self.pages = QStackedWidget(); layout.addWidget(self.pages, 1)
        dashboard = QWidget(); self.dashboard_page = dashboard
        dash = QVBoxLayout(dashboard); dash.setContentsMargins(0, 0, 0, 0); dash.setSpacing(10)
        subrow = QHBoxLayout()
        subtitle = QLabel("Systemschutz – Übersicht"); subtitle.setObjectName("pageTitle"); subrow.addWidget(subtitle)
        subrow.addStretch()
        suite = QLabel("Sicherheitsübersicht für dein Linux-System"); suite.setObjectName("muted"); subrow.addWidget(suite)
        dash.addLayout(subrow)

        self.alert_banner = QLabel("⚠ BEDROHUNG ERKANNT – Details siehe Sicherheitsereignisse")
        self.alert_banner.setStyleSheet("background:#6f202b;color:#fff;border:1px solid #e05262;border-radius:8px;padding:10px;font-weight:700")
        self.alert_banner.setWordWrap(True); self.alert_banner.hide(); dash.addWidget(self.alert_banner)

        summary = QHBoxLayout(); summary.setSpacing(10)
        for heading, detail, kind, accent in [
            ("Virenschutz", "ClamAV-Scanner und Echtzeitschutz", "shield", "#35dc80"),
            ("Systemschutz", "Rootkit-, AIDE- und Integritätsprüfung", "layers", "#ff9d32"),
            ("Netzwerk", "Ports und Firewall-Regeln", "wifi", "#28aaff"),
            ("Systemstatus", "Überwachung und Dienste", "monitor", "#45dce0")]:
            card = QFrame(); card.setObjectName("featureCard"); box = QHBoxLayout(card); box.setContentsMargins(12, 10, 12, 10)
            icon = DashboardIcon(kind, accent)
            texts = QVBoxLayout(); h = QLabel(heading); h.setStyleSheet("font-size:12pt;font-weight:700")
            d = QLabel(detail); d.setObjectName("muted"); d.setWordWrap(True); texts.addWidget(h); texts.addWidget(d)
            ok = QLabel("●"); ok.setStyleSheet("color:#35dc80;font-size:16pt")
            box.addWidget(icon); box.addLayout(texts, 1); box.addWidget(ok); summary.addWidget(card)
        dash.addLayout(summary)

        columns = QHBoxLayout(); columns.setSpacing(12)
        left = QWidget(); left_col = QVBoxLayout(left); left_col.setContentsMargins(0,0,0,0); left_col.setSpacing(9)
        scan_panel = QFrame(); scan_panel.setObjectName("featureCard"); scan_box = QVBoxLayout(scan_panel); scan_box.setContentsMargins(12,12,12,12); scan_box.setSpacing(9)
        scan_modes = QHBoxLayout()
        # Die zwei Scanaktionen verwenden immer das oben ausgewählte Profil.
        # Home scannt ausschließlich das persönliche Benutzerverzeichnis;
        # der vollständige Systemscan prüft / mit Administratorrechten.
        self.quick_scan_button = QPushButton("⌂  Home-Verzeichnis")
        self.quick_scan_button.setObjectName("accentButton")
        self.quick_scan_button.setToolTip("Prüft dein Home-Verzeichnis mit den Einstellungen des ausgewählten Scanprofils.")
        self.quick_scan_button.clicked.connect(lambda: self.start_scan(Path.home()))
        self.full_scan_button = QPushButton("▣  Vollständiger Systemscan")
        self.full_scan_button.setToolTip("Prüft das gesamte Dateisystem / mit den Einstellungen des ausgewählten Scanprofils. Administratorrechte werden über pkexec angefordert.")
        self.full_scan_button.clicked.connect(lambda: self.start_scan("/", elevated=True))
        for b in (self.quick_scan_button, self.full_scan_button):
            b.setMinimumHeight(42); scan_modes.addWidget(b)
        scan_box.addLayout(scan_modes)
        scan_body = QHBoxLayout(); ring = QLabel("◈\n⌕"); ring.setAlignment(Qt.AlignmentFlag.AlignCenter); ring.setMinimumSize(190, 190); ring.setMaximumWidth(230)
        ring.setStyleSheet("font-size:43pt;color:#d08aff;border:8px solid #8645e8;border-radius:100px;background:qradialgradient(cx:.5,cy:.5,radius:.7,fx:.5,fy:.5,stop:0 #30204e,stop:1 #111629);padding:15px")
        scan_body.addWidget(ring, 1)
        scan_info = QVBoxLayout(); scan_title = QLabel("Sicherheitsprüfung"); scan_title.setStyleSheet("font-size:19pt;font-weight:700")
        scan_hint = QLabel("Prüft wichtige Systembereiche auf Bedrohungen."); scan_hint.setObjectName("muted")
        scan_info.addWidget(scan_title); scan_info.addWidget(scan_hint)
        self.scan_scope_label = QLabel("✓  Laufende Prozesse\n✓  Autostart-Einträge\n✓  Systemverzeichnisse\n✓  Bekannte Schadsoftware")
        self.scan_scope_label.setStyleSheet("font-size:11pt;line-height:1.5"); scan_info.addWidget(self.scan_scope_label)
        self.scan_button = QPushButton("▶  Scan starten"); self.scan_button.setObjectName("accentButton"); self.scan_button.setMinimumHeight(48); self.scan_button.clicked.connect(lambda: self.start_scan())
        scan_info.addWidget(self.scan_button); scan_info.addStretch(); scan_body.addLayout(scan_info, 2)
        scan_box.addLayout(scan_body); left_col.addWidget(scan_panel, 3)

        log_panel = QFrame(); log_panel.setObjectName("featureCard"); log_layout = QVBoxLayout(log_panel); log_layout.setContentsMargins(10,8,10,8)
        log_head = QHBoxLayout(); log_title = QLabel("▣  Scan-Protokoll"); log_title.setStyleSheet("font-size:13pt;font-weight:700"); log_head.addWidget(log_title); log_head.addStretch()
        clear_log = QPushButton("Protokoll leeren"); clear_log.clicked.connect(lambda: self.log.clear()); log_head.addWidget(clear_log); log_layout.addLayout(log_head)
        self.log = QTextEdit(); self.log.setReadOnly(True); self.log.setMinimumHeight(140); self.log.setPlaceholderText("Scan-Ergebnisse und Sicherheitsmeldungen erscheinen hier.")
        self.log.setStyleSheet("font-family:'DejaVu Sans Mono';font-size:10pt;background:#080e1d;border:1px solid #39466e;border-radius:8px")
        log_layout.addWidget(self.log, 1); left_col.addWidget(log_panel, 2)

        stats = QHBoxLayout(); stats.setSpacing(7)
        self.stat_threats = QLabel("✓  Bedrohungen\n0"); self.stat_files = QLabel("▱  Geprüfte Dateien\n0")
        self.stat_size_limit = QLabel("◉  Größenlimit\n0")
        self.stat_unreadable = QLabel("⊘  Nicht lesbare\n0"); self.stat_skipped = QLabel("↪  Übersprungen\n0"); self.stat_duration = QLabel("◷  Dauer\n00:00:00")
        for widget in (self.stat_threats,self.stat_files,self.stat_size_limit,self.stat_unreadable,self.stat_skipped,self.stat_duration):
            widget.setObjectName("statCard"); widget.setAlignment(Qt.AlignmentFlag.AlignCenter); widget.setMinimumHeight(58); stats.addWidget(widget)
        left_col.addLayout(stats); columns.addWidget(left, 7)

        right = QWidget(); right_col = QVBoxLayout(right); right_col.setContentsMargins(0,0,0,0); right_col.setSpacing(9)
        self.realtime_card = QFrame(); self.realtime_card.setObjectName("featureCard"); rt = QVBoxLayout(self.realtime_card)
        rt_head = QHBoxLayout(); self.realtime_icon_label = QLabel("⬡"); self.realtime_icon_label.setStyleSheet("font-size:27pt;color:#e0a52b"); rt_head.addWidget(self.realtime_icon_label)
        rt_text = QVBoxLayout(); self.realtime_title_label = QLabel("Echtzeitschutz: Status wird geprüft …"); self.realtime_title_label.setStyleSheet("font-size:13pt;font-weight:700;color:#e0a52b"); rt_text.addWidget(self.realtime_title_label)
        rt_sub = QLabel("Überwacht dein System in Echtzeit (ClamAV)."); rt_sub.setObjectName("muted"); rt_sub.setWordWrap(True); rt_text.addWidget(rt_sub); rt_head.addLayout(rt_text,1); rt.addLayout(rt_head)
        self.realtime_button = QPushButton("Echtzeitschutz deaktivieren"); self.realtime_button.clicked.connect(self.toggle_realtime); rt.addWidget(self.realtime_button)
        right_col.addWidget(self.realtime_card)

        sig_card = QFrame(); sig_card.setObjectName("featureCard"); sig = QVBoxLayout(sig_card)
        sig_title = QLabel("◉  Virensignaturen"); sig_title.setStyleSheet("font-size:13pt;font-weight:700"); sig.addWidget(sig_title)
        self.signature_version_label = QLabel(signature_database_versions()); self.signature_version_label.setObjectName("muted"); self.signature_version_label.setWordWrap(True); sig.addWidget(self.signature_version_label)
        self.update_button = QPushButton("⟳  Jetzt aktualisieren"); self.update_button.clicked.connect(self.update_signatures_now); sig.addWidget(self.update_button)
        right_col.addWidget(sig_card)

        info_card = QFrame(); info_card.setObjectName("featureCard"); info = QVBoxLayout(info_card)
        info_title = QLabel("ⓘ  System-Informationen"); info_title.setStyleSheet("font-size:13pt;font-weight:700"); info.addWidget(info_title)
        import platform
        self.system_info_label = QLabel(f"System: Debian GNU/Linux\nKernel: {platform.release()}\nArchitektur: {platform.machine()}\nPython: {platform.python_version()}")
        self.system_info_label.setObjectName("muted"); info.addWidget(self.system_info_label); right_col.addWidget(info_card)

        fw_card = QFrame(); fw_card.setObjectName("featureCard"); fw = QVBoxLayout(fw_card)
        fw_title = QLabel("▦  Firewall"); fw_title.setStyleSheet("font-size:13pt;font-weight:700"); fw.addWidget(fw_title)
        fw_hint = QLabel("Ports und Firewall-Regeln überwachen."); fw_hint.setObjectName("muted"); fw.addWidget(fw_hint)
        fw_btn = QPushButton("Firewall-Bericht"); fw_btn.clicked.connect(lambda: self.side_nav.setCurrentRow(6)); fw.addWidget(fw_btn)
        self.virustotal_button = QPushButton("🌐  VirusTotal-Check")
        self.virustotal_button.setToolTip("SHA-256 einer ausgewählten Datei bei VirusTotal nachschlagen. Die Datei wird nicht hochgeladen.")
        self.virustotal_button.clicked.connect(self.start_virustotal_check)
        fw.addWidget(self.virustotal_button)
        right_col.addWidget(fw_card); right_col.addStretch(); columns.addWidget(right, 3)
        dash.addLayout(columns, 1)
        self.pages.addWidget(dashboard)

        self.auto_update_check = QCheckBox("Vor jedem Scan automatisch Virensignaturen mit freshclam aktualisieren")
        self.auto_update_check.setChecked(self.settings.value("auto_freshclam", False, type=bool))
        self.auto_update_check.setToolTip("Führt vor jedem Scan eine Signaturaktualisierung mit Administrator-Passwortabfrage aus. Wenn der ClamAV-Dienst läuft, übernimmt dieser die Aktualisierung.")
        self.auto_update_check.toggled.connect(lambda value: self.settings.setValue("auto_freshclam", value))
        self.system_scan_button = self.full_scan_button
        self._realtime_status_known = False; self._realtime_active = False; self._realtime_success = False; self._realtime_pending_action = "status"
        QTimer.singleShot(0, self.refresh_realtime_status)
        self.realtime_status = QLabel("Echtzeitschutz: Status wird geprüft …")
        self.realtime_indicator = QLabel("●")
        self.progress = QProgressBar(self); self.progress.setRange(0, 0); self.progress.hide()
        self.cancel_scan_button = QPushButton("Scan abbrechen", self); self.cancel_scan_button.setEnabled(False); self.cancel_scan_button.clicked.connect(self.cancel_scan); self.cancel_scan_button.hide()
        self.tray_check = QCheckBox("Beim Schließen im Infobereich weiterlaufen")
        self.tray_check.setChecked(self.settings.value("minimize_to_tray", True, type=bool)); self.tray_check.toggled.connect(self.set_minimize_to_tray)
        self.start_hidden_check = QCheckBox("Beim Start direkt im Infobereich starten")
        self.start_hidden_check.setChecked(self.settings.value("start_in_tray", False, type=bool)); self.start_hidden_check.toggled.connect(self.set_start_in_tray)
        self.autostart_check = QCheckBox("LunaSecurity automatisch bei der Anmeldung starten")
        self.autostart_check.setChecked(self.settings.value("autostart_enabled", False, type=bool)); self.autostart_check.toggled.connect(self.set_autostart)
        tabs = QTabWidget(); tabs.setMinimumHeight(205); tabs.tabBar().hide()
        # Erweiterte Diagnose: Lynis und fail2ban werden ausschließlich lesend abgefragt.
        advanced_tab = QWidget(); advanced_layout = QVBoxLayout(advanced_tab)
        advanced_intro = QLabel("Zusätzliche Systemhärtungsprüfung und Überwachung. Diese Funktionen lesen den Systemstatus und ändern keine Sicherheitsregeln.")
        advanced_intro.setWordWrap(True); advanced_intro.setObjectName("muted"); advanced_layout.addWidget(advanced_intro)
        self.advanced_output = QTextEdit(); self.advanced_output.setReadOnly(True); self.advanced_output.setMinimumHeight(140)
        adv_buttons = QHBoxLayout()
        lynis_btn = QPushButton("Lynis-Sicherheitsprüfung starten")
        lynis_btn.clicked.connect(lambda: self.run_module("Lynis-Sicherheitsprüfung", self.run_lynis_audit, cancellable=True))
        fail2ban_btn = QPushButton("fail2ban-Status prüfen")
        fail2ban_btn.clicked.connect(lambda: self.run_module("fail2ban-Überwachung", self.read_fail2ban_status, cancellable=True))
        refresh_dash_btn = QPushButton("Dashboard aktualisieren"); refresh_dash_btn.clicked.connect(self.refresh_security_dashboard)
        for b in (lynis_btn, fail2ban_btn, refresh_dash_btn): adv_buttons.addWidget(b)
        advanced_layout.addLayout(adv_buttons); advanced_layout.addWidget(self.advanced_output, 1)
        report_row = QHBoxLayout()
        html_report_btn = QPushButton("Sicherheitsbericht als HTML speichern"); html_report_btn.clicked.connect(self.export_security_report_html)
        pdf_report_btn = QPushButton("Sicherheitsbericht als PDF speichern"); pdf_report_btn.clicked.connect(self.export_security_report_pdf)
        report_row.addWidget(html_report_btn); report_row.addWidget(pdf_report_btn); advanced_layout.addLayout(report_row)
        tabs.addTab(advanced_tab, "Erweiterte Sicherheit")
        self.tabs = tabs
        tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        events_tab = QWidget(); events_layout = QVBoxLayout(events_tab)
        self.events_view = QListWidget()
        self.events_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.events_view.setToolTip("Erkannte Dateien auswählen, um sie zu isolieren oder zu löschen.")
        events_layout.addWidget(self.events_view, 1)
        event_actions = QHBoxLayout()
        quarantine_event_btn = QPushButton("Ausgewählten Fund in Quarantäne")
        quarantine_event_btn.clicked.connect(self.quarantine_detected_event)
        delete_event_btn = QPushButton("Gefundene Datei löschen")
        delete_event_btn.clicked.connect(self.delete_detected_event)
        clear_events = QPushButton("Ereignisprotokoll leeren")
        clear_events.clicked.connect(self.clear_security_events)
        for button in (quarantine_event_btn, delete_event_btn, clear_events):
            event_actions.addWidget(button)
        events_layout.addLayout(event_actions)
        tabs.addTab(events_tab, "Sicherheitsereignisse")
        self.load_security_events()

        quarantine_tab = QWidget(); quarantine_layout = QVBoxLayout(quarantine_tab)
        self.quarantine_table = QTableWidget(0, 4)
        self.quarantine_table.setHorizontalHeaderLabels(["Ursprünglicher Pfad", "SHA-256", "Quarantäne seit", "Interne Ablage"])
        self.quarantine_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.quarantine_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.quarantine_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.quarantine_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.quarantine_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.quarantine_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.quarantine_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        quarantine_layout.addWidget(self.quarantine_table, 1)
        quarantine_actions = QHBoxLayout()
        refresh_quarantine_btn = QPushButton("Aktualisieren")
        refresh_quarantine_btn.clicked.connect(self.refresh_quarantine)
        restore_quarantine_btn = QPushButton("Wiederherstellen")
        restore_quarantine_btn.clicked.connect(self.restore_quarantine_selected)
        erase_quarantine_btn = QPushButton("Endgültig löschen")
        erase_quarantine_btn.clicked.connect(self.delete_quarantine_selected)
        for button in (refresh_quarantine_btn, restore_quarantine_btn, erase_quarantine_btn):
            quarantine_actions.addWidget(button)
        quarantine_layout.addLayout(quarantine_actions)
        tabs.addTab(quarantine_tab, "Quarantäne")
        self.tabs = tabs
        self.quarantine_tab_index = tabs.indexOf(quarantine_tab)
        self.refresh_quarantine()
        system_tab = QWidget(); system_layout = QVBoxLayout(system_tab)
        rootkit_btn = QPushButton("Rootkit-Prüfung starten (rkhunter + chkrootkit)")
        rootkit_btn.clicked.connect(lambda: self.run_module("Rootkit-Prüfung", sec.rootkit_checks, cancellable=True))
        integrity_btn = QPushButton("Systemintegrität prüfen (AIDE)")
        integrity_btn.clicked.connect(lambda: self.run_module("Systemintegrität", sec.integrity_check, cancellable=True))
        audit_btn = QPushButton("System-Audit (Autostart, Dienste, Cron, SSH)")
        audit_btn.clicked.connect(lambda: self.run_module("System-Audit", sec.system_audit, cancellable=True))
        for b in (rootkit_btn, integrity_btn, audit_btn):
            b.setMinimumHeight(48); b.setMinimumWidth(0); b.setSizePolicy(b.sizePolicy().horizontalPolicy(), b.sizePolicy().verticalPolicy()); b.setToolTip(b.text()); system_layout.addWidget(b)
        system_layout.addStretch(); tabs.addTab(system_tab, "Systemschutz")

        # Klar gegliederte Reparaturverwaltung mit eigenem Scrollbereich.
        repair_tab = QWidget(); self.repair_tab = repair_tab
        repair_tab_layout = QVBoxLayout(repair_tab); repair_tab_layout.setContentsMargins(5, 5, 5, 5)
        repair_scroll = QScrollArea(); repair_scroll.setWidgetResizable(True); repair_scroll.setFrameShape(QFrame.NoFrame)
        repair_content = QWidget(); repair_layout = QVBoxLayout(repair_content)
        repair_layout.setContentsMargins(8, 8, 8, 8); repair_layout.setSpacing(10)
        repair_intro = QLabel("Reparaturen nur nach deiner Bestätigung. Vor Änderungen werden Sicherungen angelegt. Systemdateien und Rootkit-Funde werden nicht blind verändert.")
        repair_intro.setWordWrap(True); repair_intro.setObjectName("muted"); repair_layout.addWidget(repair_intro)

        auto_group = QGroupBox("Benutzer-Autostart")
        auto_layout = QVBoxLayout(auto_group)
        auto_hint = QLabel("Einträge dieses Benutzerkontos anzeigen, reversibel deaktivieren oder zurückholen.")
        auto_hint.setWordWrap(True); auto_hint.setObjectName("muted"); auto_layout.addWidget(auto_hint)
        self.repair_autostart_list = QListWidget(); self.repair_autostart_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.repair_autostart_list.setMinimumHeight(78); self.repair_autostart_list.setMaximumHeight(115)
        auto_layout.addWidget(self.repair_autostart_list)
        auto_actions = QHBoxLayout()
        refresh_repair_btn = QPushButton("Liste aktualisieren"); refresh_repair_btn.clicked.connect(self.refresh_repair_autostart)
        disable_repair_btn = QPushButton("Sichern & deaktivieren"); disable_repair_btn.clicked.connect(self.disable_selected_autostart)
        restore_repair_btn = QPushButton("Eintrag wiederherstellen"); restore_repair_btn.clicked.connect(self.restore_autostart_entry)
        for button in (refresh_repair_btn, disable_repair_btn, restore_repair_btn):
            button.setMinimumHeight(38); button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed); auto_actions.addWidget(button)
        auto_layout.addLayout(auto_actions); repair_layout.addWidget(auto_group)

        package_group = QGroupBox("Debian-Paketintegrität und Reparatur")
        package_layout = QVBoxLayout(package_group)
        package_hint = QLabel("Prüft installierte Paketdateien. Bei Abweichungen kannst du das betroffene Paket über APT neu installieren.")
        package_hint.setWordWrap(True); package_hint.setObjectName("muted"); package_layout.addWidget(package_hint)
        self.verify_package_btn = QPushButton("Installierte Pakete auf Dateiänderungen prüfen")
        self.verify_package_btn.setMinimumHeight(40); self.verify_package_btn.clicked.connect(self.verify_installed_packages); package_layout.addWidget(self.verify_package_btn)
        self.verify_package_progress = QProgressBar(); self.verify_package_progress.setRange(0, 0)
        self.verify_package_progress.setTextVisible(False); self.verify_package_progress.setFixedHeight(9)
        self.verify_package_progress.hide(); package_layout.addWidget(self.verify_package_progress)
        verify_status_row = QHBoxLayout()
        self.verify_package_status = QLabel(""); self.verify_package_status.setObjectName("muted")
        verify_status_row.addWidget(self.verify_package_status, 1)
        self.cancel_package_verify_btn = QPushButton("Prüfung abbrechen")
        self.cancel_package_verify_btn.setMinimumHeight(30); self.cancel_package_verify_btn.hide()
        self.cancel_package_verify_btn.clicked.connect(self.cancel_package_verification)
        verify_status_row.addWidget(self.cancel_package_verify_btn)
        package_layout.addLayout(verify_status_row)
        self.package_verify_timer = QTimer(self); self.package_verify_timer.setInterval(1000)
        self.package_verify_timer.timeout.connect(self.update_package_verify_elapsed)
        package_row = QHBoxLayout()
        self.repair_package_combo = QComboBox(); self.repair_package_combo.setMinimumWidth(0); self.repair_package_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.repair_package_combo.setToolTip("Pakete mit von dpkg gemeldeten Dateiabweichungen")
        self.repair_package_btn = QPushButton("Paket sichern & reparieren")
        self.repair_package_btn.setMinimumHeight(38); self.repair_package_btn.clicked.connect(self.reinstall_selected_package)
        package_row.addWidget(self.repair_package_combo, 1); package_row.addWidget(self.repair_package_btn)
        package_layout.addLayout(package_row); repair_layout.addWidget(package_group)

        restore_group = QGroupBox("Wiederherstellung")
        restore_layout = QVBoxLayout(restore_group)
        restore_hint = QLabel("Vorherige Sicherungen auswählen und zurückspielen. Bereits vorhandene Dateien werden nicht überschrieben.")
        restore_hint.setWordWrap(True); restore_hint.setObjectName("muted"); restore_layout.addWidget(restore_hint)
        self.package_rollback_btn = QPushButton("Gesicherte Paketdateien wiederherstellen")
        self.package_rollback_btn.setMinimumHeight(40); self.package_rollback_btn.clicked.connect(self.rollback_package_files)
        restore_layout.addWidget(self.package_rollback_btn); repair_layout.addWidget(restore_group)

        result_group = QGroupBox("Prüfergebnisse und Reparaturprotokoll")
        result_layout = QVBoxLayout(result_group)
        self.repair_output = QTextEdit(); self.repair_output.setReadOnly(True)
        self.repair_output.setPlaceholderText("Hier erscheinen Prüfergebnisse, Sicherungen und Reparaturschritte …")
        self.repair_output.setMinimumHeight(125); result_layout.addWidget(self.repair_output)
        repair_layout.addWidget(result_group)
        repair_layout.addStretch(1)
        repair_scroll.setWidget(repair_content); repair_tab_layout.addWidget(repair_scroll)
        tabs.addTab(repair_tab, "Reparatur & Wiederherstellung")
        self.refresh_repair_autostart()
        net_tab = QWidget(); net_layout = QVBoxLayout(net_tab)
        net_btn = QPushButton("Netzwerk- und Firewall-Sicherheitscheck (mit Admin-Abfrage)")
        net_btn.clicked.connect(lambda: self.run_module("Netzwerkprüfung", sec.network_audit))
        net_btn.setMinimumHeight(48); net_btn.setMinimumWidth(0); net_layout.addWidget(net_btn)

        # Zweite Aktionsreihe: Firewall-Portverwaltung direkt auf der Netzwerkseite.
        # Die eigentliche nftables-Implementierung und die getrennte LunaSecurity-
        # Tabelle stammen aus dem vorherigen, funktionierenden Stand.
        firewall_actions = QHBoxLayout()
        self.firewall_block_button = QPushButton("⊘  Port gezielt sperren …")
        self.firewall_block_button.setMinimumHeight(44)
        self.firewall_block_button.clicked.connect(self.block_firewall_port)
        self.firewall_persist_button = QPushButton("▣  Testregeln dauerhaft speichern")
        self.firewall_persist_button.setMinimumHeight(44)
        self.firewall_persist_button.clicked.connect(self.persist_firewall_guard)
        self.firewall_rollback_button = QPushButton("↶  LunaSecurity-Sperren aufheben")
        self.firewall_rollback_button.setMinimumHeight(44)
        self.firewall_rollback_button.clicked.connect(self.rollback_firewall_guard)
        firewall_actions.addWidget(self.firewall_block_button, 1)
        firewall_actions.addWidget(self.firewall_persist_button, 1)
        firewall_actions.addWidget(self.firewall_rollback_button, 1)
        net_layout.addLayout(firewall_actions)

        firewall_hint = QLabel(
            "Port-Sperren werden zunächst temporär getestet. Über „Testregeln dauerhaft "
            "speichern“ bleiben sie nach einem Neustart aktiv. „LunaSecurity-Sperren "
            "aufheben“ entfernt ausschließlich die von LunaSecurity verwalteten Regeln. "
            "SSH-Port 22 ist zum Schutz vor Aussperren ausgeschlossen."
        )
        firewall_hint.setWordWrap(True)
        firewall_hint.setObjectName("muted")
        net_layout.addWidget(firewall_hint)
        net_layout.addStretch()
        tabs.addTab(net_tab, "Netzwerk")
        file_tab = QWidget(); file_layout = QVBoxLayout(file_tab)
        yara_row = QHBoxLayout(); self.yara_path = QLabel("Kein Scan-Ziel ausgewählt")
        yara_pick = QPushButton("Datei/Ordner für YARA auswählen")
        yara_pick.clicked.connect(self.choose_yara_target)
        yara_pick.setMinimumHeight(48); yara_pick.setMinimumWidth(220); yara_pick.setToolTip(yara_pick.text()); self.yara_path.setWordWrap(True); yara_row.addWidget(yara_pick); yara_row.addWidget(self.yara_path,1); file_layout.addLayout(yara_row)
        yara_update_row = QHBoxLayout()
        self.yara_update_button = QPushButton("YARA-Regeln aktualisieren")
        self.yara_update_button.setMinimumHeight(42)
        self.yara_update_button.clicked.connect(self.update_yara_rules)
        self.yara_rules_status = QLabel("")
        self.yara_rules_status.setWordWrap(True)
        yara_update_row.addWidget(self.yara_update_button)
        yara_update_row.addWidget(self.yara_rules_status, 1)
        file_layout.addLayout(yara_update_row)
        self.refresh_yara_rules_status()
        quarantine_btn = QPushButton("Datei auswählen und in Quarantäne verschieben")
        quarantine_btn.clicked.connect(self.quarantine_selected)
        list_btn = QPushButton("Quarantäne anzeigen")
        list_btn.clicked.connect(lambda: (self.refresh_quarantine(), self.tabs.setCurrentIndex(self.quarantine_tab_index)))
        quarantine_btn.setMinimumHeight(48); quarantine_btn.setMinimumWidth(0); quarantine_btn.setToolTip(quarantine_btn.text())
        list_btn.setMinimumHeight(48); file_layout.addWidget(quarantine_btn); file_layout.addWidget(list_btn); file_layout.addStretch()
        tabs.addTab(file_tab, "Dateiwerkzeuge")

        audio_tab = QWidget(); audio_layout = QVBoxLayout(audio_tab)
        audio_layout.addWidget(QLabel("Alarm bei erkannten Bedrohungen"))
        self.sound_enabled = QCheckBox("Akustischen Alarm aktivieren")
        self.sound_enabled.setChecked(self.settings.value("sound_enabled", True, type=bool))
        self.sound_enabled.toggled.connect(lambda v: self.settings.setValue("sound_enabled", v))
        backend_row = QHBoxLayout(); backend_row.addWidget(QLabel("Audio-Ausgabe"))
        self.audio_backend = QComboBox(); self.audio_backend.addItems(["Automatisch", "PipeWire (pw-play)", "PulseAudio (paplay)", "ALSA (aplay)"])
        self.audio_backend.setCurrentText(self.settings.value("audio_backend", "Automatisch"))
        self.audio_backend.currentTextChanged.connect(lambda v: self.settings.setValue("audio_backend", v))
        backend_row.addWidget(self.audio_backend, 1); audio_layout.addLayout(backend_row)
        device_row = QHBoxLayout(); device_row.addWidget(QLabel("Ausgabegerät"))
        self.audio_device = QComboBox(); self.audio_device.addItem("Standardgerät", "")
        self.refresh_audio_devices(); self.audio_device.currentIndexChanged.connect(self._save_audio_device)
        device_row.addWidget(self.audio_device, 1); audio_layout.addLayout(device_row)
        volume_row = QHBoxLayout(); volume_row.addWidget(QLabel("Lautstärke"))
        self.audio_volume = QSlider(); self.audio_volume.setOrientation(__import__('PySide6.QtCore', fromlist=['Qt']).Qt.Orientation.Horizontal); self.audio_volume.setRange(0,100); self.audio_volume.setValue(self.settings.value("audio_volume", 80, type=int))
        self.audio_volume.valueChanged.connect(lambda v: self.settings.setValue("audio_volume", v)); volume_row.addWidget(self.audio_volume, 1); audio_layout.addLayout(volume_row)
        custom_row = QHBoxLayout(); self.custom_sound_label = QLabel(); self._update_sound_label(); custom_row.addWidget(self.custom_sound_label, 1)
        choose_sound = QPushButton("WAV auswählen"); choose_sound.clicked.connect(self.choose_alarm_sound); custom_row.addWidget(choose_sound)
        builtin_sound = QPushButton("Eingebauten Sound verwenden"); builtin_sound.clicked.connect(self.use_builtin_sound); custom_row.addWidget(builtin_sound); audio_layout.addLayout(custom_row)
        test_sound = QPushButton("Testalarm abspielen"); test_sound.clicked.connect(self.play_alarm); audio_layout.addWidget(test_sound)
        audio_layout.addWidget(QLabel("PipeWire-, PulseAudio- und ALSA-Ausgabe werden automatisch erkannt. Geräteauswahl wird bei unterstützten Backends angewendet."))
        audio_layout.addStretch()
        audio_scroll = QScrollArea()
        audio_scroll.setWidgetResizable(True)
        audio_scroll.setFrameShape(QFrame.Shape.NoFrame)
        audio_scroll.setHorizontalScrollBarPolicy(__import__('PySide6.QtCore', fromlist=['Qt']).Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        audio_scroll.setVerticalScrollBarPolicy(__import__('PySide6.QtCore', fromlist=['Qt']).Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        audio_scroll.setWidget(audio_tab)
        tabs.addTab(audio_scroll, "Alarm & Audio")

        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        settings_intro = QLabel("Allgemeine Programmoptionen")
        settings_intro.setStyleSheet("font-size:13pt;font-weight:700")
        settings_layout.addWidget(settings_intro)
        settings_help = QLabel("Hier findest du alle aktivierbaren Optionen der Hauptoberfläche.")
        settings_help.setObjectName("muted")
        settings_layout.addWidget(settings_help)
        appearance_group = QGroupBox("Darstellung & Sprache")
        appearance_layout = QVBoxLayout(appearance_group)
        language_row = QHBoxLayout()
        language_row.addWidget(QLabel("Sprache / Language"))
        self.language_combo = QComboBox()
        self.language_combo.addItem("Deutsch", "de")
        self.language_combo.addItem("English", "en")
        self.language_combo.setCurrentIndex(max(0, self.language_combo.findData(self.settings.value("language", "de"))))
        self.language_combo.currentIndexChanged.connect(self.change_language)
        language_row.addWidget(self.language_combo, 1)
        appearance_layout.addLayout(language_row)
        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Design / Theme"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Dunkel – Graphit", "dark")
        self.theme_combo.addItem("Hell – Luna", "light")
        self.theme_combo.setCurrentIndex(max(0, self.theme_combo.findData(self.settings.value("theme", "dark"))))
        self.theme_combo.currentIndexChanged.connect(self.change_theme)
        theme_row.addWidget(self.theme_combo, 1)
        appearance_layout.addLayout(theme_row)
        settings_layout.addWidget(appearance_group)
        clam_group = QGroupBox("ClamAV – Scanoptionen")
        clam_layout = QVBoxLayout(clam_group)
        clam_intro = QLabel("Diese Optionen werden bei Datei- und Ordnerscans an ClamAV übergeben.")
        clam_intro.setObjectName("muted")
        clam_intro.setWordWrap(True)
        clam_layout.addWidget(clam_intro)

        self.ignore_max_filesize_check = QCheckBox("ClamAV-Größenlimit-Überschreitungen nicht als Bedrohung zählen")
        self.ignore_max_filesize_check.setChecked(self.settings.value("scan_ignore_max_filesize", True, type=bool))
        self.ignore_max_filesize_check.setToolTip("Global für alle Scanprofile: Heuristics.Limits.Exceeded.MaxFileSize wird als nicht vollständig geprüfte Datei statt als Malware-Fund behandelt. Andere Erkennungen bleiben unverändert aktiv.")
        self.ignore_max_filesize_check.toggled.connect(lambda v: self.settings.setValue("scan_ignore_max_filesize", v))
        clam_layout.addWidget(self.ignore_max_filesize_check)

        self.detect_pua_check = QCheckBox("Potenziell unerwünschte Programme (PUP) erkennen")
        self.detect_pua_check.setChecked(self.settings.value("scan_detect_pua", False, type=bool))
        self.detect_pua_check.setToolTip("Aktiviert ClamAVs Erkennung potenziell unerwünschter Anwendungen. Kann zusätzliche Treffer liefern.")
        self.detect_pua_check.toggled.connect(lambda v: self.settings.setValue("scan_detect_pua", v))
        clam_layout.addWidget(self.detect_pua_check)

        self.heuristics_check = QCheckBox("Heuristische Erkennung verwenden")
        self.heuristics_check.setChecked(self.settings.value("scan_heuristics", True, type=bool))
        self.heuristics_check.setToolTip("Aktiviert oder deaktiviert ClamAVs heuristische Erkennung.")
        self.heuristics_check.toggled.connect(lambda v: self.settings.setValue("scan_heuristics", v))
        clam_layout.addWidget(self.heuristics_check)

        self.hidden_files_check = QCheckBox("Versteckte Dateien und Ordner untersuchen")
        self.hidden_files_check.setChecked(self.settings.value("scan_hidden_files", False, type=bool))
        self.hidden_files_check.setToolTip("Bezieht bei Ordnerscans auch Einträge ein, deren Name mit einem Punkt beginnt.")
        self.hidden_files_check.toggled.connect(lambda v: self.settings.setValue("scan_hidden_files", v))
        clam_layout.addWidget(self.hidden_files_check)

        self.large_files_check = QCheckBox("Dateien größer als 20 MB untersuchen (bis 2 GB)")
        self.large_files_check.setChecked(self.settings.value("scan_large_files", False, type=bool))
        self.large_files_check.setToolTip("Erhöht die ClamAV-Grenzen für Dateigröße und entpackte Scanmenge auf bis zu 2 GB. Das kann deutlich länger dauern.")
        self.large_files_check.toggled.connect(lambda v: self.settings.setValue("scan_large_files", v))
        clam_layout.addWidget(self.large_files_check)

        self.recursive_check = QCheckBox("Unterordner rekursiv durchsuchen")
        self.recursive_check.setChecked(self.settings.value("scan_recursive", True, type=bool))
        self.recursive_check.setToolTip("Wenn deaktiviert, werden bei einem Ordnerscan nur Dateien direkt im ausgewählten Ordner geprüft.")
        self.recursive_check.toggled.connect(lambda v: self.settings.setValue("scan_recursive", v))
        clam_layout.addWidget(self.recursive_check)
        clam_layout.addWidget(self.auto_update_check)
        settings_layout.addWidget(clam_group)

        # VirusTotal API-Zugangsdaten: maskiert anzeigen und lokal in QSettings speichern.
        vt_group = QGroupBox("VirusTotal – API")
        vt_layout = QVBoxLayout(vt_group)
        vt_layout.addWidget(QLabel("VirusTotal-API-Schlüssel"))
        self.virustotal_api_key_edit = QLineEdit()
        self.virustotal_api_key_edit.setPlaceholderText("API-Schlüssel hier eingeben")
        self.virustotal_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.virustotal_api_key_edit.setText(self.settings.value("virustotal_api_key", ""))
        self.virustotal_api_key_edit.setToolTip("Der Schlüssel wird lokal in den LunaSecurity-Einstellungen gespeichert und nicht im Klartext angezeigt.")
        self.virustotal_api_key_edit.textChanged.connect(lambda value: self.settings.setValue("virustotal_api_key", value.strip()))
        vt_layout.addWidget(self.virustotal_api_key_edit)
        vt_help = QLabel("Der Schlüssel wird lokal in deinen LunaSecurity-Einstellungen gespeichert. Beim Check wird nur der SHA-256-Hash abgefragt – niemals automatisch die Datei hochgeladen. VirusTotal erhält den Hash und kann Abfragen in seinen Datensatz aufnehmen. Öffentliche API: standardmäßig höchstens 4 Anfragen pro Minute.")
        vt_help.setObjectName("muted")
        vt_help.setWordWrap(True)
        vt_layout.addWidget(vt_help)
        settings_layout.addWidget(vt_group)

        general_group = QGroupBox("Allgemeine Programmoptionen")
        general_layout = QVBoxLayout(general_group)
        general_layout.addWidget(self.tray_check)
        general_layout.addWidget(self.start_hidden_check)
        general_layout.addWidget(self.autostart_check)
        general_layout.addWidget(self.sound_enabled)
        settings_layout.addWidget(general_group)
        settings_layout.addStretch()
        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setFrameShape(QFrame.Shape.NoFrame)
        settings_scroll.setWidget(settings_tab)
        tabs.addTab(settings_scroll, "Einstellungen")
        # Sicherheitsereignisse bleiben der erste Navigationspunkt.
        events_index = tabs.indexOf(events_tab)
        if events_index > 0:
            tabs.tabBar().moveTab(events_index, 0)
        # Die Navigation liegt jetzt dauerhaft links; die alte mittlere Tableiste entfällt.
        self._navigation_labels = [
            ("Übersicht", "⌂"), ("Virenschutz", "◈"), ("Erweiterte Sicherheit", "✦"),
            ("Quarantäne", "⬡"), ("Systemschutz", "▣"), ("Reparatur & Wiederherstellung", "⚒"),
            ("Netzwerk", "◎"), ("Dateiwerkzeuge", "▤"), ("Alarm & Audio", "♫"), ("Einstellungen", "⚙"),
        ]
        for label, glyph in self._navigation_labels:
            self.side_nav.addItem(QListWidgetItem(f"{glyph}   {label}"))
        self.tabs = tabs
        self.pages.addWidget(tabs)
        self.side_nav.currentRowChanged.connect(self._navigate_to)
        tabs.currentChanged.connect(lambda index: self.side_nav.setCurrentRow(index + 1))
        self.side_nav.setCurrentRow(0)
        self.apply_theme(self.settings.value("theme", "dark"))
        self.retranslate_ui()


    def _navigate_to(self, row):
        if row <= 0:
            self.pages.setCurrentIndex(0)
            return
        self.pages.setCurrentIndex(1)
        if hasattr(self, "tabs"):
            target = min(row - 1, self.tabs.count() - 1)
            if target >= 0 and self.tabs.currentIndex() != target:
                self.tabs.setCurrentIndex(target)

    def _profile_selected(self, index):
        """Speichert eine stabile Profil-ID, unabhängig von der UI-Sprache."""
        profile = self.scan_profile.itemData(index) or "custom"
        if profile == "manage":
            self.side_nav.setCurrentRow(9)
            previous = self.settings.value("scan_profile", "custom")
            if previous in ("Eigenes Profil", "Standard (Empfohlen)", "Hoher Schutz", "Maximaler Schutz"):
                previous = {"Eigenes Profil": "custom", "Standard (Empfohlen)": "standard",
                            "Hoher Schutz": "high", "Maximaler Schutz": "maximum"}[previous]
            old_index = self.scan_profile.findData(previous)
            if old_index >= 0:
                self.scan_profile.setCurrentIndex(old_index)
            return
        self.settings.setValue("scan_profile", profile)
        descriptions = {
            "custom": "Verwendet die individuellen ClamAV-Scanoptionen aus den Einstellungen.",
            "standard": "Ausgewogene Prüfung mit heuristischer Erkennung und Unterordnern.",
            "high": "Zusätzlich PUP-Erkennung und Prüfung versteckter Dateien.",
            "maximum": "Alle erweiterten ClamAV-Prüfoptionen einschließlich großer Dateien.",
        }
        self.scan_scope_label.setText("✓  " + descriptions.get(profile, descriptions["custom"]))

    def change_theme(self, _index=None):
        theme = self.theme_combo.currentData()
        self.settings.setValue("theme", theme)
        self.apply_theme(theme)

    def apply_theme(self, theme=None):
        theme = theme or self.settings.value("theme", "dark")
        if theme == "light":
            css = """
            QMainWindow,QWidget {background:#f3f5fb;color:#20263a;font-family:'Noto Sans';font-size:12pt}
            QFrame#panel,QFrame#featureCard {background:#ffffff;border:1px solid #d7dced;border-radius:12px}
            QLabel#pageTitle {font-size:19pt;font-weight:700;color:#20263a}
            QLabel#statCard {background:#f4f5fb;border:1px solid #d7dced;border-radius:9px;padding:8px;font-weight:700}
            QLabel#title {font-size:23pt;font-weight:700;color:#20263a}
            QLabel#muted {color:#59647d}
            QPushButton {background:#526fe0;color:white;border:1px solid #718cf4;border-radius:9px;padding:7px 11px;font-weight:600;min-height:34px}
            QPushButton:hover {background:#6848d8;border-color:#8b72ef}
            QPushButton:disabled {background:#dce1ed;color:#8992a6;border-color:#cbd2e1}
            QTextEdit,QLineEdit,QComboBox,QSpinBox,QTableWidget,QListWidget {background:#ffffff;color:#20263a;border:1px solid #cbd3e5;border-radius:6px;selection-background-color:#dcd5ff;selection-color:#24203a}
            QCheckBox {spacing:8px;color:#20263a}
            QGroupBox {border:1px solid #cbd3e5;border-radius:9px;margin-top:9px;padding-top:8px;color:#303951}
            QGroupBox::title {subcontrol-origin:margin;left:10px;padding:0 5px;color:#4d5872}
            QProgressBar {background:#e6eaf3;color:#20263a;border:1px solid #cbd3e5;border-radius:6px;text-align:center}
            QProgressBar::chunk {background:#6651d9;border-radius:5px}
            """
            sidebar = self.findChild(QWidget, "sidebar")
            if sidebar: sidebar.setStyleSheet("QWidget#sidebar{background:#e6e9f4;border-right:1px solid #cbd3e5}")
            if hasattr(self, "brand_label"):
                self.brand_label.setStyleSheet("font-size:14pt;font-weight:700;color:#28314b;padding:8px 4px 16px 4px")
            if hasattr(self, "side_nav"):
                self.side_nav.setStyleSheet("QListWidget#sideNav{background:#e6e9f4;border:0;border-right:1px solid #cbd3e5;padding:9px 7px;outline:0} QListWidget#sideNav::item{color:#303951;padding:11px 9px;margin:3px 2px;border-radius:9px;min-height:22px} QListWidget#sideNav::item:hover{background:#d8dced} QListWidget#sideNav::item:selected{background:#ddd5ff;border:1px solid #927be8;color:#352477;font-weight:700}")
        else:
            css = """
            QMainWindow,QWidget {background:#111629;color:#e9edfa;font-family:'Noto Sans';font-size:12pt}
            QFrame#panel,QFrame#featureCard {background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #202a49,stop:1 #11192d);border:1px solid #53638f;border-radius:12px}
            QLabel#pageTitle {font-size:19pt;font-weight:700;color:#ffffff}
            QLabel#statCard {background:#1b2540;border:1px solid #45557e;border-radius:9px;padding:8px;font-weight:700;color:#f2f4ff}
            QLabel#title {font-size:23pt;font-weight:700;color:#ffffff}
            QLabel#muted {color:#aab8d5}
            QPushButton {background:#315bd5;color:white;border:1px solid #6484ff;border-radius:9px;padding:7px 11px;font-weight:600;min-height:34px}
            QPushButton:hover {background:#6544dc;border-color:#a78bfa}
            QPushButton#accentButton {background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #7438d6,stop:1 #9b4ef0);border:1px solid #c18cff;font-size:12pt;font-weight:700;padding:9px}
            QPushButton:disabled {background:#39445f;color:#9aa4b8;border-color:#46516b}
            QTextEdit,QLineEdit,QComboBox,QSpinBox,QTableWidget,QListWidget {background:#0b1122;color:#e9edfa;border:1px solid #34436f;border-radius:6px;selection-background-color:#49358d;selection-color:#ffffff}
            QCheckBox {spacing:8px;color:#e9edfa}
            QGroupBox {border:1px solid #34436f;border-radius:9px;margin-top:9px;padding-top:8px;color:#e9edfa}
            QGroupBox::title {subcontrol-origin:margin;left:10px;padding:0 5px;color:#c5ceef}
            QProgressBar {background:#0b1122;color:#e9edfa;border:1px solid #34436f;border-radius:6px;text-align:center}
            QProgressBar::chunk {background:#6847dc;border-radius:5px}
            """
            sidebar = self.findChild(QWidget, "sidebar")
            if sidebar: sidebar.setStyleSheet("QWidget#sidebar{background:#10142c;border-right:1px solid #35416c}")
            if hasattr(self, "brand_label"):
                self.brand_label.setStyleSheet("font-size:14pt;font-weight:700;color:#ffffff;padding:8px 4px 16px 4px")
            if hasattr(self, "side_nav"):
                self.side_nav.setStyleSheet("QListWidget#sideNav{background:#10142c;border:0;border-right:1px solid #35416c;padding:9px 7px;outline:0} QListWidget#sideNav::item{color:#e5e9fa;padding:11px 9px;margin:3px 2px;border-radius:9px;min-height:22px} QListWidget#sideNav::item:hover{background:#252653} QListWidget#sideNav::item:selected{background:#49358d;border:1px solid #9b78ff;color:white;font-weight:700}")
        self.setStyleSheet(css)

    def change_language(self, _index=None):
        global APP_LANGUAGE
        APP_LANGUAGE = self.language_combo.currentData()
        self.settings.setValue("language", APP_LANGUAGE)
        app = QApplication.instance()
        global APP_QT_TRANSLATOR, APP_DIALOG_BUTTON_FIX, APP_EN_DIALOG_FIX
        if app is not None:
            if APP_LANGUAGE == "en":
                if APP_QT_TRANSLATOR is not None:
                    app.removeTranslator(APP_QT_TRANSLATOR)
                if APP_DIALOG_BUTTON_FIX is not None:
                    app.removeEventFilter(APP_DIALOG_BUTTON_FIX)
                if APP_EN_DIALOG_FIX is None:
                    APP_EN_DIALOG_FIX = EnglishMessageBoxFix(app)
                app.installEventFilter(APP_EN_DIALOG_FIX)
            else:
                if APP_EN_DIALOG_FIX is not None:
                    app.removeEventFilter(APP_EN_DIALOG_FIX)
                if APP_QT_TRANSLATOR is None:
                    APP_QT_TRANSLATOR = GermanQtTranslator(app)
                app.installTranslator(APP_QT_TRANSLATOR)
                if APP_DIALOG_BUTTON_FIX is None:
                    APP_DIALOG_BUTTON_FIX = GermanDialogButtonFix(app)
                app.installEventFilter(APP_DIALOG_BUTTON_FIX)
            QLocale.setDefault(QLocale(QLocale.Language.English if APP_LANGUAGE == "en" else QLocale.Language.German,
                                       QLocale.Country.UnitedStates if APP_LANGUAGE == "en" else QLocale.Country.Germany))
        self.retranslate_ui()

    def retranslate_ui(self):
        language = self.settings.value("language", "de")
        mapping = EN_TRANSLATIONS if language == "en" else {}
        for widget in self.findChildren(QWidget):
            if isinstance(widget, QGroupBox):
                if not widget.property("_luna_source_text"):
                    widget.setProperty("_luna_source_text", widget.title())
                source_text = widget.property("_luna_source_text")
                widget.setTitle(mapping.get(source_text, source_text))
                if widget.toolTip():
                    if not widget.property("_luna_source_tooltip"):
                        widget.setProperty("_luna_source_tooltip", widget.toolTip())
                    widget.setToolTip(mapping.get(widget.property("_luna_source_tooltip"), widget.property("_luna_source_tooltip")))
            elif isinstance(widget, (QLabel, QPushButton, QCheckBox)):
                if not widget.property("_luna_source_text"):
                    widget.setProperty("_luna_source_text", widget.text())
                source_text = widget.property("_luna_source_text")
                widget.setText(mapping.get(source_text, source_text))
                if widget.toolTip():
                    if not widget.property("_luna_source_tooltip"):
                        widget.setProperty("_luna_source_tooltip", widget.toolTip())
                    widget.setToolTip(mapping.get(widget.property("_luna_source_tooltip"), widget.property("_luna_source_tooltip")))
            elif isinstance(widget, QComboBox) and widget is not self.language_combo and widget is not self.theme_combo:
                if not widget.property("_luna_source_items"):
                    widget.setProperty("_luna_source_items", [widget.itemText(i) for i in range(widget.count())])
                items = widget.property("_luna_source_items")
                current = widget.currentData()
                widget.blockSignals(True)
                for i, source in enumerate(items):
                    widget.setItemText(i, mapping.get(source, source))
                idx = widget.findData(current)
                if idx >= 0: widget.setCurrentIndex(idx)
                widget.blockSignals(False)
        if hasattr(self, "theme_combo"):
            self.theme_combo.setItemText(0, "Dark – Graphite" if language == "en" else "Dunkel – Graphit")
            self.theme_combo.setItemText(1, "Light – Luna" if language == "en" else "Hell – Luna")
        if hasattr(self, "side_nav"):
            labels = ["Overview","Virus protection","Advanced security","Quarantine","System protection","Repair & recovery","Network","File tools","Alerts & audio","Settings"] if language == "en" else [x[0] for x in self._navigation_labels]
            for i, label in enumerate(labels):
                item = self.side_nav.item(i)
                if item: item.setText(f"{self._navigation_labels[i][1]}   {label}")
        # Laufzeitstatus wird nicht aus dem gerade angezeigten (übersetzten)
        # Label abgeleitet, sondern aus dem zuletzt bestätigten Dienstzustand.
        if hasattr(self, "realtime_button"):
            pending = getattr(self, "_realtime_pending_action", None)
            if pending:
                pending_text = ("Echtzeitschutz: Hintergrundauftrag läuft …" if pending != "status"
                                else "Echtzeitschutz: Status wird geprüft …")
                self.realtime_status.setText(_ui_text(pending_text))
                self.realtime_button.setEnabled(False)
            elif getattr(self, "_realtime_status_known", False):
                active = self._realtime_active
                self.realtime_status.setText(_ui_text("Echtzeitschutz:") + " " + _ui_text("Aktiv" if active else "Aus"))
                self.realtime_button.setText(_ui_text("Echtzeitschutz deaktivieren" if active else "Echtzeitschutz aktivieren"))
                self.realtime_button.setEnabled(True)
            else:
                self.realtime_status.setText(_ui_text("Echtzeitschutz: Status wird geprüft …"))
                self.realtime_button.setEnabled(False)
        self.setWindowTitle("LunaSecurity – Linux Security Suite")
    def refresh_audio_devices(self):
        saved = self.settings.value("audio_device", "")
        pactl = shutil.which("pactl")
        if pactl:
            try:
                result = subprocess.run([pactl, "-f", "json", "list", "sinks"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    for sink in json.loads(result.stdout):
                        name = sink.get("name", "")
                        if name:
                            self.audio_device.addItem(sink.get("description") or name, name)
            except Exception:
                pass
        idx = self.audio_device.findData(saved)
        self.audio_device.setCurrentIndex(max(0, idx))

    def _save_audio_device(self, _index):
        self.settings.setValue("audio_device", self.audio_device.currentData() or "")

    def choose_alarm_sound(self):
        path, _ = _choose_file(self, "Alarm-WAV auswählen", Path.home(), "WAV-Dateien (*.wav)")
        if path:
            try:
                with wave.open(path, "rb") as wav:
                    if wav.getnchannels() not in (1, 2) or wav.getframerate() < 8000:
                        raise ValueError("Nicht unterstütztes WAV-Format")
                self.settings.setValue("custom_sound", path); self._update_sound_label()
            except Exception as exc:
                QMessageBox.warning(self, "Alarmdatei", f"Die WAV-Datei kann nicht verwendet werden: {exc}")

    def _update_sound_label(self):
        path = self.settings.value("custom_sound", "")
        self.custom_sound_label.setText(f"Eigene WAV: {path}" if path else "Aktiver Alarm: Eingebauter LunaSecurity-Sound")
        self.custom_sound_label.setToolTip(path or "Eingebauter LunaSecurity-Sound")

    def use_builtin_sound(self):
        self.settings.setValue("custom_sound", "")
        self._update_sound_label()

    def play_alarm(self):
        if not self.sound_enabled.isChecked() and self.sender() is None:
            return
        path = self.settings.value("custom_sound", "")
        temporary = None
        if not path or not Path(path).is_file():
            fd, temporary = tempfile.mkstemp(prefix="lunasecurity-alarm-", suffix=".wav")
            os.close(fd)
            # Sanfter, kurzer Dreiklang statt des bisherigen Rechtecksignals,
            # das auf manchen Lautsprechern als Knacken wahrgenommen wurde.
            rate = 44100
            melody = ((784.0, 0.24), (988.0, 0.24), (1174.66, 0.34))
            silence = 0.055
            samples = bytearray()
            for frequency, duration in melody:
                count = int(rate * duration)
                fade = max(1, int(rate * 0.018))
                for i in range(count):
                    envelope = min(1.0, i / fade, (count - 1 - i) / fade)
                    # Weiche Sinusschwingung mit zusätzlicher Pegelbegrenzung.
                    value = int(5200 * max(0.0, envelope) * math.sin(2.0 * math.pi * frequency * i / rate))
                    samples.extend(struct.pack("<h", value))
                samples.extend(b"\x00\x00" * int(rate * silence))
            with wave.open(temporary, "wb") as wav:
                wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(rate)
                wav.writeframes(samples)
            path = temporary
        backend = self.audio_backend.currentText()
        commands = []
        if backend in ("Automatisch", "PipeWire (pw-play)") and shutil.which("pw-play"):
            cmd = [shutil.which("pw-play"), "--volume", str(self.audio_volume.value()/100)]
            if self.audio_device.currentData(): cmd += ["--target", self.audio_device.currentData()]
            cmd.append(path); commands.append(cmd)
        if backend in ("Automatisch", "PulseAudio (paplay)") and shutil.which("paplay"):
            cmd = [shutil.which("paplay")]
            if self.audio_device.currentData(): cmd += ["--device", self.audio_device.currentData()]
            cmd += ["--volume", str(int(65536*self.audio_volume.value()/100))]
            cmd.append(path); commands.append(cmd)
        if backend in ("Automatisch", "ALSA (aplay)") and shutil.which("aplay"):
            cmd = [shutil.which("aplay"), "-q"]
            if self.audio_device.currentData(): cmd += ["-D", self.audio_device.currentData()]
            cmd.append(path); commands.append(cmd)
        if not commands:
            QMessageBox.warning(self, "Audio", "Kein passender Audioplayer gefunden. Installiere pipewire-audio, pulseaudio-utils oder alsa-utils.")
            return
        try:
            cmd = commands[0]
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        except OSError as exc:
            QMessageBox.warning(self, "Audio", str(exc))
        finally:
            if temporary:
                QTimer.singleShot(5000, lambda p=temporary: Path(p).unlink(missing_ok=True))

    def _autostart_file(self):
        return Path.home() / ".config" / "autostart" / "lunasecurity.desktop"

    def _write_autostart_entry(self, enabled):
        entry = self._autostart_file()
        if not enabled:
            entry.unlink(missing_ok=True)
            return
        entry.parent.mkdir(parents=True, exist_ok=True)
        hidden = self.settings.value("start_in_tray", False, type=bool)
        command = "/usr/bin/lunasecurity --hidden" if hidden else "/usr/bin/lunasecurity"
        content = (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=LunaSecurity\n"
            "Comment=Linux Security Suite\n"
            f"Exec={command}\n"
            "Icon=lunasecurity\n"
            "Terminal=false\n"
            "X-GNOME-Autostart-enabled=true\n"
        )
        entry.write_text(content, encoding="utf-8")
        entry.chmod(0o644)

    def set_start_in_tray(self, enabled):
        self.settings.setValue("start_in_tray", enabled)
        if self.settings.value("autostart_enabled", False, type=bool):
            try:
                self._write_autostart_entry(True)
            except OSError as exc:
                QMessageBox.warning(self, "Autostart", f"Autostart-Eintrag konnte nicht aktualisiert werden:\\n{exc}")

    def set_autostart(self, enabled):
        self.settings.setValue("autostart_enabled", enabled)
        try:
            self._write_autostart_entry(enabled)
        except OSError as exc:
            self.settings.setValue("autostart_enabled", not enabled)
            self.autostart_check.blockSignals(True)
            self.autostart_check.setChecked(not enabled)
            self.autostart_check.blockSignals(False)
            QMessageBox.warning(self, "Autostart", f"Autostart-Einstellung konnte nicht gespeichert werden:\\n{exc}")

    def _sync_tray_status(self):
        """Zeigt das neutrale Tray-Symbol nur bei gespeicherten Funden als Warnung."""
        events = self._read_security_events()
        status = "warning" if events else "normal"
        if hasattr(self, "_qt_tray"):
            if status == "warning":
                self._qt_tray.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning))
                self._qt_tray.setToolTip("LunaSecurity – Sicherheitswarnung vorhanden")
            else:
                self._qt_tray.setIcon(QIcon.fromTheme("security-high", QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)))
                self._qt_tray.setToolTip("LunaSecurity – Keine offenen Warnungen")
        if self.tray:
            self.tray.set_status(status)

    def _start_tray(self):
        try:
            self.tray=GtkStatusTray(lambda:self.bridge.show_window.emit(), lambda:self.bridge.quit_app.emit())
            self.log.append("GTK-System-Tray gestartet (Gtk.StatusIcon, wie in LunaKalender 1.4.0).")
        except Exception as exc:
            self.log.append(f"System-Tray nicht verfügbar: {exc}")

    @Slot()
    def quit_application(self):
        """Beendet die Anwendung vollständig, einschließlich beider Tray-Icons."""
        if getattr(self, "_quitting", False):
            return
        self._quitting = True
        if hasattr(self, "_realtime_log_timer"):
            self._realtime_log_timer.stop()
        if hasattr(self, "_qt_tray"):
            self._qt_tray.hide()
        if self.tray:
            tray, self.tray = self.tray, None
            tray.stop()
        QApplication.quit()

    @Slot()
    def show_from_tray(self):
        self.showNormal(); self.raise_(); self.activateWindow()

    def set_minimize_to_tray(self, enabled):
        """Speichert die Einstellung zum Weiterlaufen im Infobereich dauerhaft."""
        self.settings.setValue("minimize_to_tray", bool(enabled))
        self.settings.sync()

    def closeEvent(self,event):
        # Den aktuellen Zustand auch beim Schließen explizit sichern, damit die
        # Auswahl nach einem Neustart zuverlässig erhalten bleibt.
        if hasattr(self, "tray_check"):
            self.set_minimize_to_tray(self.tray_check.isChecked())
        if self.tray_check.isChecked() and self.tray:
            self.hide()
            event.ignore()
        else:
            event.accept()
            QApplication.quit()

    def start_scan(self, target=None, elevated=False, full_scan=False):
        if target is None:
            # Explizite Auswahl statt Ja/Nein-Frage: auf Linux/GTK-Desktops
            # kann der native Dialog sonst unsichtbar bleiben oder unklar wirken.
            chooser = QMessageBox(self)
            chooser.setWindowTitle(_ui_text("Scan-Ziel auswählen"))
            chooser.setText(_ui_text("Was möchtest du scannen?"))
            file_btn = chooser.addButton(_ui_text("Datei auswählen"), QMessageBox.ButtonRole.AcceptRole)
            folder_btn = chooser.addButton(_ui_text("Ordner auswählen"), QMessageBox.ButtonRole.ActionRole)
            chooser.addButton(QMessageBox.StandardButton.Cancel)
            chooser.exec()
            clicked = chooser.clickedButton()
            options = QFileDialog.Option.DontUseNativeDialog
            if clicked is file_btn:
                target, _ = _choose_file(self, _ui_text("Datei zum Scannen auswählen"), Path.home())
                if not target:
                    self.log.append("Dateiauswahl abgebrochen; kein Scan gestartet.")
                    return
            elif clicked is folder_btn:
                target = _choose_directory(self, _ui_text("Ordner zum Scannen auswählen"), Path.home())
                if not target:
                    self.log.append("Ordnerauswahl abgebrochen; kein Scan gestartet.")
                    return
            else:
                self.log.append("Scan abgebrochen; kein Scan-Ziel ausgewählt.")
                return
            if not target:
                return
        if isinstance(target, (list, tuple, set)):
            target = [str(Path(item).expanduser()) for item in target if Path(item).expanduser().exists()]
            if not target:
                QMessageBox.warning(self, "LunaSecurity", "Keines der ausgewählten Systemverzeichnisse ist vorhanden."); return
            target_label = ", ".join(target)
        else:
            target = str(Path(target).expanduser())
            if not Path(target).exists():
                QMessageBox.warning(self,"LunaSecurity",f"Pfad nicht gefunden: {target}"); return
            target_label = target

        # Ein neuer Scan ist eine neue Erkennungssitzung. Pfade, deren alte
        # Funde zuvor bereinigt wurden, dürfen bei einem erneuten Fund wieder
        # als Sicherheitsereignis gespeichert und gemeldet werden.
        self._resolved_detection_paths = set()
        self.scan_started_at = time.monotonic()

        # Klare Regel für Ordner-Scans:
        # Alles innerhalb des persönlichen Home-Verzeichnisses läuft ohne Root.
        # Jeder andere Ordner bietet Root-Rechte an – unabhängig davon, ob
        # einzelne Zugriffsrechte aktuell zufällig gesetzt sind.
        if not elevated:
            selected_targets = target if isinstance(target, (list, tuple, set)) else [target]
            home_path = Path.home().resolve()
            outside_home_directory = False
            for selected_path in selected_targets:
                selected = Path(selected_path)
                if not selected.is_dir():
                    continue
                try:
                    resolved = selected.resolve()
                    try:
                        is_inside_home = os.path.commonpath(
                            [str(home_path), str(resolved)]
                        ) == str(home_path)
                    except ValueError:
                        is_inside_home = False
                    if not is_inside_home:
                        outside_home_directory = True
                        break
                except OSError:
                    outside_home_directory = True
                    break

            if outside_home_directory:
                if not shutil.which("pkexec"):
                    QMessageBox.warning(
                        self,
                        "Administratorrechte erforderlich",
                        "Für Ordner außerhalb deines Home-Verzeichnisses werden "
                        "Root-Rechte benötigt. pkexec ist nicht verfügbar."
                    )
                    return
                answer = QMessageBox.question(
                    self,
                    "Root-Rechte für den Ordnerscan",
                    "Du hast einen Ordner außerhalb deines Home-Verzeichnisses ausgewählt.\\n\\n"
                    "Möchtest du den Scan mit Root-Rechten starten?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes,
                )
                if answer != QMessageBox.StandardButton.Yes:
                    self.log.append(
                        "Scan nicht gestartet: Root-Rechte für den ausgewählten Ordner wurden abgelehnt."
                    )
                    return
                elevated = True

        for scan_control in (self.scan_button, self.quick_scan_button, self.full_scan_button):
            scan_control.setEnabled(False)
        self.update_button.setEnabled(False); self.progress.hide(); self.cancel_scan_button.setEnabled(True)
        self.log.append(f"\nScan gestartet: {target_label}")
        profile = self.scan_profile.currentData() or "custom"
        if profile == "custom":
            # Eigenes Profil bedeutet ausschließlich die individuell gespeicherten
            # Einstellungen. Keine impliziten Standardwerte aus anderen Profilen.
            scan_options = {
                "detect_pua": self.detect_pua_check.isChecked(),
                "heuristics": self.heuristics_check.isChecked(),
                "hidden_files": self.hidden_files_check.isChecked(),
                "large_files": self.large_files_check.isChecked(),
                "recursive": self.recursive_check.isChecked(),
            }
        elif profile == "standard":
            scan_options = {"detect_pua": False, "heuristics": True, "hidden_files": False, "large_files": False, "recursive": True}
        elif profile == "high":
            scan_options = {"detect_pua": True, "heuristics": True, "hidden_files": True, "large_files": False, "recursive": True}
        elif profile == "maximum":
            scan_options = {"detect_pua": True, "heuristics": True, "hidden_files": True, "large_files": True, "recursive": True}
        else:
            # Unbekannte/alte Profilkennung sicher wie Eigenes Profil behandeln.
            scan_options = {
                "detect_pua": self.detect_pua_check.isChecked(),
                "heuristics": self.heuristics_check.isChecked(),
                "hidden_files": self.hidden_files_check.isChecked(),
                "large_files": self.large_files_check.isChecked(),
                "recursive": self.recursive_check.isChecked(),
            }
        # Auch die manuelle Datei-/Ordnerauswahl läuft durch denselben
        # Profil-Resolver wie Home- und vollständiger Systemscan.
        # Das eigene Profil liest die aktuell sichtbaren, gespeicherten Checkbox-Werte.
        profile_names = {
            "custom": "Eigenes Profil",
            "standard": "Standard (Empfohlen)",
            "high": "Hoher Schutz",
            "maximum": "Maximaler Schutz",
        }
        self.log.append(
            "Scanprofil: " + profile_names.get(profile, "Eigenes Profil")
            + " | PUP: " + ("An" if scan_options["detect_pua"] else "Aus")
            + " | Heuristik: " + ("An" if scan_options["heuristics"] else "Aus")
            + " | Versteckte Dateien: " + ("An" if scan_options["hidden_files"] else "Aus")
            + " | Große Dateien: " + ("An" if scan_options["large_files"] else "Aus")
            + " | Unterordner: " + ("An" if scan_options["recursive"] else "Aus")
        )
        # Kein Scanmodus überschreibt die Profiloptionen.
        # ClamOnAcc can log file accesses caused by an intentional manual scan.
        # Suppress those mirrored on-access lines; the scan report handles them.
        self._manual_scan_realtime_suppressed_until = time.monotonic() + 5
        self.scan_monitor = ClamScanMonitor(target_label, self, cancel_callback=self.cancel_scan, ignore_max_filesize=self.ignore_max_filesize_check.isChecked())
        self.scan_monitor.show()
        self.worker=ScanWorker(target, update_signatures=self.auto_update_check.isChecked(), scan_options=scan_options, elevated=elevated)
        self.worker.progress_batch.connect(self.scan_monitor.add_lines)
        self.worker.total_files.connect(self.scan_monitor.set_total_files)
        self.worker.result.connect(self.scan_finished)
        self.worker.start()

    def scan_system_areas(self):
        """Scannt wichtige echte Systemverzeichnisse, ohne virtuelle Dateisysteme."""
        if self.worker and self.worker.isRunning():
            QMessageBox.information(self, "LunaSecurity", "Es läuft bereits eine Sicherheitsaufgabe.")
            return
        candidates = ["/etc", "/usr/bin", "/usr/sbin", "/usr/lib", "/boot",
                      "/opt", "/var/lib", "/var/log"]
        targets = []
        seen = set()
        for raw in candidates:
            path = Path(raw)
            try:
                if path.is_dir() and not path.is_symlink():
                    resolved = str(path.resolve())
                    if resolved not in seen:
                        seen.add(resolved)
                        targets.append(resolved)
            except OSError:
                continue
        if not targets:
            QMessageBox.warning(self, "LunaSecurity", "Keine erreichbaren Systemverzeichnisse für den Scan gefunden.")
            return
        self.start_scan(targets, elevated=True)

    def run_lynis_audit(self, worker=None):
        executable = shutil.which("lynis")
        if not executable:
            return "Lynis ist nicht installiert. Installation: sudo apt install lynis"
        args = [executable, "audit", "system", "--quick", "--no-colors"]
        if worker is not None:
            return worker.run_command(args, 900)
        result = subprocess.run(args, capture_output=True, text=True, timeout=900)
        return (result.stdout + "\\n" + result.stderr).strip()

    def read_fail2ban_status(self, worker=None):
        if not shutil.which("fail2ban-client"):
            return "fail2ban-client ist nicht installiert. Installation: sudo apt install fail2ban"
        pkexec = shutil.which("pkexec")
        helper = "/usr/lib/lunasecurity/fail2ban-status-helper"
        if not os.path.isfile(helper):
            helper = str(Path(__file__).resolve().parent.parent / "scripts" / "fail2ban-status-helper")
        if not pkexec:
            return "Für die fail2ban-Statusabfrage wird pkexec benötigt (policykit-1)."
        if not os.path.isfile(helper):
            return "Der LunaSecurity-Helfer für fail2ban fehlt."
        if worker is not None:
            return _ui_text(worker.run_command([pkexec, helper], 35))
        result = subprocess.run([pkexec, helper], capture_output=True, text=True, timeout=35)
        return (result.stdout + "\\n" + result.stderr).strip()

    def refresh_security_dashboard(self):
        checks=[]
        for label, command in (("ClamAV", ["systemctl", "is-active", "clamav-daemon"]),
                               ("LunaSecurity-Echtzeitschutz", ["systemctl", "is-active", "lunasecurity-realtime.service"]),
                               ("fail2ban", ["systemctl", "is-active", "fail2ban"])):
            try:
                result=subprocess.run(command, capture_output=True, text=True, timeout=5)
                state=(result.stdout or result.stderr).strip() or "unbekannt"
            except Exception as exc: state=str(exc)
            checks.append(f"{label}: {state}")
        self.advanced_output.setPlainText("SICHERHEITSSTATUS-DASHBOARD\n\n" + "\n".join(checks) +
            "\n\nHinweis: Ein aktiver Dienst ist kein Nachweis für ein sauberes System. Starte bei Bedarf die jeweiligen Prüfungen.")

    def _security_report_html(self):
        from datetime import datetime
        import html
        # Der Bericht bildet bewusst den Inhalt des sichtbaren Haupt-Protokollfensters ab.
        # Dadurch werden genau die Meldungen exportiert, die der Benutzer dort sieht.
        log_text = self.log.toPlainText() if hasattr(self, "log") else ""
        escaped_log = html.escape(log_text)
        return ("<!doctype html><html lang='de'><meta charset='utf-8'>"
                "<title>LunaSecurity – Prüfbericht</title>"
                "<style>@page{size:A4;margin:18mm}body{font:10pt sans-serif;margin:0;color:#202638}"
                "h1{font-size:18pt;color:#344a9a;margin-bottom:8mm}h2{font-size:13pt;margin-top:6mm}"
                "pre{white-space:pre-wrap;overflow-wrap:anywhere;word-wrap:break-word;"
                "background:#f2f4fa;padding:5mm;border:1px solid #ccd2e0;"
                "font:9pt 'DejaVu Sans Mono',monospace;line-height:1.35}</style>"
                "<h1>LunaSecurity – Prüfbericht</h1><p>Erstellt: "
                + html.escape(datetime.now().astimezone().isoformat(timespec="seconds"))
                + "</p><h2>Inhalt des Protokollfensters</h2><pre>"
                + escaped_log + "</pre></html>")

    def export_security_report_html(self):
        path,_=QFileDialog.getSaveFileName(self,"HTML-Sicherheitsbericht speichern",str(Path.home()/"LunaSecurity-Bericht.html"),"HTML (*.html)")
        if path:
            Path(path).write_text(self._security_report_html(),encoding="utf-8")
            QMessageBox.information(self,"Bericht gespeichert",f"HTML-Bericht gespeichert:\n{path}")

    def export_security_report_pdf(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "PDF-Sicherheitsbericht speichern",
            str(Path.home() / "LunaSecurity-Bericht.pdf"), "PDF (*.pdf)"
        )
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"
        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            printer.setPageMargins(QMarginsF(18, 18, 18, 18), QPageLayout.Unit.Millimeter)
            printer.setOutputFileName(path)
            if not printer.isValid():
                raise RuntimeError("Der PDF-Drucker konnte nicht initialisiert werden.")

            document = QTextDocument()
            document.setDefaultFont(QFont("DejaVu Sans Mono", 9))
            text_option = QTextOption()
            text_option.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
            document.setDefaultTextOption(text_option)
            document.setHtml(self._security_report_html())
            printable = printer.pageLayout().paintRect(QPageLayout.Unit.Point)
            document.setPageSize(printable.size())
            document.print_(printer)

            output = Path(path)
            if printer.printerState() == QPrinter.PrinterState.Error or not output.is_file() or output.stat().st_size == 0:
                raise RuntimeError("Qt konnte keine PDF-Datei schreiben. Bitte prüfe den Zielordner und seine Schreibrechte.")
            QMessageBox.information(
                self, "Bericht gespeichert",
                f"PDF-Bericht wurde erfolgreich gespeichert:\n{path}"
            )
        except Exception as exc:
            QMessageBox.critical(
                self, "PDF-Bericht konnte nicht gespeichert werden",
                f"Beim Erstellen der PDF-Datei ist ein Fehler aufgetreten:\n{exc}"
            )

    def _start_realtime_worker(self, action):
        if self.realtime_worker and self.realtime_worker.isRunning():
            return
        worker = RealtimeWorker(action)
        self.realtime_worker = worker
        _background_workers.add(worker)
        worker.result.connect(self.realtime_finished)
        worker.finished.connect(lambda w=worker: _background_workers.discard(w))
        self._realtime_pending_action = action
        self.realtime_button.setEnabled(False)
        if action == "status":
            self.realtime_status.setText(_ui_text("Echtzeitschutz: Status wird geprüft …"))
        else:
            self.realtime_status.setText(_ui_text("Echtzeitschutz: Hintergrundauftrag läuft …"))
            self.log.append("\nEchtzeitschutz wird im Hintergrund " + ("aktiviert …" if action == "enable" else "deaktiviert …"))
        worker.start()

    def refresh_realtime_status(self):
        self._start_realtime_worker("status")

    def start_virustotal_check(self):
        api_key = self.settings.value("virustotal_api_key", "", type=str).strip()
        if not api_key:
            QMessageBox.warning(self, "VirusTotal", "Bitte trage zuerst unter Einstellungen → VirusTotal – API deinen API-Schlüssel ein.")
            return
        file_path, _ = QFileDialog.getOpenFileName(self, "Datei für VirusTotal auswählen", str(Path.home()), "Alle Dateien (*)")
        if not file_path:
            return
        self._start_virustotal_worker(file_path, api_key, upload_unknown=False)

    def _start_virustotal_worker(self, file_path, api_key, upload_unknown=False):
        self.virustotal_button.setEnabled(False)
        self.virustotal_button.setText("VirusTotal lädt hoch …" if upload_unknown else "VirusTotal prüft …")
        self.virustotal_worker = VirusTotalLookupWorker(
            file_path, api_key, self, upload_unknown=upload_unknown
        )
        self.virustotal_worker.finished_report.connect(self.virustotal_check_finished)
        self.virustotal_worker.start()

    def virustotal_check_finished(self, result):
        self.virustotal_button.setEnabled(True)
        self.virustotal_button.setText("🌐  VirusTotal-Check")
        status = result.get("status")
        if status == "unknown":
            path = result.get("path", "")
            size = int(result.get("size", 0))
            size_text = f"{size / (1024 * 1024):.2f} MB"
            answer = QMessageBox.question(
                self, "VirusTotal – Datei unbekannt",
                "VirusTotal kennt diese Datei noch nicht.\n\n"
                f"Datei: {os.path.basename(path)}\nGröße: {size_text}\n"
                f"SHA-256: {result.get('hash')}\n\n"
                "Möchtest du die Datei jetzt zur Analyse an VirusTotal hochladen?\n\n"
                "WICHTIG: Die Datei wird an VirusTotal übertragen und kann in den "
                "VirusTotal-Datensatz aufgenommen und für andere Nutzer zugänglich werden. "
                "Keine vertraulichen oder persönlichen Dateien hochladen.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer == QMessageBox.StandardButton.Yes:
                if size > 32 * 1024 * 1024:
                    QMessageBox.warning(
                        self, "VirusTotal – Datei zu groß",
                        "Derzeit unterstützt der direkte Upload Dateien bis 32 MB. "
                        "Diese Datei ist größer und wurde nicht übertragen."
                    )
                else:
                    api_key = self.settings.value("virustotal_api_key", "", type=str).strip()
                    self._start_virustotal_worker(path, api_key, upload_unknown=True)
            else:
                QMessageBox.information(
                    self, "VirusTotal – Upload übersprungen",
                    "Die Datei blieb unverändert auf deinem Rechner. Es wurde nur der SHA-256-Hash abgefragt."
                )
        elif status == "pending":
            QMessageBox.information(
                self, "VirusTotal – Analyse läuft noch",
                "Die Datei wurde hochgeladen. VirusTotal hat die Analyse noch nicht abgeschlossen.\n\n"
                f"SHA-256: {result.get('hash')}\nAnalyse-ID: {result.get('analysis_id')}\n\n"
                "Du kannst den Bericht später auf VirusTotal öffnen."
            )
        elif status == "error":
            QMessageBox.warning(self, "VirusTotal – Fehler", result.get("message", "Unbekannter Fehler"))
        else:
            malicious = result.get("malicious", 0)
            suspicious = result.get("suspicious", 0)
            verdict = "Keine Erkennung gemeldet." if not malicious and not suspicious else "Achtung: VirusTotal meldet mögliche Erkennungen."
            box = QMessageBox(self)
            box.setWindowTitle("VirusTotal – Prüfergebnis")
            box.setIcon(QMessageBox.Icon.Warning if malicious or suspicious else QMessageBox.Icon.Information)
            box.setText(verdict)
            detections = result.get("detections", [])
            detail_lines = [
                f"Erkennungen: {malicious}",
                f"Verdächtig: {suspicious}",
                f"Nicht erkannt: {result.get('undetected', 0)}",
                f"Unauffällig: {result.get('harmless', 0)}",
                f"Ausgewertete Anbieter: {result.get('total', 0)}",
            ]
            if detections:
                detail_lines.append("\\nGemeldete Anbieter:")
                for item in detections:
                    detail_lines.append(
                        f"• {item.get('vendor')}: {item.get('result')} ({item.get('category')})"
                    )
            detail_lines.extend([
                f"\\nDatei: {result.get('path', '')}",
                f"SHA-256: {result.get('hash')}",
                "",
                "Datei wurde hochgeladen." if result.get("uploaded") else "Es wurde nur der Hash abgefragt; die Datei wurde nicht hochgeladen.",
                "VirusTotal kann abgefragte Indikatoren und hochgeladene Dateien in seinen Datensatz aufnehmen."
            ])
            box.setInformativeText("\\n".join(detail_lines))
            open_report = box.addButton("Bericht auf VirusTotal öffnen", QMessageBox.ButtonRole.ActionRole)
            box.addButton(QMessageBox.StandardButton.Close)
            box.exec()
            if box.clickedButton() is open_report:
                import webbrowser
                webbrowser.open(result.get("permalink", "https://www.virustotal.com/"))
        self.virustotal_worker = None

    def toggle_realtime(self):
        if self.realtime_worker and self.realtime_worker.isRunning():
            return
        if not getattr(self, "_realtime_status_known", False):
            self.refresh_realtime_status()
            return
        self._start_realtime_worker("disable" if self._realtime_active else "enable")

    @Slot(str, bool, bool)
    def realtime_finished(self, message, active, success):
        self._realtime_pending_action = None
        self._realtime_status_known = bool(success)
        self._realtime_active = bool(active) if success else False
        self._realtime_success = bool(success)
        status_label = "Aktiv" if active else ("Aus" if success else "Status unklar")
        self.realtime_status.setText(_ui_text("Echtzeitschutz:") + " " + _ui_text(status_label))
        if hasattr(self, "realtime_title_label"):
            self.realtime_title_label.setText("Echtzeitschutz: " + status_label)
            state_color = "#42e987" if active and success else "#ff6978" if success else "#e0b45a"
            self.realtime_title_label.setStyleSheet("font-size:13pt;font-weight:700;color:" + state_color)
        if hasattr(self, "realtime_icon_label"):
            self.realtime_icon_label.setStyleSheet("font-size:27pt;color:" + ("#42e987" if active and success else "#ff6978" if success else "#e0b45a"))
        if success:
            self.realtime_indicator.setStyleSheet(
                "font-size:22px;font-weight:900;color:" + ("#28e66b" if active else "#ff3b45") + ";padding-left:5px;padding-right:5px;"
            )
            self.realtime_indicator.setToolTip(_ui_text("Echtzeitschutz ist aktiv" if active else "Echtzeitschutz ist ausgeschaltet"))
        else:
            self.realtime_indicator.setStyleSheet("font-size:22px;font-weight:900;color:#e0a52b;padding-left:5px;padding-right:5px;")
            self.realtime_indicator.setToolTip(_ui_text("Status des Echtzeitschutzes konnte nicht ermittelt werden"))
        # Anzeigeelemente gemeinsam aktualisieren, damit kein alter grüner Statuspunkt
        # neben einer Schaltfläche mit gegenteiliger Aktion stehen bleibt.
        self.realtime_button.setText(_ui_text("Echtzeitschutz deaktivieren" if active else "Echtzeitschutz aktivieren"))
        self.realtime_button.setEnabled(True)
        if message and message != "Status geprüft.":
            self.log.append(message)
        if not success:
            self.log.append("Hinweis: Der Dienststatus konnte nicht sicher bestätigt werden.")

    def _suppress_quarantine_move_alert(self, path):
        """Unterdrückt den ClamOnAcc-Event, der allein durch das Wegverschieben entsteht."""
        normalized = str(Path(path).expanduser().resolve(strict=False))
        if not hasattr(self, "_quarantine_move_suppressed_paths"):
            self._quarantine_move_suppressed_paths = set()
        self._quarantine_move_suppressed_paths.add(normalized)
        QTimer.singleShot(
            10000,
            lambda value=normalized: self._quarantine_move_suppressed_paths.discard(value)
            if hasattr(self, "_quarantine_move_suppressed_paths") else None
        )

    def show_realtime_detection_window(self, output):
        """Zeigt neue Echtzeitfunde im gemeinsamen Prüfungsfenster."""
        title = "Echtzeitschutz – Bedrohung erkannt"
        dialog = ModuleProgressDialog(title, lambda: None, self)
        dialog.setWindowTitle(_ui_text("LunaSecurity – Echtzeitschutz: Bedrohung erkannt"))
        dialog.findChild(QLabel).setText(_ui_text("Der Echtzeitschutz hat eine Bedrohung gefunden"))
        detected_path = None
        for line in str(output).splitlines():
            if line.strip().endswith("FOUND") or " FOUND " in line:
                detected_path = sec.detection_path(line.strip())
                if detected_path:
                    break
        if detected_path:
            dialog.status.setText(_ui_text("Bedrohung erkannt – Datei:") + " " + detected_path)
        else:
            dialog.status.setText(_ui_text("Bedrohung erkannt – Details stehen im Prüfbericht."))
        dialog.finish(title, str(output))
        dialog.cancel_button.hide()
        dialog.close_button.setEnabled(True)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        if not hasattr(self, "_realtime_detection_dialogs"):
            self._realtime_detection_dialogs = []
        self._realtime_detection_dialogs.append(dialog)
        dialog.finished.connect(
            lambda _result, item=dialog:
            self._realtime_detection_dialogs.remove(item)
            if item in self._realtime_detection_dialogs else None
        )

    def report_detections(self, output, source="Manueller Scan"):
        """Persist ClamAV FOUND lines, ignoring paths just resolved by the user."""
        added = 0
        if not hasattr(self, "_resolved_detection_paths"):
            self._resolved_detection_paths = set()
        for line in str(output).splitlines():
            line = line.strip()
            if not line or not (line.endswith("FOUND") or " FOUND " in line):
                continue
            if (self.settings.value("scan_ignore_max_filesize", True, type=bool)
                    and "HEURISTICS.LIMITS.EXCEEDED.MAXFILESIZE" in line.upper()):
                continue
            path = sec.detection_path(line)
            if not path:
                continue
            normalized_path = str(Path(path).expanduser().resolve(strict=False))
            suppressed_paths = getattr(self, "_quarantine_move_suppressed_paths", set())
            if normalized_path in suppressed_paths:
                # Suppress only the old file-move event (the source no longer
                # exists). If a file is created again at the same path, it is
                # a fresh object and must be scanned/reported immediately.
                if not Path(path).expanduser().exists():
                    continue
                suppressed_paths.discard(normalized_path)
            # ClamOnAcc can still emit events for moves into the private
            # quarantine even when its config exclusion is active. Never treat
            # the quarantine storage itself as a user-facing detection.
            try:
                Path(path).expanduser().resolve(strict=False).relative_to(
                    sec.QUARANTINE.expanduser().resolve(strict=False)
                )
                continue
            except ValueError:
                pass
            # A real-time log line can arrive just after the file was moved.
            # Do not recreate the just-resolved finding in the same session.
            if (source != "Echtzeitschutz" and
                    str(Path(path).expanduser().resolve(strict=False)) in self._resolved_detection_paths):
                continue
            # Avoid adding the same path/signature repeatedly on each refresh.
            existing = self._read_security_events()
            if any(sec.detection_path(str(event.get("detail", ""))) == path and
                   str(event.get("detail", "")) == line for event in existing):
                continue
            record_security_event(source, line)
            added += 1
        if added:
            self.log.append(f"\n{added} erkannte Datei(en) im Sicherheitsereignis-Protokoll gespeichert.")
            if source == "Echtzeitschutz":
                # Echtzeitfunde ebenfalls im großen Haupt-Protokollfeld mit
                # vollständigem Pfad anzeigen – genauso wie manuelle Scanfunde.
                realtime_paths = []
                for found_line in str(output).splitlines():
                    found_line = found_line.strip()
                    if found_line.endswith("FOUND") or " FOUND " in found_line:
                        found_path = sec.detection_path(found_line)
                        if found_path and found_path not in realtime_paths:
                            realtime_paths.append(found_path)
                if realtime_paths:
                    self.log.append("Echtzeitschutz – gefundene Datei(en):")
                    for found_path in realtime_paths:
                        self.log.append(f"Datei: {found_path}")
                self.show_realtime_detection_window(str(output))
            if hasattr(self, "_qt_tray") and self._qt_tray.isVisible():
                self._qt_tray.showMessage("LunaSecurity – Bedrohung erkannt", f"{added} Fund/Funde: {source}", QSystemTrayIcon.MessageIcon.Warning, 10000)
            if hasattr(self, "sound_enabled") and self.sound_enabled.isChecked():
                self.play_alarm()
        self.load_security_events()
        return added

    def _read_security_events(self):
        try:
            data = json.loads(EVENTS_FILE.read_text()) if EVENTS_FILE.exists() else []
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def load_security_events(self):
        events = self._read_security_events()
        if hasattr(self, "_qt_tray"):
            self._sync_tray_status()
        self.events_view.clear()
        for item in events:
            detail = str(item.get("detail", ""))
            path = sec.detection_path(detail)
            label = f'{item.get("time", "")} | {item.get("kind", "Fund")}\n{detail}'
            if path:
                label += f"\nDatei: {path}"
            entry = QListWidgetItem(label)
            entry.setData(256, {"path": path, "detail": detail})
            # Keep the complete record so only this exact event is removed
            # after a successful quarantine/delete action.
            entry.setData(257, dict(item))
            self.events_view.addItem(entry)
        if events:
            # Keep the warning banner tied to the persisted event list, not to
            # a translated tab caption or a cached UI state.
            count = len(events)
            if APP_LANGUAGE == "en":
                banner_text = f"⚠ {count} saved security event(s) – details under Virus protection"
            else:
                banner_text = f"⚠ {count} gespeicherte Sicherheitsereignisse – Details unter Virenschutz"
            self.alert_banner.setText(banner_text)
            self.alert_banner.setVisible(True)
            self.alert_banner.raise_()
        else:
            self.events_view.addItem(_ui_text("Noch keine erkannten Bedrohungen gespeichert."))
            self.alert_banner.setVisible(False)

    def _selected_detection_path(self):
        item = self.events_view.currentItem()
        if not item:
            return None
        data = item.data(256) or {}
        return data.get("path")

    def _remove_processed_security_event(self, event_record, path=None):
        """Remove the processed file's events, but preserve every other file's findings."""
        if not isinstance(event_record, dict):
            return False
        if not hasattr(self, "_resolved_detection_paths"):
            self._resolved_detection_paths = set()
        target_path = str(Path(path).expanduser().resolve(strict=False)) if path else None
        if target_path:
            self._resolved_detection_paths.add(target_path)
        events = self._read_security_events()
        kept = []
        removed = False
        for event in events:
            same_record = event == event_record
            event_path = sec.detection_path(str(event.get("detail", ""))) if isinstance(event, dict) else None
            same_file = bool(target_path and event_path and str(Path(event_path).expanduser().resolve(strict=False)) == target_path)
            if same_record or same_file:
                removed = True
            else:
                kept.append(event)
        if removed:
            EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
            temp_file = EVENTS_FILE.with_suffix('.json.tmp')
            temp_file.write_text(json.dumps(kept, ensure_ascii=False, indent=2))
            try:
                temp_file.chmod(0o600)
            except OSError:
                pass
            temp_file.replace(EVENTS_FILE)
        return removed

    def quarantine_detected_event(self):
        selected_item = self.events_view.currentItem()
        event_record = selected_item.data(257) if selected_item else None
        path = self._selected_detection_path()
        if not path:
            QMessageBox.information(self, "LunaSecurity", "Bitte zuerst einen Fund mit erkannter Dateiangabe auswählen.")
            return
        answer = QMessageBox.warning(self, "In Quarantäne verschieben",
            f"Die erkannte Datei wird verschoben und isoliert:\\n\\n{path}\\n\\nFortfahren?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        try:
            self._suppress_quarantine_move_alert(path)
            self.log.append(sec.quarantine_file(path))
            self._remove_processed_security_event(event_record, path)
            self.refresh_quarantine()
            self.load_security_events()
            self.tabs.setCurrentIndex(self.quarantine_tab_index)
        except Exception as exc:
            QMessageBox.critical(self, "Quarantäne fehlgeschlagen", str(exc))

    def delete_detected_event(self):
        selected_item = self.events_view.currentItem()
        event_record = selected_item.data(257) if selected_item else None
        path = self._selected_detection_path()
        if not path:
            QMessageBox.information(self, "LunaSecurity", "Bitte zuerst einen Fund mit erkannter Dateiangabe auswählen.")
            return
        answer = QMessageBox.warning(self, "Datei endgültig löschen",
            f"Diese Datei wird unwiderruflich gelöscht:\\n\\n{path}\\n\\nFortfahren?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        try:
            sec.delete_detected_file(path)
            self.log.append(f"Datei gelöscht: {path}")
            self._remove_processed_security_event(event_record, path)
            self.load_security_events()
        except Exception as exc:
            QMessageBox.critical(self, "Löschen fehlgeschlagen", str(exc))

    def clear_security_events(self):
        try:
            EVENTS_FILE.unlink(missing_ok=True)
        except OSError as exc:
            QMessageBox.warning(self, "LunaSecurity", f"Protokoll konnte nicht geleert werden: {exc}")
            return
        self.load_security_events()
        self._sync_tray_status()

    def refresh_quarantine(self):
        rows = sec.quarantine_entries()
        self.quarantine_table.setRowCount(len(rows))
        for row, item in enumerate(rows):
            values = [item["original"], item["sha256"], item["created_text"], item["stored"]]
            for col, value in enumerate(values):
                self.quarantine_table.setItem(row, col, QTableWidgetItem(str(value)))
            self.quarantine_table.item(row, 0).setData(256, item["id"])
        self.quarantine_table.resizeRowsToContents()

    def _selected_quarantine_id(self):
        rows = self.quarantine_table.selectionModel().selectedRows()
        if not rows:
            return None
        item = self.quarantine_table.item(rows[0].row(), 0)
        return item.data(256) if item else None

    def restore_quarantine_selected(self):
        entry_id = self._selected_quarantine_id()
        if entry_id is None:
            QMessageBox.information(self, "Quarantäne", "Bitte zuerst eine Datei auswählen.")
            return
        if self.module_worker and self.module_worker.isRunning():
            QMessageBox.information(self, "LunaSecurity", "Bitte zuerst die laufende Sicherheitsprüfung abschließen.")
            return
        try:
            # Consume any pending notification from the earlier move into
            # quarantine while its source path is still suppressed.
            self.check_realtime_log()
            row, _stored = sec._quarantine_record(entry_id)
            restored_path = str(Path(row[1]).expanduser().resolve(strict=False))
            result = sec.restore_quarantined(entry_id)
            # The quarantine-move suppression must not hide the new file
            # creation at the original path. Remove it immediately after the
            # restore; the pending move event was consumed above.
            getattr(self, "_quarantine_move_suppressed_paths", set()).discard(restored_path)
            self.log.append(result)
            self.refresh_quarantine()
            # File-creation events are not guaranteed to be emitted by
            # clamonacc on every filesystem/backend. Explicitly hand the restored
            # path to the active clamd daemon so restoration is checked at once.
            self._scan_restored_file_realtime(restored_path)
        except Exception as exc:
            QMessageBox.critical(self, "Wiederherstellen fehlgeschlagen", str(exc))

    def _scan_restored_file_realtime(self, path):
        worker = RestoredFileScanWorker(path)
        self._restored_file_scan_workers = getattr(self, "_restored_file_scan_workers", set())
        self._restored_file_scan_workers.add(worker)
        _background_workers.add(worker)
        worker.result.connect(self._restored_file_scan_finished)
        worker.finished.connect(lambda w=worker: self._restored_file_scan_workers.discard(w))
        worker.finished.connect(lambda w=worker: _background_workers.discard(w))
        self.log.append("Echtzeitschutz: Wiederhergestellte Datei wird sofort erneut geprüft …")
        worker.start()

    @Slot(str, str, int)
    def _restored_file_scan_finished(self, path, output, returncode):
        if " FOUND" in str(output).upper() or str(output).strip().endswith("FOUND"):
            self.report_detections(output, source="Echtzeitschutz")
            self.log.append("Echtzeitschutz: Bedrohung nach Wiederherstellung erneut erkannt.")
        elif returncode == 0:
            self.log.append(f"Echtzeitschutz: Wiederhergestellte Datei geprüft – keine Bedrohung: {path}")
        else:
            self.log.append("Echtzeitschutz: Prüfung der wiederhergestellten Datei nicht möglich. " + (output or f"ClamAV-Exit-Code {returncode}"))

    def delete_quarantine_selected(self):
        entry_id = self._selected_quarantine_id()
        if entry_id is None:
            QMessageBox.information(self, "Quarantäne", "Bitte zuerst eine Datei auswählen.")
            return
        answer = QMessageBox.warning(self, "Quarantäne-Datei endgültig löschen",
            "Die ausgewählte isolierte Datei wird unwiderruflich gelöscht. Fortfahren?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        try:
            self.log.append(sec.delete_quarantined(entry_id))
            self.refresh_quarantine()
        except Exception as exc:
            QMessageBox.critical(self, "Löschen fehlgeschlagen", str(exc))

    def check_realtime_log(self):
        try:
            if not self._realtime_log_path.exists():
                return
            size = self._realtime_log_path.stat().st_size
            if size < self._realtime_log_offset:
                self._realtime_log_offset = 0
            if size == self._realtime_log_offset:
                return
            # Den Logzeiger erst nach der Verarbeitung weiterschieben. Während
            # eines manuellen Scans dürfen gespiegelt auftauchende OnAccess-Zeilen
            # nicht als Echtzeit-Popup erscheinen; sie bleiben aber im Log und
            # werden danach verarbeitet. Bereits vom manuellen Scan gespeicherte
            # Funde werden durch report_detections() dedupliziert.
            start_offset = self._realtime_log_offset
            with self._realtime_log_path.open("r", errors="replace") as handle:
                handle.seek(start_offset)
                chunk = handle.read()
                end_offset = handle.tell()
            scan_running = bool(self.worker and self.worker.isRunning())
            suppress_until = getattr(self, "_manual_scan_realtime_suppressed_until", 0)
            if scan_running or time.monotonic() < suppress_until:
                return
            self._realtime_log_offset = end_offset
            for line in chunk.splitlines():
                if " FOUND" in line or line.strip().endswith("FOUND"):
                    self.report_detections(line, source="Echtzeitschutz")
        except OSError:
            return

    def update_signatures_now(self):
        if self.worker and self.worker.isRunning():
            QMessageBox.information(self, "LunaSecurity", "Es läuft bereits eine Sicherheitsaufgabe.")
            return
        # freshclam läuft bereits in einem QThread. Nur den Aktualisieren-Knopf
        # sperren; die restliche Oberfläche bleibt sichtbar und bedienbar.
        self.update_button.setEnabled(False)
        self.progress.hide()
        self.log.append("\nSignaturaktualisierung im Hintergrund gestartet …")
        self.worker = ScanWorker(update_only=True)
        self.worker.result.connect(self.signature_update_finished)
        self.worker.start()

    def signature_update_finished(self, text):
        self.progress.hide()
        self.update_button.setEnabled(True)
        self.log.append(text)
        self.log.append("Signaturaktualisierung im Hintergrund beendet.")
        self.signature_version_label.setText(_ui_text("Installierte Virensignaturen:") + " " + signature_database_versions())
        # Kein modaler Ergebnisdialog: Status und vollständige Ausgabe stehen im Protokoll.

    def _repair_backup_dir(self):
        path = Path.home() / ".local" / "share" / "LunaSecurity" / "repair-backups" / "autostart"
        path.mkdir(parents=True, exist_ok=True)
        try: path.chmod(0o700)
        except OSError: pass
        return path

    def refresh_repair_autostart(self):
        if not hasattr(self, "repair_autostart_list"): return
        self.repair_autostart_list.clear()
        source = Path.home() / ".config" / "autostart"
        source.mkdir(parents=True, exist_ok=True)
        for entry in sorted(source.glob("*.desktop")):
            if entry.is_file() and not entry.is_symlink():
                item = QListWidgetItem(entry.name); item.setData(Qt.ItemDataRole.UserRole, str(entry))
                self.repair_autostart_list.addItem(item)
        if self.repair_autostart_list.count() == 0:
            self.repair_autostart_list.addItem("Keine Benutzer-Autostart-Dateien gefunden")
            self.repair_autostart_list.item(0).setFlags(Qt.ItemFlag.NoItemFlags)

    def disable_selected_autostart(self):
        item = self.repair_autostart_list.currentItem()
        if not item or not item.data(Qt.ItemDataRole.UserRole): return
        source = Path(item.data(Qt.ItemDataRole.UserRole))
        backup = self._repair_backup_dir() / source.name
        if backup.exists():
            QMessageBox.warning(self, "Reparatur", f"Eine Sicherung mit diesem Namen existiert bereits:\n{backup}")
            return
        answer = QMessageBox.question(self, "Autostart deaktivieren", f"Dieser Eintrag wird aus dem Autostart entfernt, aber sicher verschoben und kann wiederhergestellt werden:\n\n{source}\n\nFortfahren?")
        if answer != QMessageBox.StandardButton.Yes: return
        try:
            shutil.move(str(source), str(backup))
            record_security_event("Reparatur-Sicherung", f"Autostart deaktiviert; Sicherung: {backup}; Original: {source}")
            self.repair_output.append(f"Gesichert und deaktiviert:\n{source}\nSicherung: {backup}")
        except OSError as exc:
            QMessageBox.critical(self, "Reparatur fehlgeschlagen", str(exc))
        self.refresh_repair_autostart()

    def restore_autostart_entry(self):
        backups = sorted(self._repair_backup_dir().glob("*.desktop"))
        if not backups:
            QMessageBox.information(self, "Wiederherstellung", "Keine gesicherten Autostart-Einträge vorhanden.")
            return
        choices = [p.name for p in backups]
        selected, ok = QInputDialog.getItem(self, "Wiederherstellen", "Gesicherten Eintrag auswählen:", choices, 0, False)
        if not ok or not selected: return
        backup = self._repair_backup_dir() / selected
        target = Path.home() / ".config" / "autostart" / selected
        if target.exists():
            QMessageBox.warning(self, "Wiederherstellung", f"Am ursprünglichen Ort existiert bereits eine Datei. Nichts wurde überschrieben:\n{target}")
            return
        if QMessageBox.question(self, "Wiederherstellung bestätigen", f"Eintrag wiederherstellen?\n\n{backup}\n→ {target}") != QMessageBox.StandardButton.Yes: return
        try:
            target.parent.mkdir(parents=True, exist_ok=True); shutil.move(str(backup), str(target))
            record_security_event("Reparatur-Rollback", f"Autostart wiederhergestellt: {target}")
            self.repair_output.append(f"Wiederhergestellt: {target}")
        except OSError as exc: QMessageBox.critical(self, "Wiederherstellung fehlgeschlagen", str(exc))
        self.refresh_repair_autostart()

    def verify_installed_packages(self):
        if self.package_verify_worker is not None and self.package_verify_worker.isRunning():
            return
        self.repair_package_combo.clear()
        self.verify_package_btn.setEnabled(False)
        self.verify_package_btn.setText("Paketprüfung läuft …")
        self.verify_package_progress.show()
        self.verify_package_progress.setRange(0, 0)
        self.cancel_package_verify_btn.show(); self.cancel_package_verify_btn.setEnabled(True)
        self.package_verify_started = time.monotonic()
        self.verify_package_status.setText("Starte Prüfung …")
        self.package_verify_timer.start()
        self.repair_output.append("Paketprüfung gestartet. Die Oberfläche bleibt bedienbar. Die Paketzuordnung wird aus der lokalen dpkg-Dateiliste aufgebaut.")
        worker = PackageVerifyWorker(self)
        worker.status.connect(self.verify_package_status.setText)
        worker.completed.connect(self.package_verification_finished)
        worker.finished.connect(worker.deleteLater)
        self.package_verify_worker = worker
        worker.start()

    def update_package_verify_elapsed(self):
        if self.package_verify_started:
            elapsed = max(0, int(time.monotonic() - self.package_verify_started))
            self.verify_package_status.setText(f"{self.verify_package_status.text().split(' | ')[0]} | Laufzeit {elapsed // 60:02d}:{elapsed % 60:02d}")

    def cancel_package_verification(self):
        worker = self.package_verify_worker
        if worker is not None and worker.isRunning():
            self.cancel_package_verify_btn.setEnabled(False)
            self.verify_package_status.setText("Abbruch wird ausgeführt …")
            worker.cancel()

    @Slot(str, object, str)
    def package_verification_finished(self, output, packages, error):
        self.package_verify_timer.stop()
        elapsed = max(0, int(time.monotonic() - self.package_verify_started)) if self.package_verify_started else 0
        self.package_verify_started = 0.0
        self.verify_package_progress.hide()
        self.verify_package_btn.setEnabled(True)
        self.verify_package_btn.setText("Installierte Pakete auf Dateiänderungen prüfen")
        self.cancel_package_verify_btn.hide(); self.cancel_package_verify_btn.setEnabled(True)
        self.verify_package_status.setText(f"Letzte Prüfung beendet nach {elapsed // 60:02d}:{elapsed % 60:02d} min")
        self.package_verify_worker = None
        if error:
            self.repair_output.append(error)
        self.repair_package_combo.clear()
        for pkg, count in sorted(packages.items()):
            self.repair_package_combo.addItem(f"{pkg} ({count} Abweichung(en))", pkg)
        self.repair_output.append("Debian-Paketprüfung (nur lesend):\n" + (output or "Keine Abweichungen von dpkg gemeldet."))
        self.repair_output.append("dpkg --verify vergleicht vorhandene Prüfsummen-Metadaten; dies ist kein Malware-Nachweis. Die Paketzuordnung erfolgt gesammelt über /var/lib/dpkg/info/*.list statt mit einem dpkg-query-Aufruf pro Datei.")
        if not packages and not error:
            self.repair_output.append("Keine veränderten Paketdateien gefunden, die einem installierten Paket zugeordnet werden konnten.")

    def reinstall_selected_package(self):
        package = self.repair_package_combo.currentData()
        if not package:
            QMessageBox.information(self, "Paket-Reparatur", "Bitte zuerst eine Paketprüfung ausführen und ein betroffenes Paket auswählen.")
            return
        helper = Path('/usr/lib/lunasecurity/package-repair-helper')
        if not helper.is_file():
            helper = Path(__file__).resolve().parent.parent / 'scripts' / 'package-repair-helper'
        if not helper.is_file():
            QMessageBox.warning(self, "Paket-Reparatur", "Das Reparatur-Hilfsprogramm fehlt."); return
        simulation = subprocess.run(["apt-get", "-s", "install", "--reinstall", "--no-remove", package], capture_output=True, text=True, timeout=120)
        plan = simulation.stdout + "\n" + simulation.stderr
        if simulation.returncode != 0 or any(line.startswith("Remv ") for line in plan.splitlines()):
            QMessageBox.warning(self, "Paket-Reparatur abgebrochen", "APT konnte keinen sicheren Reparaturplan erstellen oder würde Pakete entfernen. Es wurde nichts verändert.\n\n" + plan[-5000:]); return
        answer = QMessageBox.question(self, "Paket neu installieren", f"Paket: {package}\n\nVorhandene abweichende Paketdateien werden zuerst in /var/lib/lunasecurity/repair-backups gesichert. Danach wird ausschließlich dieses Paket über APT neu installiert. APT darf dabei keine Pakete entfernen.\n\nFortfahren?")
        if answer != QMessageBox.StandardButton.Yes: return
        pkexec = shutil.which("pkexec")
        if not pkexec:
            QMessageBox.warning(self, "Paket-Reparatur", "pkexec ist nicht installiert."); return
        try:
            result = subprocess.run([pkexec, str(helper), package], capture_output=True, text=True, timeout=1800)
            detail = (result.stdout + "\n" + result.stderr).strip() or f"Exit-Code: {result.returncode}"
            self.repair_output.append("Paket-Reparatur für " + package + ":\n" + detail)
            if result.returncode == 0:
                QMessageBox.information(self, "Paket-Reparatur", "APT-Neuinstallation abgeschlossen. Bitte anschließend die Paketprüfung erneut ausführen.\n\n" + detail[-2500:])
            else:
                QMessageBox.warning(self, "Paket-Reparatur", "Reparatur nicht erfolgreich oder abgebrochen. Details stehen im Protokoll.\n\n" + detail[-2500:])
        except (OSError, subprocess.SubprocessError) as exc:
            self.repair_output.append(f"Paket-Reparatur fehlgeschlagen: {exc}")

    def rollback_package_files(self):
        backup_root = Path.home() / ".local/share/LunaSecurity/repair-backups/packages"
        backups = sorted((p for p in backup_root.iterdir() if p.is_dir()), reverse=True) if backup_root.exists() else []
        if not backups:
            QMessageBox.information(self, "Paket-Wiederherstellung", "Keine Paketsicherungen gefunden."); return
        selected, ok = QInputDialog.getItem(self, "Paketdateien zurückspielen", "Sicherung auswählen:", [p.name for p in backups], 0, False)
        if not ok or not selected: return
        helper = Path('/usr/lib/lunasecurity/package-rollback-helper')
        if not helper.is_file(): helper = Path(__file__).resolve().parent.parent / 'scripts' / 'package-rollback-helper'
        if not helper.is_file():
            QMessageBox.warning(self, "Wiederherstellung", "Das Wiederherstellungsprogramm fehlt."); return
        if QMessageBox.warning(self, "Paketdateien zurückspielen", "Die zuvor gesicherten Dateien werden an ihre ursprünglichen Pfade kopiert. Aktuelle Dateien werden zusätzlich mit .lunasecurity-before-rollback gesichert. Paket-Skripte und Seiteneffekte sind nicht Teil dieses Rollbacks. Fortfahren?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes: return
        pkexec = shutil.which("pkexec")
        if not pkexec:
            QMessageBox.warning(self, "Wiederherstellung", "pkexec ist nicht installiert."); return
        result = subprocess.run([pkexec, str(helper), selected], capture_output=True, text=True, timeout=300)
        detail = (result.stdout + "\n" + result.stderr).strip() or f"Exit-Code: {result.returncode}"
        self.repair_output.append("Paketdatei-Rollback:\n" + detail)
        if result.returncode == 0: QMessageBox.information(self, "Wiederherstellung", detail)
        else: QMessageBox.warning(self, "Wiederherstellung fehlgeschlagen", detail)

    def cancel_scan(self):
        if self.module_worker and self.module_worker.isRunning() and self.module_worker.cancellable:
            self.cancel_scan_button.setEnabled(False)
            self.log.append("\nAIDE-Abbruch wird ausgeführt …")
            if getattr(self, "module_progress_dialog", None) is not None:
                self.module_progress_dialog._cancel()
            else:
                self.module_worker.cancel()
            return
        if self.worker and self.worker.isRunning():
            self.cancel_scan_button.setEnabled(False)
            self.log.append("\nScan wurde erfolgreich abgebrochen.")
            self.worker.cancel()

    @Slot(str)
    def scan_finished(self,text):
        self.progress.hide()
        for scan_control in (self.scan_button, self.quick_scan_button, self.full_scan_button):
            scan_control.setEnabled(True)
        self.update_button.setEnabled(True); self.cancel_scan_button.setEnabled(False)
        if self.scan_monitor is not None:
            self.scan_monitor.finish(text)
            # Den angezeigten Scanumfang direkt aus dem Scanfenster übernehmen.
            scan_window_text = self.scan_monitor.log.toPlainText()
            scan_scope_line = next(
                (line.strip() for line in scan_window_text.splitlines()
                 if line.strip().startswith("Scanumfang:")),
                "",
            )
            if scan_scope_line:
                self.log.append(scan_scope_line)
            else:
                self.log.append(
                    "FEHLER: Der Scanumfang konnte nicht aus dem Scanfenster "
                    "übernommen werden. Bitte das Scan-Protokoll im Scanfenster prüfen."
                )
        else:
            self.log.append(
                "FEHLER: Das Scanfenster ist nicht verfügbar; der Scanumfang "
                "konnte nicht ins Hauptprotokoll übernommen werden."
            )
        self.log.append("ClamAV-Prüfung beendet. Details und Live-Protokoll stehen im Scanfenster.")
        # Ignore delayed ClamOnAcc notifications caused by the manual scan.
        self._manual_scan_realtime_suppressed_until = time.monotonic() + 5
        if "Scan wurde vom Benutzer abgebrochen" not in text:
            self.report_detections(text, source="Manueller Scan")
            # Show every detected file path directly in the main activity
            # panel (the red-marked area), not only in the event list below.
            found_items = []
            for line in str(text).splitlines():
                line = line.strip()
                if line.endswith("FOUND") or " FOUND " in line:
                    if (self.settings.value("scan_ignore_max_filesize", True, type=bool)
                            and "HEURISTICS.LIMITS.EXCEEDED.MAXFILESIZE" in line.upper()):
                        continue
                    found_path = sec.detection_path(line)
                    detection_type = _clamav_detection_type(line)
                    item = (found_path, detection_type)
                    if found_path and item not in found_items:
                        found_items.append(item)
            if found_items:
                self.log.append("Gefundene Datei(en):")
                for found_path, detection_type in found_items:
                    self.log.append(f"Datei: {found_path}")
                    if detection_type:
                        self.log.append("Art der Bedrohung: " + detection_type)
        self.log.append("Scan-Aufgabe beendet.")
        self.signature_version_label.setText(_ui_text("Installierte Virensignaturen:") + " " + signature_database_versions())
        # Die Dashboard-Kennzahlen werden aus dem tatsächlichen ClamAV-Bericht gefüllt.
        def metric(pattern, default="0"):
            match = re.search(pattern, str(text), re.IGNORECASE | re.MULTILINE)
            return match.group(1) if match else default
        infected = metric(r"Infected files:\s*(\d+)")
        size_limit_hits = sum(
            1 for line in str(text).splitlines()
            if "HEURISTICS.LIMITS.EXCEEDED.MAXFILESIZE" in line.upper()
            and (line.strip().endswith("FOUND") or " FOUND " in line)
        )
        if self.settings.value("scan_ignore_max_filesize", True, type=bool):
            infected = str(max(0, int(infected) - size_limit_hits))
        scanned = metric(r"Scanned files:\s*(\d+)")
        errors = metric(r"(\d+) errors?", "0")
        skipped = metric(r"Skipped files:\s*(\d+)", "0")
        elapsed = max(0, int(time.monotonic() - getattr(self, "scan_started_at", time.monotonic())))
        # Die Scan-Dialog-Zähler sind die maßgebliche Quelle: ClamAV-Ausgaben
        # können je nach Scanart/Version unterschiedliche Zusammenfassungen liefern.
        monitor = self.scan_monitor
        if monitor is not None:
            infected = str(monitor.threats)
            scanned = str(monitor.checked)
            errors = str(monitor.unreadable)
            skipped = str(monitor.skipped)
            size_limit_hits = monitor.size_limit_count
            elapsed = max(0, int(time.monotonic() - monitor.started))
        self.stat_threats.setText(f"✓  Bedrohungen\n{infected}")
        self.stat_files.setText(f"▱  Geprüfte Dateien\n{scanned}")
        self.stat_size_limit.setText(f"◉  Größenlimit\n{size_limit_hits}")
        self.stat_unreadable.setText(f"⊘  Nicht lesbare\n{errors}")
        self.stat_skipped.setText(f"↪  Übersprungen\n{skipped}")
        self.stat_duration.setText(f"◷  Dauer\n{elapsed//3600:02d}:{(elapsed//60)%60:02d}:{elapsed%60:02d}")
        for card in (self.stat_threats, self.stat_files, self.stat_size_limit, self.stat_unreadable, self.stat_skipped, self.stat_duration):
            card.update()
            card.repaint()
        # Ergebnis, Kopieren und Schließen sind im gemeinsamen ClamAV-Fenster.

    def _show_test_report(self, title, result):
        """Einheitliches, gut lesbares Ergebnisfenster für alle Sicherheitsprüfungen."""
        upper = str(result).upper()
        cancelled = any(token in upper for token in ("ABGEBROCHEN", "CANCELLED", "CANCELED"))
        has_findings = any(token in upper for token in (" FOUND", "INFECTED", "MÖGLICHER FUND", "ROOTKIT FOUND"))
        has_warning = any(token in upper for token in ("WARNUNG", "WARNING", "FEHLER", "ERROR", "NICHT VOLLSTÄNDIG", "SUSPICIOUS"))
        if cancelled:
            heading_text = "Prüfung abgebrochen"
            heading_style = "background:#3a3f50;border:1px solid #77809a;"
        elif has_findings or has_warning:
            heading_text = "Hinweise oder Funde – bitte Ergebnis prüfen"
            heading_style = "background:#6f4d20;border:1px solid #c99b36;"
        else:
            heading_text = "Prüfung abgeschlossen"
            heading_style = "background:#203f36;border:1px solid #4d9b79;"

        dialog = QDialog(self)
        dialog.setWindowTitle(f"LunaSecurity – {title} – Ergebnis")
        dialog.setModal(True)
        dialog.resize(960, 700)
        dialog.setMinimumSize(700, 500)
        dialog.setStyleSheet(self.styleSheet())
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        heading = QLabel(heading_text)
        heading.setWordWrap(True)
        heading.setStyleSheet("font-size:14pt;font-weight:700;padding:12px;border-radius:8px;color:#fff;" + heading_style)
        layout.addWidget(heading)

        subtitle = QLabel(f"Vollständiges Ergebnis: {title}. Warnungen sind nicht automatisch bestätigte Infektionen.")
        subtitle.setWordWrap(True)
        subtitle.setObjectName("muted")
        layout.addWidget(subtitle)

        details = QTextEdit()
        details.setReadOnly(True)
        details.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        details.setPlainText(str(result) or "Keine zusätzlichen Details ausgegeben.")
        details.setStyleSheet("font-family:monospace;font-size:9pt;background:#101522;color:#e8ecf5;padding:8px")
        layout.addWidget(details, 1)

        buttons = QHBoxLayout()
        copy_button = QPushButton("Ergebnis kopieren")
        copy_button.clicked.connect(lambda: QApplication.clipboard().setText(f"{title}\n\n{result}"))
        buttons.addWidget(copy_button)
        buttons.addStretch()
        close_button = QPushButton("Schließen")
        close_button.setMinimumWidth(130)
        close_button.clicked.connect(dialog.accept)
        buttons.addWidget(close_button)
        layout.addLayout(buttons)
        dialog.exec()

    def run_module(self, title, function, cancellable=False):
        if self.module_worker and self.module_worker.isRunning():
            QMessageBox.information(self, "LunaSecurity", "Es läuft bereits eine Sicherheitsprüfung.")
            return
        self.log.append(f"\n{title} gestartet … (Hintergrund)")
        self.progress.hide()
        if cancellable:
            self.cancel_scan_button.setText("Prüfung abbrechen")
            self.cancel_scan_button.setEnabled(True)
        worker = ModuleWorker(title, function, cancellable=cancellable)
        self.module_worker = worker
        self.module_progress_dialog = ModuleProgressDialog(title, worker.cancel, self)
        self.module_progress_dialog.append_output(f"{title} gestartet.")
        worker.output.connect(self.module_progress_dialog.append_output)
        worker.result.connect(self.module_progress_dialog.finish)
        worker.result.connect(self.module_finished)
        self.module_progress_dialog.show()
        worker.start()

    @staticmethod
    def _rootkit_serious_finding(result):
        upper = result.upper().replace("NOT INFECTED", "").replace("NOT FOUND", "")
        return any(token in upper for token in ("INFECTED", "POSSIBLE ROOTKIT", "ROOTKIT FOUND"))

    def _rootkit_recommendations(self, result):
        """Erstellt vorsichtige, verständliche Hinweise aus den Scanner-Ausgaben."""
        upper = result.upper()
        tips = []
        if "NICHT INSTALLIERT" in upper or "NOT INSTALLED" in upper:
            tips.append("Fehlender Scanner: Installiere rkhunter bzw. chkrootkit über die Debian-Paketverwaltung und starte die Prüfung erneut.")
        if self._rootkit_serious_finding(result):
            tips.append("Ernsthafter Verdacht: Trenne das Gerät vorsorglich vom Netzwerk, wenn du ungewöhnliches Verhalten bemerkst. Sichere zuerst wichtige Protokolle und lösche keine Systemdateien auf Verdacht.")
            tips.append("Prüfe den genannten Fund mit einem zweiten Werkzeug und vergleiche Datei, Prozess oder Prüfsumme mit einer vertrauenswürdigen Quelle bzw. einem sauberen System.")
            tips.append("Bei bestätigtem Befall: Zugangsdaten von einem sauberen Gerät ändern und eine Neuinstallation aus vertrauenswürdigen Installationsmedien erwägen.")
        elif "WARNING" in upper or "WARNUNG" in upper or "SUSPICIOUS" in upper:
            tips.append("Hinweise sind nicht automatisch ein Rootkit-Nachweis. rkhunter und chkrootkit melden gelegentlich legitime Dateien, Kernel-Funktionen oder lokale Anpassungen.")
            tips.append("Lies bei jeder Warnung den vollständigen Pfad und die Begründung. Prüfe, ob die Datei zu einem installierten Debian-Paket gehört (z. B. mit dpkg -S /Pfad/zur/Datei).")
            tips.append("Vergleiche verdächtige Dateien mit den Paketprüfsummen bzw. installiere das betroffene Paket aus einer vertrauenswürdigen Debian-Quelle neu.")
        if "NOT TESTED" in upper or "NOT CHECKED" in upper or "NICHT GEPRÜFT" in upper:
            tips.append("Einige Tests wurden übersprungen oder konnten nicht ausgeführt werden. Prüfe die jeweilige Begründung und wiederhole die Prüfung mit den erforderlichen Rechten.")
        if not tips:
            tips.append("Es wurde kein eindeutiger Rootkit-Hinweis in den Scanner-Ausgaben erkannt. Das ist keine Garantie für ein vollständig sauberes System.")
            tips.append("Halte Debian und die Scanner aktuell und wiederhole die Prüfung nach größeren Systemänderungen.")
        tips.append("Wichtig: LunaSecurity löscht oder verändert aufgrund dieser Ergebnisse nichts automatisch.")
        return tips

    def _show_rootkit_report(self, result):
        upper = result.upper()
        if self._rootkit_serious_finding(result):
            status = "Möglicher ernsthafter Fund – bitte zeitnah prüfen"
            status_style = "background:#6f202b;border:1px solid #e05262;"
        elif "WARNING" in upper or "WARNUNG" in upper or "SUSPICIOUS" in upper:
            status = "Hinweise gefunden – nicht automatisch eine Infektion"
            status_style = "background:#66501d;border:1px solid #c99b36;"
        else:
            status = "Prüfung abgeschlossen – kein eindeutiger Fund erkannt"
            status_style = "background:#203f36;border:1px solid #4d9b79;"

        dialog = QDialog(self)
        dialog.setWindowTitle("LunaSecurity – Rootkit-Prüfbericht")
        dialog.setModal(True)
        dialog.resize(980, 760)
        dialog.setMinimumSize(760, 580)
        dialog.setStyleSheet(self.styleSheet())
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        heading = QLabel(status)
        heading.setWordWrap(True)
        heading.setStyleSheet("font-size:14pt;font-weight:700;padding:12px;border-radius:8px;color:#fff;" + status_style)
        layout.addWidget(heading)

        intro = QLabel("Ergebnisse von rkhunter und chkrootkit. Warnungen können Fehlalarme sein und müssen einzeln bewertet werden.")
        intro.setWordWrap(True)
        intro.setObjectName("muted")
        layout.addWidget(intro)

        tips_title = QLabel("Empfohlene nächste Schritte")
        tips_title.setStyleSheet("font-size:12pt;font-weight:700")
        layout.addWidget(tips_title)
        tips = QTextEdit()
        tips.setReadOnly(True)
        tips.setMaximumHeight(150)
        tips.setPlainText("\n".join(f"• {tip}" for tip in self._rootkit_recommendations(result)))
        layout.addWidget(tips)

        details_title = QLabel("Vollständige Scanner-Ausgabe")
        details_title.setStyleSheet("font-size:12pt;font-weight:700")
        layout.addWidget(details_title)
        details = QTextEdit()
        details.setReadOnly(True)
        details.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        details.setPlainText(result)
        details.setStyleSheet("font-family:monospace;font-size:9pt;background:#101522;color:#e8ecf5;padding:8px")
        layout.addWidget(details, 1)

        row = QHBoxLayout()
        copy_button = QPushButton("Bericht kopieren")
        copy_button.clicked.connect(lambda: QApplication.clipboard().setText(
            status + "\n\nEmpfohlene nächste Schritte:\n" +
            "\n".join(f"- {tip}" for tip in self._rootkit_recommendations(result)) +
            "\n\nScanner-Ausgabe:\n" + result))
        row.addWidget(copy_button)
        repair_button = QPushButton("Reparaturhilfe öffnen")
        repair_button.clicked.connect(lambda: self._open_repair_help_from_report(dialog))
        row.addWidget(repair_button)
        row.addStretch()
        close_button = QPushButton("Schließen")
        close_button.setMinimumWidth(130)
        close_button.clicked.connect(dialog.accept)
        row.addWidget(close_button)
        layout.addLayout(row)
        dialog.exec()

    def _open_repair_help_from_report(self, report_dialog):
        """Aktiviert das Hauptfenster und die Reparaturhilfe vor dem Schließen des Berichts."""
        self.showNormal()
        self.tabs.setCurrentWidget(self.repair_tab)
        self.tabs.setFocus()
        self.raise_()
        self.activateWindow()
        report_dialog.accept()

    @Slot(str, str)
    def module_finished(self, title, result):
        self.progress.hide()
        if title in ("Systemintegrität", "Lynis-Sicherheitsprüfung", "fail2ban-Überwachung", "Rootkit-Prüfung", "System-Audit"):
            self.cancel_scan_button.setEnabled(False)
            self.cancel_scan_button.setText("Scan abbrechen")
        if title == "YARA-Regelaktualisierung":
            self.yara_update_button.setEnabled(True)
            self.refresh_yara_rules_status()

        # Keine zusätzlichen Ergebnisdialoge: Das gemeinsame Prüfungsfenster
        # zeigt bereits den vollständigen Rückgabewert.
        if title == "Rootkit-Prüfung":
            if self._rootkit_serious_finding(result):
                summary = "Rootkit-Prüfung: möglicher ernsthafter Fund – Ergebnisfenster prüfen."
            elif any(token in result.upper() for token in ("WARNING", "WARNUNG", "SUSPICIOUS")):
                summary = "Rootkit-Prüfung: Hinweise gefunden – Ergebnisfenster prüfen."
            else:
                summary = "Rootkit-Prüfung abgeschlossen – Ergebnisfenster prüfen."
            self.log.append(summary)
            return

        self.log.append(result)
        if title in ("Lynis-Sicherheitsprüfung", "fail2ban-Überwachung"):
            self.advanced_output.setPlainText(title + "\\n\\n" + result)
        self.log.append(f"{title} beendet. Ergebnisse bitte im Prüfungsfenster prüfen; Warnungen sind nicht automatisch bestätigte Infektionen.")

    def block_firewall_port(self):
        port, ok = QInputDialog.getInt(
            self, "Port gezielt sperren",
            "Welchen eingehenden Port möchtest du vorübergehend blockieren?\\n"
            "SSH-Port 22 ist zum Schutz vor Aussperren ausgeschlossen.",
            8080, 1, 65535, 1)
        if not ok:
            return
        protocol, ok = QInputDialog.getItem(
            self, "Protokoll auswählen", "Für welches Protokoll?",
            ["tcp", "udp"], 0, False)
        if not ok:
            return
        confirm = QMessageBox.question(
            self, "Firewall-Regel bestätigen",
            f"Der eingehende Port {port}/{protocol} wird sofort durch eine zusätzliche "
            "LunaSecurity-Regel blockiert. Bestehende Regeln bleiben unverändert. "
            "Die Regel gilt zunächst nur bis zum Neustart/Neuladen der Firewall. "
            "Du kannst sie später mit „Testregeln dauerhaft speichern“ übernehmen. "
            "Eine Sicherung des aktuellen nftables-Regelsatzes wird vorher angelegt. "
            "Möchtest du fortfahren?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if confirm != QMessageBox.StandardButton.Yes:
            return
        result = sec.firewall_guard_action("block-port", port, protocol)
        QMessageBox.information(self, "LunaSecurity – Firewall-Aktion", result)

    def persist_firewall_guard(self):
        confirm = QMessageBox.question(
            self, "Testregeln dauerhaft speichern",
            "Die aktuell aktiven LunaSecurity-Testregeln werden gesichert und für "
            "künftige Systemstarts aktiviert. Andere Firewall-Regeln bleiben "
            "unverändert. Du kannst die LunaSecurity-Regeln später jederzeit über "
            "„LunaSecurity-Sperren aufheben“ entfernen. Möchtest du diese Regeln "
            "dauerhaft übernehmen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if confirm != QMessageBox.StandardButton.Yes:
            return
        result = sec.firewall_guard_action("persist")
        QMessageBox.information(self, "LunaSecurity – Dauerhaft speichern", result)

    def rollback_firewall_guard(self):
        confirm = QMessageBox.question(
            self, "Firewall-Sperren aufheben",
            "Alle temporären und dauerhaft gespeicherten Port-Sperren, die LunaSecurity "
            "über seine eigene Firewall-Kette angelegt hat, werden entfernt. Auch der "
            "Autostart dieser Regeln wird deaktiviert. Andere Firewall-Regeln bleiben "
            "unverändert. Möchtest du fortfahren?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if confirm != QMessageBox.StandardButton.Yes:
            return
        result = sec.firewall_guard_action("rollback")
        QMessageBox.information(self, "LunaSecurity – Rückgängig", result)

    def refresh_yara_rules_status(self):
        rules_dir = Path("/etc/lunasecurity/yara-rules")
        count = len(list(rules_dir.glob("*.yar"))) + len(list(rules_dir.glob("*.yara"))) if rules_dir.exists() else 0
        if hasattr(self, "yara_rules_status"):
            self.yara_rules_status.setText(
                f"{count} YARA-Regeldateien installiert" if count else
                "Noch keine YARA-Regeln installiert. Bitte zuerst aktualisieren."
            )

    def update_yara_rules(self):
        helper = Path("/usr/lib/lunasecurity/yara-update-helper")
        pkexec = shutil.which("pkexec")
        if not helper.exists():
            QMessageBox.warning(self, "YARA-Regeln", "Das YARA-Aktualisierungsprogramm fehlt.")
            return
        if not pkexec:
            QMessageBox.warning(self, "YARA-Regeln", "pkexec ist nicht installiert. Für die Installation der Regeln werden Administratorrechte benötigt.")
            return
        self.yara_update_button.setEnabled(False)
        self.run_module("YARA-Regelaktualisierung", lambda: self._run_yara_update(pkexec, helper))

    def _run_yara_update(self, pkexec, helper):
        try:
            result = subprocess.run([pkexec, str(helper)], capture_output=True, text=True, timeout=300)
            detail = (result.stdout + "\\n" + result.stderr).strip()
            if result.returncode != 0:
                detail = detail or f"YARA-Regelaktualisierung fehlgeschlagen (Exit-Code {result.returncode})."
            return detail or "YARA-Regeln wurden aktualisiert."
        except subprocess.TimeoutExpired:
            return "YARA-Regelaktualisierung wegen Zeitüberschreitung abgebrochen."
        except Exception as exc:
            return f"YARA-Regelaktualisierung fehlgeschlagen: {exc}"

    def choose_yara_target(self):
        path = _choose_directory(self, "Scan-Verzeichnis auswählen", Path.home())
        if path:
            self.yara_path.setText(path)
            self.run_module("YARA-Scan", lambda: sec.yara_scan(path))

    def quarantine_selected(self):
        path, _ = _choose_file(self, "Datei für Quarantäne auswählen", Path.home())
        if not path: return
        answer = QMessageBox.warning(self, "Quarantäne bestätigen", f"Diese Datei wird aus ihrem ursprünglichen Ort verschoben und isoliert:\n\n{path}\n\nFortfahren?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer == QMessageBox.Yes:
            try:
                self._suppress_quarantine_move_alert(path)
                self.log.append(sec.quarantine_file(path))
            except Exception as exc: QMessageBox.critical(self, "Quarantäne fehlgeschlagen", str(exc))

    def shutdown(self):
        if hasattr(self, "_qt_tray"):
            self._qt_tray.hide()
        if self.tray:
            tray, self.tray = self.tray, None
            tray.stop()


def main():
    hidden_arg = "--hidden" in sys.argv[1:]
    qt_args = [arg for arg in sys.argv if arg != "--hidden"]
    # Eigene Qt-Dialoge erzwingen: native GTK/Plattformdialoge können unabhängig
    # von der Sprache der App englische Beschriftungen anzeigen.
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs, True)
    app=QApplication(qt_args); app.setApplicationName("LunaSecurity"); app.setQuitOnLastWindowClosed(False)
    startup_settings = QSettings("LunaSecurity", "LunaSecurity")
    startup_language = startup_settings.value("language", "de")
    QLocale.setDefault(QLocale(QLocale.Language.English if startup_language == "en" else QLocale.Language.German,
                               QLocale.Country.UnitedStates if startup_language == "en" else QLocale.Country.Germany))
    global APP_QT_TRANSLATOR, APP_DIALOG_BUTTON_FIX, APP_EN_DIALOG_FIX, APP_LANGUAGE
    APP_LANGUAGE = startup_language
    if startup_language == "en":
        APP_EN_DIALOG_FIX = EnglishMessageBoxFix(app)
        app.installEventFilter(APP_EN_DIALOG_FIX)
    else:
        APP_QT_TRANSLATOR = GermanQtTranslator(app)
        app.installTranslator(APP_QT_TRANSLATOR)
        APP_DIALOG_BUTTON_FIX = GermanDialogButtonFix(app)
        app.installEventFilter(APP_DIALOG_BUTTON_FIX)
    window=MainWindow()
    start_hidden = hidden_arg or window.settings.value("start_in_tray", False, type=bool)
    if start_hidden and window.tray:
        window.hide()
        window.log.append("LunaSecurity wurde im System-Tray gestartet.")
    else:
        window.show()
    app.aboutToQuit.connect(window.shutdown)
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
