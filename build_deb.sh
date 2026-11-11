#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
VERSION=$(sed -n 's/^__version__[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/p' "$ROOT/lunasecurity/__init__.py")
if [ -z "$VERSION" ]; then
    echo "Fehler: Versionsnummer in lunasecurity/__init__.py nicht gefunden." >&2
    exit 1
fi

BUILD=$(mktemp -d "${TMPDIR:-/tmp}/lunasecurity-build.XXXXXX")
DIST="$ROOT/dist"
OUTPUT="$DIST/lunasecurity_${VERSION}_all.deb"
trap 'rm -rf "$BUILD"' EXIT HUP INT TERM

mkdir -p "$BUILD/DEBIAN" \
    "$BUILD/usr/share/doc/lunasecurity" \
    "$BUILD/usr/lib/lunasecurity/lunasecurity" \
    "$BUILD/usr/bin" \
    "$BUILD/usr/share/applications" \
    "$BUILD/usr/share/pixmaps" \
    "$BUILD/usr/lib/systemd/system" \
    "$BUILD/usr/lib/lunasecurity" \
    "$DIST"

cp -a "$ROOT/lunasecurity/"*.py "$BUILD/usr/lib/lunasecurity/lunasecurity/"
install -m 0644 "$ROOT/README.md" "$BUILD/usr/share/doc/lunasecurity/README.md"
install -m 0644 "$ROOT/CHANGELOG.md" "$BUILD/usr/share/doc/lunasecurity/changelog.md"
install -m 0644 "$ROOT/debian/lunasecurity.desktop" "$BUILD/usr/share/applications/lunasecurity.desktop"
install -m 0644 "$ROOT/assets/lunasecurity.svg" "$BUILD/usr/share/pixmaps/lunasecurity.svg"

install -m 0755 "$ROOT/scripts/configure-realtime" "$BUILD/usr/lib/lunasecurity/configure-realtime"
install -m 0755 "$ROOT/scripts/lunasecurity-realtime" "$BUILD/usr/lib/lunasecurity/lunasecurity-realtime"
install -m 0644 "$ROOT/scripts/lunasecurity-realtime.service" "$BUILD/usr/lib/systemd/system/lunasecurity-realtime.service"
install -m 0644 "$ROOT/scripts/lunasecurity-firewall-guard.service" "$BUILD/usr/lib/systemd/system/lunasecurity-firewall-guard.service"

for helper in \
    aide-check-helper aide-cancel-helper network-audit-helper \
    package-repair-helper package-rollback-helper yara-update-helper \
    clamav-scan-helper clamav-scan-cancel-helper fail2ban-status-helper
do
    install -m 0755 "$ROOT/scripts/$helper" "$BUILD/usr/lib/lunasecurity/$helper"
done

cat > "$BUILD/usr/bin/lunasecurity" <<'LAUNCH'
#!/bin/sh
exec /usr/bin/python3 -c 'import sys; sys.path.insert(0, "/usr/lib/lunasecurity"); from lunasecurity.main import main; raise SystemExit(main())' "$@"
LAUNCH
chmod 0755 "$BUILD/usr/bin/lunasecurity"

cat > "$BUILD/DEBIAN/control" <<CONTROL
Package: lunasecurity
Version: $VERSION
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-pyside6.qtwidgets, python3-pyside6.qtprintsupport, python3-gi, gir1.2-gtk-3.0, clamav, clamav-daemon, clamav-freshclam, rkhunter, chkrootkit, pkexec, polkitd, aide, yara, nftables, iproute2, auditd, lynis, fail2ban
Recommends: mate-polkit
Maintainer: LunaSecurity Project <maintainer@example.invalid>
Description: Linux Security Suite mit Qt-Oberfläche und GTK-System-Tray
 Qt-/GTK-Tray-Sicherheitsanwendung mit ClamAV und optionalen Rootkit-Prüfwerkzeugen.
CONTROL
chmod 0644 "$BUILD/DEBIAN/control"
chmod 0755 "$BUILD/DEBIAN"

dpkg-deb --build --root-owner-group "$BUILD" "$OUTPUT"
echo "Fertig: $OUTPUT"
