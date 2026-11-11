#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
VERSION=0.4.30
BUILD="/mnt/data/lunasecurity_build_0.4.30_bannerfix"
DIST="/mnt/data/lunasecurity_dist_0.4.30_bannerfix"
rm -rf "$BUILD" "$DIST"
mkdir -p "$BUILD/DEBIAN" "$BUILD/usr/share/doc/lunasecurity" "$BUILD/usr/lib/lunasecurity/lunasecurity" "$BUILD/usr/bin" "$BUILD/usr/share/applications" "$BUILD/usr/share/pixmaps" "$BUILD/usr/lib/systemd/system" "$BUILD/usr/lib/lunasecurity" "$DIST"
cp -a "$ROOT/lunasecurity/"*.py "$BUILD/usr/lib/lunasecurity/lunasecurity/"
cat > "$BUILD/usr/bin/lunasecurity" <<'LAUNCH'
#!/bin/sh
exec /usr/bin/python3 -m lunasecurity "$@"
LAUNCH
chmod 0755 "$BUILD/usr/bin/lunasecurity"
install -m 0644 "$ROOT/README.md" "$BUILD/usr/share/doc/lunasecurity/README.md"
install -m 0644 "$ROOT/CHANGELOG.md" "$BUILD/usr/share/doc/lunasecurity/changelog.md"
install -m 0644 "$ROOT/debian/lunasecurity.desktop" "$BUILD/usr/share/applications/lunasecurity.desktop"
install -m 0644 "$ROOT/assets/lunasecurity.svg" "$BUILD/usr/share/pixmaps/lunasecurity.svg"
install -m 0755 "$ROOT/scripts/configure-realtime" "$BUILD/usr/lib/lunasecurity/configure-realtime"
install -m 0755 "$ROOT/scripts/lunasecurity-realtime" "$BUILD/usr/lib/lunasecurity/lunasecurity-realtime"
install -m 0644 "$ROOT/scripts/lunasecurity-realtime.service" "$BUILD/usr/lib/systemd/system/lunasecurity-realtime.service"
install -m 0644 "$ROOT/scripts/lunasecurity-firewall-guard.service" "$BUILD/usr/lib/systemd/system/lunasecurity-firewall-guard.service"
install -m 0755 "$ROOT/scripts/aide-check-helper" "$BUILD/usr/lib/lunasecurity/aide-check-helper"
install -m 0755 "$ROOT/scripts/aide-cancel-helper" "$BUILD/usr/lib/lunasecurity/aide-cancel-helper"
install -m 0755 "$ROOT/scripts/network-audit-helper" "$BUILD/usr/lib/lunasecurity/network-audit-helper"
install -m 0755 "$ROOT/scripts/package-repair-helper" "$BUILD/usr/lib/lunasecurity/package-repair-helper"
install -m 0755 "$ROOT/scripts/package-rollback-helper" "$BUILD/usr/lib/lunasecurity/package-rollback-helper"
install -m 0755 "$ROOT/scripts/yara-update-helper" "$BUILD/usr/lib/lunasecurity/yara-update-helper"
install -m 0755 "$ROOT/scripts/clamav-scan-helper" "$BUILD/usr/lib/lunasecurity/clamav-scan-helper"
install -m 0755 "$ROOT/scripts/clamav-scan-cancel-helper" "$BUILD/usr/lib/lunasecurity/clamav-scan-cancel-helper"
install -m 0755 "$ROOT/scripts/fail2ban-status-helper" "$BUILD/usr/lib/lunasecurity/fail2ban-status-helper"
printf '%s\n' '#!/usr/bin/python3' 'import sys' 'sys.path.insert(0, "/usr/lib/lunasecurity")' 'from lunasecurity.main import main' 'raise SystemExit(main())' > "$BUILD/usr/bin/lunasecurity-real"
chmod 0755 "$BUILD/usr/bin/lunasecurity-real"
# Launcher uses module path directly.
sed -i 's|exec /usr/bin/python3 -m lunasecurity|exec /usr/bin/python3 -c '\''import sys; sys.path.insert(0, "/usr/lib/lunasecurity"); from lunasecurity.main import main; raise SystemExit(main())'\''|' "$BUILD/usr/bin/lunasecurity"
printf '%s\n' 'Package: lunasecurity' "Version: $VERSION" 'Section: utils' 'Priority: optional' 'Architecture: all' 'Depends: python3, python3-pyside6.qtwidgets, python3-pyside6.qtprintsupport, python3-gi, gir1.2-gtk-3.0, clamav, clamav-daemon, clamav-freshclam, rkhunter, chkrootkit, pkexec, polkitd, aide, yara, nftables, iproute2, auditd, lynis, fail2ban' 'Recommends: mate-polkit' 'Maintainer: LunaSecurity Project <maintainer@example.invalid>' 'Description: Linux Security Suite mit Qt-Oberfläche und GTK-System-Tray' ' Qt-/GTK-Tray-Sicherheitsanwendung mit ClamAV und optionalen Rootkit-Prüfwerkzeugen.' > "$BUILD/DEBIAN/control"
chmod 0644 "$BUILD/DEBIAN/control"
chmod 0755 "$BUILD/DEBIAN"
chmod g-s "$BUILD/DEBIAN"
dpkg-deb --build --root-owner-group "$BUILD" "$DIST/lunasecurity_${VERSION}_all.deb"
