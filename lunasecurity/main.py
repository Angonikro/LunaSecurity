from __future__ import annotations
import os, shutil, subprocess, sys, threading, time, json, wave, tempfile, struct, math, signal, re
from pathlib import Path
from PySide6.QtCore import QObject, Signal, Slot, QThread, QSettings, QTimer, QTranslator, QLocale, Qt, QEvent, QPoint, QMarginsF
from PySide6.QtGui import QAction, QIcon, QTextDocument, QTextOption, QFont, QPainter, QLinearGradient, QRadialGradient, QColor, QPolygon, QPen, QBrush, QTextCursor
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtGui import QPageSize, QPageLayout
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QDialog,
    QLabel, QPushButton, QTextEdit, QProgressBar, QCheckBox, QMessageBox, QFrame, QFileDialog, QTabWidget, QGroupBox, QScrollArea, QSystemTrayIcon, QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QComboBox, QSlider, QSpinBox, QStyle, QInputDialog, QSizePolicy)

def _german_file_dialog(parent, title, start_dir, directory_mode=False, file_filter="Alle Dateien (*)"):
    """Einheitlicher Qt-Dateidialog für Datei- und Ordnerauswahl, vollständig deutsch."""
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QLabel, QPushButton, QComboBox

    dialog = QFileDialog(parent, title, str(start_dir))
    dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
    dialog.setFileMode(QFileDialog.FileMode.Directory if directory_mode else QFileDialog.FileMode.ExistingFile)
    # Gleiche Dialogansicht für Datei- und Ordnerauswahl; nur der Auswahlmodus ändert sich.
    dialog.setOption(QFileDialog.Option.ShowDirsOnly, False)
    dialog.setLabelText(QFileDialog.DialogLabel.LookIn, "Suchen in:")
    dialog.setLabelText(QFileDialog.DialogLabel.FileName,
                        "Verzeichnis:" if directory_mode else "Dateiname:")
    dialog.setLabelText(QFileDialog.DialogLabel.FileType, "Dateityp:")
    dialog.setLabelText(QFileDialog.DialogLabel.Accept,
                        "Ordner auswählen" if directory_mode else "Datei auswählen")
    dialog.setLabelText(QFileDialog.DialogLabel.Reject, "Abbrechen")
    dialog.setNameFilter("Verzeichnisse (*)" if directory_mode else file_filter)

    def translate_widgets():
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
            status = subprocess.run([systemctl, "is-active", "--quiet", "lunasecurity-realtime.service"],
                                    capture_output=True, timeout=10)
            active = status.returncode == 0
            self.result.emit(detail or ("Echtzeitschutz aktiviert." if active else "Echtzeitschutz deaktiviert."), active, True)
        except subprocess.TimeoutExpired:
            self.result.emit("Zeitüberschreitung beim Hintergrundauftrag. Die Oberfläche bleibt bedienbar; bitte Dienststatus prüfen.", False, False)
        except Exception as exc:
            self.result.emit(f"Echtzeitschutz-Auftrag fehlgeschlagen: {exc}", False, False)

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


