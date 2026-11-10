"""GTK 3 StatusIcon tray implementation, following LunaKalender 1.4.0."""
from __future__ import annotations
import threading


class GtkStatusTray:
    """Run Gtk.StatusIcon in its own GLib/GTK thread, like LunaKalender.

    GTK signals are forwarded to the Qt main thread through supplied callbacks.
    Left click activates the main window; right click opens the GTK menu.
    """
    def __init__(self, on_show, on_quit, on_error=None):
        self.on_show = on_show
        self.on_quit = on_quit
        self.on_error = on_error
        self.icon = None
        self.menu = None
        self.status = "normal"
        self.Gtk = self.GLib = None
        self.ready = threading.Event()
        self.error = None
        self.thread = threading.Thread(target=self._run, daemon=True, name="LunaSecurity-GTK-Tray")
        self.thread.start()
        self.ready.wait(timeout=4)
        if self.error:
            raise RuntimeError(self.error)
        if self.icon is None:
            raise RuntimeError("GTK-System-Tray konnte nicht initialisiert werden")

    def _run(self):
        try:
            import gi
            gi.require_version("Gtk", "3.0")
            from gi.repository import Gtk, GLib
            self.Gtk, self.GLib = Gtk, GLib
            ok, _argv = Gtk.init_check([])
            if not ok:
                raise RuntimeError("Keine GTK-Tray-Sitzung verfügbar")
            icon = Gtk.StatusIcon()
            icon.set_from_icon_name("security-high")
            icon.set_tooltip_text("LunaSecurity – Linux Security Suite")
            icon.set_visible(True)
            icon.connect("activate", lambda *_: self.on_show())

            menu = Gtk.Menu()
            show_item = Gtk.MenuItem(label="LunaSecurity anzeigen")
            show_item.connect("activate", lambda *_: self.on_show())
            menu.append(show_item)
            menu.append(Gtk.SeparatorMenuItem())
            quit_item = Gtk.MenuItem(label="LunaSecurity beenden")
            quit_item.connect("activate", lambda *_: self.on_quit())
            menu.append(quit_item)
            menu.show_all()
            icon.connect("popup-menu", lambda _icon, button, activate_time:
                         menu.popup(None, None, Gtk.StatusIcon.position_menu,
                                    icon, button, activate_time))
            self.icon, self.menu = icon, menu
            self.ready.set()
            Gtk.main()
        except Exception as exc:
            self.error = str(exc)
            self.ready.set()
            if self.on_error:
                self.on_error(self.error)

    def set_status(self, status="normal"):
        """Aktualisiert das Tray-Symbol thread-sicher je nach Sicherheitsstatus."""
        self.status = status if status in ("normal", "warning", "critical") else "normal"
        if self.GLib and self.icon:
            names = {"normal": "security-high", "warning": "dialog-warning", "critical": "dialog-error"}
            name = names[self.status]
            def _update():
                if self.icon:
                    self.icon.set_from_icon_name(name)
                    tips = {"normal": "LunaSecurity – Keine offenen Warnungen", "warning": "LunaSecurity – Sicherheitswarnung vorhanden", "critical": "LunaSecurity – Kritische Bedrohung erkannt"}
                    self.icon.set_tooltip_text(tips[self.status])
                return False
            self.GLib.idle_add(_update)

    def stop(self):
        """Blendet das GTK-Icon aus und beendet den GTK-Loop kontrolliert."""
        if self.GLib and self.Gtk:
            try:
                def _quit_tray():
                    try:
                        if self.icon:
                            self.icon.set_visible(False)
                    finally:
                        self.Gtk.main_quit()
                    return False
                self.GLib.idle_add(_quit_tray)
            except Exception:
                pass
        if self.thread and self.thread.is_alive() and threading.current_thread() is not self.thread:
            self.thread.join(timeout=2.0)
