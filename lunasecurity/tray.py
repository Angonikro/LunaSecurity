"""Native Qt system tray for LunaSecurity; GTK is not used."""
from __future__ import annotations

from PySide6.QtCore import QObject
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QStyle


class QtStatusTray(QObject):
    def __init__(self, on_show, on_quit, on_error=None, language="de"):
        super().__init__()
        self.on_show = on_show
        self.on_quit = on_quit
        self.language = language
        self.status = "normal"
        self.tray = QSystemTrayIcon(self)
        style = QApplication.style()
        self.icons = {
            "normal": QIcon.fromTheme(
                "security-high",
                style.standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton),
            ),
            "warning": style.standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning),
            "critical": style.standardIcon(QStyle.StandardPixmap.SP_MessageBoxCritical),
        }
        self.menu = QMenu()
        show_text = "Show LunaSecurity" if language == "en" else "LunaSecurity anzeigen"
        quit_text = "Quit LunaSecurity" if language == "en" else "LunaSecurity beenden"
        self.show_action = QAction(show_text, self.menu)
        self.show_action.triggered.connect(self.on_show)
        self.menu.addAction(self.show_action)
        self.menu.addSeparator()
        self.quit_action = QAction(quit_text, self.menu)
        self.quit_action.triggered.connect(self.on_quit)
        self.menu.addAction(self.quit_action)
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._activated)
        self.set_status("normal")
        self.tray.show()
        if not QSystemTrayIcon.isSystemTrayAvailable() and on_error:
            on_error("Qt meldet momentan kein verfügbares System-Tray.")

    def _activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger,
                      QSystemTrayIcon.ActivationReason.DoubleClick):
            self.on_show()

    def set_status(self, status="normal"):
        self.status = status if status in self.icons else "normal"
        tips = {
            "normal": ("LunaSecurity – No open warnings" if self.language == "en"
                       else "LunaSecurity – Keine offenen Warnungen"),
            "warning": ("LunaSecurity – Security warning present" if self.language == "en"
                        else "LunaSecurity – Sicherheitswarnung vorhanden"),
            "critical": ("LunaSecurity – Critical threat detected" if self.language == "en"
                         else "LunaSecurity – Kritische Bedrohung erkannt"),
        }
        self.tray.setIcon(self.icons[self.status])
        self.tray.setToolTip(tips[self.status])

    def isVisible(self):
        return self.tray.isVisible()

    def showMessage(self, *args, **kwargs):
        return self.tray.showMessage(*args, **kwargs)

    def hide(self):
        self.tray.hide()

    def stop(self):
        self.tray.hide()
        self.menu.deleteLater()