class ModuleProgressDialog(QDialog):
    """Fortschrittsfenster für Sicherheitsprüfungen außerhalb von ClamAV."""
    def __init__(self, title, cancel_callback, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"LunaSecurity – {title}")
        self.setMinimumSize(700, 480)
        self.resize(860, 600)
        self.setModal(False)
        self._finished = False
        self.setStyleSheet(parent.styleSheet() if parent else "")
        layout = QVBoxLayout(self)
        heading = QLabel(f"{title} läuft")
        heading.setStyleSheet("font-size:17pt;font-weight:800")
        layout.addWidget(heading)
        self.status = QLabel("Prüfung wird vorbereitet …")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.bar = QProgressBar()
        self.bar.setRange(0, 0)
        self.bar.setFormat("Prüfung läuft …")
        layout.addWidget(self.bar)
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.output.document().setMaximumBlockCount(10000)
        self.output.setPlaceholderText("Ausgaben der laufenden Prüfung erscheinen hier.")
        layout.addWidget(self.output, 1)
        buttons = QHBoxLayout()
        self.cancel_button = QPushButton("Prüfung abbrechen")
        self.cancel_button.clicked.connect(self._cancel)
        self._cancel_callback = cancel_callback
        buttons.addWidget(self.cancel_button)
        self.copy_button = QPushButton("Ergebnis kopieren")
        self.copy_button.clicked.connect(lambda: QApplication.clipboard().setText(self.output.toPlainText()))
        buttons.addWidget(self.copy_button)
        buttons.addStretch(1)
        self.close_button = QPushButton("Schließen")
        self.close_button.setEnabled(False)
        self.close_button.clicked.connect(self.accept)
        buttons.addWidget(self.close_button)
        layout.addLayout(buttons)

    def _cancel(self):
        self.cancel_button.setEnabled(False)
        self.cancel_button.setText("Abbruch läuft …")
        self.status.setText("Die Prüfung wird abgebrochen …")
        self._cancel_callback()

    def append_output(self, line):
        if line:
            self.output.append(str(line))
            self.status.setText(str(line)[:500])

    def finish(self, title, result):
        self._finished = True
        result = str(result or "")
        if result.strip():
            self.output.setPlainText(result)
            self.output.moveCursor(QTextCursor.MoveOperation.Start)
        cancelled = any(token in result.lower() for token in ("abgebrochen", "abbruch", "cancelled"))
        self.status.setText("Prüfung abgebrochen" if cancelled else "Prüfung abgeschlossen")
        self.bar.setRange(0, 1)
        self.bar.setValue(0 if cancelled else 1)
        self.bar.setFormat("Abgebrochen" if cancelled else "100 %")
        self.cancel_button.setEnabled(False)
        self.close_button.setEnabled(True)

    def closeEvent(self, event):
        if not self._finished:
            event.ignore()
            return
        super().closeEvent(event)


class ClamScanMonitor(QDialog):
    """Einheitliche Live-Ansicht für sämtliche ClamAV-Scans."""
    def __init__(self, target, parent=None, cancel_callback=None):
        super().__init__(parent)
        self.cancel_callback = cancel_callback
        self.setWindowTitle("LunaSecurity – ClamAV-Systemprüfung")
        self.setMinimumSize(760, 560)
        self.setModal(False)
        self.started = time.monotonic()
        self.checked = 0
        self.total_files = 0
        self._checked_paths = set()
        self.threats = 0
        self.unreadable = 0
        self.skipped = 0
        self._current_scan_path = ""
        self._unreadable_paths = set()
        self._skipped_paths = set()
        self._unreadable_fallback = set()
        self._skipped_fallback = set()
        root = QVBoxLayout(self)
        head = QHBoxLayout()
        title = QLabel("ClamAV-Scan läuft")
        title.setStyleSheet("font-size:19pt;font-weight:800")
        self.state = QLabel("● Aktiv")
        self.state.setStyleSheet("color:#35d46a;font-weight:700")
        head.addWidget(title); head.addStretch(1); head.addWidget(self.state)
        root.addLayout(head)
        self.target_label = QLabel(f"Scanbereich: {target}")
        self.target_label.setWordWrap(True)
        root.addWidget(self.target_label)
        self.note = QLabel("Root-Rechte werden nur für geschützte Systembereiche benötigt.")
        self.note.setObjectName("muted")
        root.addWidget(self.note)
        self.bar = QProgressBar(); self.bar.setRange(0, 0)
        root.addWidget(self.bar)
        stats = QHBoxLayout()
        self.checked_label = QLabel("0\nGeprüfte Dateien")
        self.threat_label = QLabel("0\nBedrohungen")
        self.unreadable_label = QLabel("0\nNicht lesbar")
        self.skipped_label = QLabel("0\nÜbersprungen")
        for label in (self.checked_label, self.threat_label, self.unreadable_label, self.skipped_label):
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("QLabel{background:#292b3b;border:1px solid #555875;border-radius:9px;padding:12px;font-size:12pt;font-weight:700}")
            stats.addWidget(label)
        root.addLayout(stats)
        self.current = QLabel("Aktuelle Datei: wird vorbereitet …")
        self.current.setWordWrap(True)
        root.addWidget(self.current)
        log_title = QLabel("Scan-Protokoll")
        log_title.setStyleSheet("font-size:13pt;font-weight:700")
        root.addWidget(log_title)
        self.log = QTextEdit(); self.log.setReadOnly(True)
        self.log.document().setMaximumBlockCount(5000)
        root.addWidget(self.log, 1)
        self.elapsed = QLabel("Verstrichene Zeit: 00:00")
        root.addWidget(self.elapsed)
        actions = QHBoxLayout()
        self.actions_layout = actions
        self.cancel_button = QPushButton("Scan abbrechen")
        self.cancel_button.clicked.connect(self.cancel_scan)
        actions.addWidget(self.cancel_button)
        self.copy_button = QPushButton("Scan-Ergebnis kopieren")
        self.copy_button.clicked.connect(self.copy_result)
        actions.addWidget(self.copy_button)
        actions.addStretch(1)
        # Der Button existiert von Anfang an im Layout, ist aber während
        # des Scans vollständig verborgen. Im Abschluss-Slot wird er eingeblendet.
        self.close_button = QPushButton("Schließen")
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
            self.bar.setFormat("Scan läuft …")

    def update_elapsed(self):
        seconds = int(time.monotonic() - self.started)
        self.elapsed.setText(f"Verstrichene Zeit: {seconds//3600:02d}:{(seconds//60)%60:02d}:{seconds%60:02d}")

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
            if " FOUND" in upper or "INFECTED" in upper:
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
        self.current.setText("Aktuelle Datei: " + (self._current_scan_path or cleaned[-1])[:500])
        self.checked_label.setText(f"{self.checked:,}\nGeprüfte Dateien".replace(",", "."))
        if self.total_files > 0:
            self.bar.setValue(min(self.checked, self.total_files))
        self.threat_label.setText(f"{self.threats}\nBedrohungen")
        self.unreadable_label.setText(f"{self.unreadable}\nNicht lesbar")
        self.skipped_label.setText(f"{self.skipped}\nÜbersprungen")

    def cancel_scan(self):
        if self.cancel_callback:
            self.cancel_button.setEnabled(False)
            self.cancel_button.setText("Abbruch läuft …")
            self.note.setText("Der Scan wird abgebrochen …")
            self.cancel_callback()
            # Sofort die Schließen-Aktion anbieten; der Worker beendet parallel ClamAV.
            self._replace_close_button()

    def copy_result(self):
        QApplication.clipboard().setText(self.log.toPlainText())

    def _replace_close_button(self):
        # Kompatibler Name; der Button ist bereits im Layout und wird nur gezeigt.
        self.cancel_button.setEnabled(False)
        self.cancel_button.setText("Scan abbrechen")
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
        self.bar.setFormat("Abgebrochen" if cancelled else "100 %")
        self.state.setText("● Abgebrochen" if cancelled else "● Abgeschlossen")
        # This is the authoritative terminal-state command. Reveal the close
        # button immediately here, rather than waiting for later report/log work.
        self._replace_close_button()
        self.state.setStyleSheet("color:#35d46a;font-weight:700")
        self.note.setText(
            "Scan abgebrochen. Das bisherige Ergebnis steht im Scan-Protokoll."
            if cancelled else
            "Scan abgeschlossen. Das vollständige Ergebnis steht im Scan-Protokoll."
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
            summary = re.search(r"Scanned files:\s*(\d+)", str(result), re.IGNORECASE)
            if summary:
                self.checked = int(summary.group(1))
                self.checked_label.setText(f"{self.checked:,}\nGeprüfte Dateien".replace(",", "."))
        self._replace_close_button()
        # Normaler Abschluss: Sichtbarkeit nach dem Qt-Signal nochmals anwenden.
        QTimer.singleShot(0, self._replace_close_button)
        QTimer.singleShot(150, self._replace_close_button)



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LunaSecurity – Linux Security Suite")
        self.resize(1320, 900)  # Platz für linke Navigation und Arbeitsbereich
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
        self.setStyleSheet("""
          QMainWindow,QWidget {background:#111629;color:#e9edfa;font-family:'Noto Sans';font-size:12pt}
          QFrame#panel {background:#1a2340;border:1px solid #394879;border-radius:12px}
          QLabel#title {font-size:23pt;font-weight:700;color:#ffffff}
          QLabel#muted {color:#aab8d5}
          QPushButton {background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #386ff0,stop:1 #2447c9);color:white;border:1px solid #6484ff;border-radius:9px;padding:7px 11px;font-weight:600;min-height:34px}
          QPushButton:hover {background:#6544dc;border-color:#a78bfa}
          QPushButton:disabled {background:#39445f;color:#9aa4b8;border-color:#46516b}
          QTextEdit {background:#0b1122;border:1px solid #34436f;border-radius:8px;color:#dce5f5}
          QCheckBox {spacing:8px}
          QListWidget#sideNav {background:#10142c;border:0;border-right:1px solid #35416c;padding:9px 7px;outline:0}
          QListWidget#sideNav::item {color:#e5e9fa;padding:11px 9px;margin:3px 2px;border-radius:9px;min-height:22px}
          QListWidget#sideNav::item:hover {background:#252653}
          QListWidget#sideNav::item:selected {background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #6937d9,stop:1 #3829a8);border:1px solid #9b78ff;color:white;font-weight:700}
          QTabBar {qproperty-drawBase:0; height:0; max-height:0}
          QTabWidget::pane {border:0;top:0}
          QGroupBox {border:1px solid #34436f;border-radius:9px;margin-top:9px;padding-top:8px}
          QGroupBox::title {subcontrol-origin:margin;left:10px;padding:0 5px;color:#c5ceef}
        """)
        root=QWidget(); self.setCentralWidget(root)
        shell=QHBoxLayout(root); shell.setContentsMargins(0,0,0,0); shell.setSpacing(0)
        sidebar=QWidget(); sidebar.setObjectName("sidebar"); sidebar.setFixedWidth(356)
        sidebar.setStyleSheet("QWidget#sidebar{background:#10142c;border-right:1px solid #35416c}")
        side_layout=QVBoxLayout(sidebar); side_layout.setContentsMargins(10,14,10,0); side_layout.setSpacing(8)
        brand=QLabel("◈  LunaSecurity\n     Linux Security Suite")
        brand.setStyleSheet("font-size:14pt;font-weight:700;color:#ffffff;padding:8px 4px 16px 4px")
        side_layout.addWidget(brand)
        self.side_nav=QListWidget(); self.side_nav.setObjectName("sideNav"); self.side_nav.setSpacing(1)
        side_layout.addWidget(self.side_nav,1)
        side_layout.addWidget(MoonArtwork(sidebar))
        shell.addWidget(sidebar)
        content=QWidget(); shell.addWidget(content,1)
        layout=QVBoxLayout(content); layout.setContentsMargins(14,10,14,10); layout.setSpacing(7)
        header=QHBoxLayout(); title=QLabel("LunaSecurity"); title.setObjectName("title"); header.addWidget(title)
        version=QLabel(f"LINUX SECURITY SUITE  ·  {__version__}"); version.setObjectName("muted"); header.addStretch(); header.addWidget(version); layout.addLayout(header)
        subtitle=QLabel("Sicherheitsübersicht für dein Linux-System"); subtitle.setObjectName("muted"); layout.addWidget(subtitle)
        self.alert_banner = QLabel("⚠ BEDROHUNG ERKANNT – Details siehe Sicherheitsereignisse")
        self.alert_banner.setStyleSheet("background:#6f202b;color:#fff;border:1px solid #e05262;border-radius:8px;padding:12px;font-weight:700")
        self.alert_banner.setWordWrap(True)
        self.alert_banner.hide()
        layout.addWidget(self.alert_banner)
        cards=QHBoxLayout()
        for heading,detail in [("Virenschutz","ClamAV-Scanner und Echtzeitschutz"),
              ("Systemschutz","Rootkit-, AIDE- und System-Audit"),
              ("Netzwerk","Ports und Firewall-Regeln")]:
            card=QFrame(); card.setObjectName("panel"); box=QVBoxLayout(card); h=QLabel(heading); h.setStyleSheet("font-size:13pt;font-weight:700"); d=QLabel(detail); d.setObjectName("muted"); box.addWidget(h); box.addWidget(d); cards.addWidget(card)
        layout.addLayout(cards)
        actions=QHBoxLayout(); self.scan_button=QPushButton("Dateien / Ordner scannen"); self.scan_button.clicked.connect(lambda _checked=False: self.start_scan()); actions.addWidget(self.scan_button)
        self.home_button=QPushButton("Home-Verzeichnis prüfen"); self.home_button.clicked.connect(lambda:self.start_scan(str(Path.home()), full_scan=True)); actions.addWidget(self.home_button)
        self.scan_profile = QComboBox(); self.scan_profile.addItems(["Eigenes Profil", "Schnellscan", "Komplettscan"])
        self.scan_profile.setToolTip("Legt die Scanoptionen für den nächsten Scan fest."); actions.addWidget(self.scan_profile); layout.addLayout(actions)
        self.auto_update_check = QCheckBox("Vor jedem Scan automatisch Virensignaturen mit freshclam aktualisieren")
        self.auto_update_check.setChecked(self.settings.value("auto_freshclam", False, type=bool))
        self.auto_update_check.setToolTip("Führt vor jedem Scan eine Signaturaktualisierung mit Administrator-Passwortabfrage aus. Wenn der ClamAV-Dienst läuft, übernimmt dieser die Aktualisierung.")
        self.auto_update_check.toggled.connect(lambda value: self.settings.setValue("auto_freshclam", value))
        self.update_button = QPushButton("Virensignatur aktualisieren")
        self.update_button.clicked.connect(self.update_signatures_now)
        self.signature_version_label = QLabel("Installierte Virensignaturen: " + signature_database_versions())
        self.signature_version_label.setObjectName("muted")
        self.signature_version_label.setWordWrap(True)
        layout.addWidget(self.signature_version_label)
        realtime_row = QHBoxLayout()
        self.system_scan_button = QPushButton("Vollständiger Systemscan")
        self.system_scan_button.setToolTip("Prüft das gesamte Wurzelverzeichnis / einschließlich geschützter Bereiche; Root-Rechte werden über pkexec angefordert.")
        self.system_scan_button.clicked.connect(lambda: self.start_scan("/", elevated=True))
        realtime_row.addWidget(self.system_scan_button)
        realtime_row.addWidget(self.update_button)
        self.realtime_button = QPushButton("Echtzeitschutz aktivieren")
        self.realtime_button.clicked.connect(self.toggle_realtime)
        realtime_row.addWidget(self.realtime_button)
        realtime_row.addStretch(1)
        self.realtime_status = QLabel("Echtzeitschutz: Status wird geprüft …")
        self.realtime_status.setObjectName("muted")
        self.realtime_status.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        realtime_row.addWidget(self.realtime_status)
        self.realtime_indicator = QLabel("●")
        self.realtime_indicator.setToolTip("Status des ClamAV-Echtzeitschutzes")
        self.realtime_indicator.setStyleSheet("font-size:22px;font-weight:900;color:#e0a52b;padding-left:5px;padding-right:5px;")
        realtime_row.addWidget(self.realtime_indicator)
        layout.addLayout(realtime_row)
        self.refresh_realtime_status()
        # Der alte Fortschritts-/Abbruchbereich der Hauptansicht wurde entfernt.
        # Statusobjekte bleiben intern für bestehende Nicht-ClamAV-Prüfungen erhalten,
        # werden aber nicht mehr in die Oberfläche eingefügt.
        self.progress = QProgressBar(self)
        self.progress.setRange(0, 0)
        self.progress.hide()
        self.cancel_scan_button = QPushButton("Scan abbrechen", self)
        self.cancel_scan_button.setEnabled(False)
        self.cancel_scan_button.clicked.connect(self.cancel_scan)
        self.cancel_scan_button.hide()
        self.log=QTextEdit(); self.log.setReadOnly(True); self.log.setMinimumHeight(152); self.log.setMaximumHeight(152); self.log.setPlaceholderText("Scan-Ergebnisse und Sicherheitsmeldungen erscheinen hier."); layout.addWidget(self.log, 0)
        self.tray_check=QCheckBox("Beim Schließen im Infobereich weiterlaufen")
        self.tray_check.setChecked(self.settings.value("minimize_to_tray", True, type=bool))
        self.tray_check.toggled.connect(self.set_minimize_to_tray)

        self.start_hidden_check=QCheckBox("Beim Start direkt im Infobereich starten")
        self.start_hidden_check.setChecked(self.settings.value("start_in_tray", False, type=bool))
        self.start_hidden_check.toggled.connect(self.set_start_in_tray)

        self.autostart_check=QCheckBox("LunaSecurity automatisch bei der Anmeldung starten")
        self.autostart_check.setChecked(self.settings.value("autostart_enabled", False, type=bool))
        self.autostart_check.toggled.connect(self.set_autostart)
        tabs = QTabWidget()
        tabs.setMinimumHeight(205)
        tabs.tabBar().hide()
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
        net_btn.setMinimumHeight(48); net_btn.setMinimumWidth(0); net_layout.addWidget(net_btn); net_layout.addStretch(); tabs.addTab(net_tab, "Netzwerk")
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
        clam_group = QGroupBox("ClamAV – Scanoptionen")
        clam_layout = QVBoxLayout(clam_group)
        clam_intro = QLabel("Diese Optionen werden bei Datei- und Ordnerscans an ClamAV übergeben.")
        clam_intro.setObjectName("muted")
        clam_intro.setWordWrap(True)
        clam_layout.addWidget(clam_intro)

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
            ("Sicherheitsereignisse", "◈"),
            ("Erweiterte Sicherheit", "✦"),
            ("Quarantäne", "⬡"),
            ("Systemschutz", "▣"),
            ("Reparatur & Wiederherstellung", "⚒"),
            ("Netzwerk", "◎"),
            ("Dateiwerkzeuge", "▤"),
            ("Alarm & Audio", "♫"),
            ("Einstellungen", "⚙"),
        ]
        for label, glyph in self._navigation_labels:
            self.side_nav.addItem(QListWidgetItem(f"{glyph}   {label}"))
        self.side_nav.currentRowChanged.connect(tabs.setCurrentIndex)
        tabs.currentChanged.connect(self.side_nav.setCurrentRow)
        self.side_nav.setCurrentRow(0)
        layout.addWidget(tabs, 1)
        note=QLabel("LunaSecurity führt Prüfungen nachvollziehbar aus. Rootkit- und Integritätsprüfungen können Administratorrechte benötigen. Funde werden nicht automatisch gelöscht."); note.setObjectName("muted"); note.setWordWrap(True); layout.addWidget(note)

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
            chooser.setWindowTitle("Scan-Ziel auswählen")
            chooser.setText("Was möchtest du scannen?")
            file_btn = chooser.addButton("Datei auswählen", QMessageBox.ButtonRole.AcceptRole)
            folder_btn = chooser.addButton("Ordner auswählen", QMessageBox.ButtonRole.ActionRole)
            chooser.addButton(QMessageBox.StandardButton.Cancel)
            chooser.exec()
            clicked = chooser.clickedButton()
            options = QFileDialog.Option.DontUseNativeDialog
            if clicked is file_btn:
                target, _ = _choose_file(self, "Datei zum Scannen auswählen", Path.home())
                if not target:
                    self.log.append("Dateiauswahl abgebrochen; kein Scan gestartet.")
                    return
            elif clicked is folder_btn:
                target = _choose_directory(self, "Ordner zum Scannen auswählen", Path.home())
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

        self.scan_button.setEnabled(False); self.home_button.setEnabled(False); self.system_scan_button.setEnabled(False); self.update_button.setEnabled(False); self.progress.show(); self.cancel_scan_button.setEnabled(True)
        self.log.append(f"\nScan gestartet: {target_label}")
        scan_options = {
            "detect_pua": self.detect_pua_check.isChecked(),
            "heuristics": self.heuristics_check.isChecked(),
            "hidden_files": self.hidden_files_check.isChecked(),
            "large_files": self.large_files_check.isChecked(),
            "recursive": self.recursive_check.isChecked(),
        }
        profile = self.scan_profile.currentText()
        if profile == "Schnellscan":
            # Bewusst schlank: keine PUP-Suche, keine versteckten Dateien,
            # keine großen Dateien und nur die direkte Ordnerebene.
            scan_options.update({"detect_pua": False, "heuristics": False,
                                 "hidden_files": False, "large_files": False,
                                 "recursive": False})
        elif profile == "Komplettscan":
            # Vollständige ClamAV-Prüfung mit erweiterten Erkennungen und Limits.
            scan_options.update({"detect_pua": True, "heuristics": True,
                                 "hidden_files": True, "large_files": True,
                                 "recursive": True})
        if full_scan:
            # Home-Scan umfasst auch versteckte Dateien und alle Unterordner.
            scan_options.update({"hidden_files": True, "recursive": True})
        self.scan_monitor = ClamScanMonitor(target_label, self, cancel_callback=self.cancel_scan)
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
            return worker.run_command([pkexec, helper], 35)
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
        if action != "status":
            self.realtime_button.setEnabled(False)
            self.realtime_status.setText("Echtzeitschutz: Hintergrundauftrag läuft …")
            self.log.append("\nEchtzeitschutz wird im Hintergrund " + ("aktiviert …" if action == "enable" else "deaktiviert …"))
        worker.start()

    def refresh_realtime_status(self):
        self._start_realtime_worker("status")

    def toggle_realtime(self):
        if self.realtime_worker and self.realtime_worker.isRunning():
            return
        active = self.realtime_status.text().endswith("Aktiv")
        self._start_realtime_worker("disable" if active else "enable")

    @Slot(str, bool, bool)
    def realtime_finished(self, message, active, success):
        self.realtime_status.setText("Echtzeitschutz: " + ("Aktiv" if active else ("Aus" if success else "Status unklar")))
        if success:
            self.realtime_indicator.setStyleSheet(
                "font-size:22px;font-weight:900;color:" + ("#28e66b" if active else "#ff3b45") + ";padding-left:5px;padding-right:5px;"
            )
            self.realtime_indicator.setToolTip("Echtzeitschutz ist aktiv" if active else "Echtzeitschutz ist ausgeschaltet")
        else:
            self.realtime_indicator.setStyleSheet("font-size:22px;font-weight:900;color:#e0a52b;padding-left:5px;padding-right:5px;")
            self.realtime_indicator.setToolTip("Status des Echtzeitschutzes konnte nicht ermittelt werden")
        self.realtime_button.setText("Echtzeitschutz deaktivieren" if active else "Echtzeitschutz aktivieren")
        self.realtime_button.setEnabled(True)
        if message and message != "Status geprüft.":
            self.log.append(message)
        if not success:
            self.log.append("Hinweis: Der Dienststatus konnte nicht sicher bestätigt werden.")

    def report_detections(self, output, source="Manueller Scan"):
        """Persist ClamAV FOUND lines, ignoring paths just resolved by the user."""
        added = 0
        if not hasattr(self, "_resolved_detection_paths"):
            self._resolved_detection_paths = set()
        for line in str(output).splitlines():
            line = line.strip()
            if not line or not (line.endswith("FOUND") or " FOUND " in line):
                continue
            path = sec.detection_path(line)
            if not path:
                continue
            # A real-time log line can arrive just after the file was moved.
            # Do not recreate the just-resolved finding in the same session.
            if str(Path(path).expanduser().resolve(strict=False)) in self._resolved_detection_paths:
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
        if not events:
            self.events_view.addItem("Noch keine erkannten Bedrohungen gespeichert.")
            self.alert_banner.hide()
        else:
            self.alert_banner.setText(f"⚠ {len(events)} gespeicherte Sicherheitsereignisse – Details im Tab „Sicherheitsereignisse“")
            self.alert_banner.show()

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
        try:
            result = sec.restore_quarantined(entry_id)
            self.log.append(result)
            self.refresh_quarantine()
        except Exception as exc:
            QMessageBox.critical(self, "Wiederherstellen fehlgeschlagen", str(exc))

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
            with self._realtime_log_path.open("r", errors="replace") as handle:
                handle.seek(self._realtime_log_offset)
                chunk = handle.read()
                self._realtime_log_offset = handle.tell()
            for line in chunk.splitlines():
                if " FOUND" in line or line.strip().endswith("FOUND"):
                    self.report_detections(line, source="Echtzeitschutz")
        except OSError:
            return

    def update_signatures_now(self):
        if self.worker and self.worker.isRunning():
            QMessageBox.information(self, "LunaSecurity", "Es läuft bereits eine Sicherheitsaufgabe.")
            return
        self.scan_button.setEnabled(False); self.home_button.setEnabled(False); self.system_scan_button.setEnabled(False); self.update_button.setEnabled(False); self.progress.show()
        self.log.append("\nSignaturaktualisierung mit freshclam gestartet …")
        self.worker = ScanWorker(update_only=True)
        self.worker.result.connect(self.signature_update_finished)
        self.worker.start()

    def signature_update_finished(self, text):
        self.progress.hide()
        self.scan_button.setEnabled(True); self.home_button.setEnabled(True)
        self.system_scan_button.setEnabled(True); self.update_button.setEnabled(True)
        self.cancel_scan_button.setEnabled(False)
        self.log.append(text)
        self.log.append("Signaturaktualisierung beendet.")
        self.signature_version_label.setText("Installierte Virensignaturen: " + signature_database_versions())
        self._show_test_report("Signaturaktualisierung", text)

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
        self.progress.hide(); self.scan_button.setEnabled(True); self.home_button.setEnabled(True); self.system_scan_button.setEnabled(True); self.update_button.setEnabled(True); self.cancel_scan_button.setEnabled(False)
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
        if "Scan wurde vom Benutzer abgebrochen" not in text:
            self.report_detections(text)
        self.log.append("Scan-Aufgabe beendet.")
        self.signature_version_label.setText("Installierte Virensignaturen: " + signature_database_versions())
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
        self.progress.show()
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
            try: self.log.append(sec.quarantine_file(path))
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
    QLocale.setDefault(QLocale(QLocale.Language.German, QLocale.Country.Germany))
    app=QApplication(qt_args); app.setApplicationName("LunaSecurity"); app.setQuitOnLastWindowClosed(False)
    german_translator = GermanQtTranslator(app)
    app.installTranslator(german_translator)
    dialog_button_fix = GermanDialogButtonFix(app)
    app.installEventFilter(dialog_button_fix)
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
