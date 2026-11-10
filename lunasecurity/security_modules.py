"""Linux security checks and explicit, user-confirmed quarantine helpers."""
from __future__ import annotations
import os, shutil, subprocess, hashlib, sqlite3, time, signal
from pathlib import Path

DATA = Path.home() / '.local' / 'share' / 'LunaSecurity'
QUARANTINE = DATA / 'quarantine'
DB = DATA / 'security.db'

def run_command(args, timeout=1800):
    exe = shutil.which(args[0])
    if not exe:
        return f"Nicht installiert: {args[0]}"
    try:
        p = subprocess.run([exe, *args[1:]], capture_output=True, text=True, timeout=timeout)
        return (p.stdout + '\n' + p.stderr).strip() or f"Beendet mit Exit-Code {p.returncode}"
    except Exception as exc:
        return f"Fehler bei {args[0]}: {exc}"

def admin_command(args, timeout=3600):
    if not shutil.which(args[0]):
        return f"Nicht installiert: {args[0]}"
    pkexec = shutil.which('pkexec')
    if not pkexec:
        return 'Administratorrechte benötigt; pkexec ist nicht installiert.'
    try:
        p = subprocess.run([pkexec, shutil.which(args[0]), *args[1:]], capture_output=True, text=True, timeout=timeout)
        return ((p.stdout + '\n' + p.stderr).strip() or 'Keine Ausgabe') + f'\nExit-Code: {p.returncode}'
    except Exception as exc:
        return f'Fehler: {exc}'

def rootkit_checks(worker=None):
    """Run rkhunter and chkrootkit sequentially with cancellation support."""
    parts = ["Rootkit-Prüfung: rkhunter und chkrootkit werden nacheinander gestartet."]
    tools = (
        ("rkhunter", ["rkhunter", "--check", "--sk"]),
        ("chkrootkit", ["chkrootkit"]),
    )
    for name, command in tools:
        if worker is not None and worker._cancel_event.is_set():
            parts.append("Rootkit-Prüfung vom Benutzer abgebrochen.")
            break
        executable = shutil.which(name)
        if not executable:
            parts.append(f"### {name}\\nNicht installiert. Installiere das Debian-Paket {name}.")
            continue
        pkexec = shutil.which("pkexec")
        if not pkexec:
            parts.append(f"### {name}\\nAdministratorrechte benötigt; pkexec ist nicht installiert.")
            continue
        args = [pkexec, executable, *command[1:]]
        result = worker.run_command(args, 3600) if worker is not None else admin_command(command, 3600)
        parts.append(f"### {name}\\n{result}")
        if worker is not None and worker._cancel_event.is_set():
            parts.append("Rootkit-Prüfung vom Benutzer abgebrochen.")
            break
    return "\\n\\n".join(parts)


def integrity_check(worker=None):
    """Run AIDE via a root helper that tracks and owns its complete process group."""
    helper = Path('/usr/lib/lunasecurity/aide-check-helper')
    if not helper.is_file():
        helper = Path(__file__).resolve().parent.parent / 'scripts' / 'aide-check-helper'
    if not helper.is_file():
        return ('AIDE-Prüfprogramm fehlt. Bitte LunaSecurity vollständig installieren '
                'oder das Quellarchiv unverändert verwenden.')
    pkexec = shutil.which('pkexec')
    if not pkexec:
        return ('Administratorrechte benötigt: pkexec ist nicht installiert. '
                'Installiere das Debian-Paket policykit-1 und starte einen '
                'PolicyKit-Authentifizierungsagenten.')
    if worker is not None and worker._cancel_event.is_set():
        return 'AIDE-Prüfung abgebrochen. Es wurde kein Prüfergebnis erzeugt.'
    try:
        proc = subprocess.Popen([pkexec, str(helper)], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, start_new_session=True)
        if worker is not None:
            worker.set_process(proc)
        try:
            out, err = proc.communicate(timeout=3600)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
                out, err = proc.communicate(timeout=4)
            except subprocess.TimeoutExpired:
                try: os.killpg(proc.pid, signal.SIGKILL)
                except OSError: pass
                out, err = proc.communicate()
            return 'AIDE-Prüfung abgebrochen: Zeitüberschreitung nach 60 Minuten.'
        if worker is not None and worker._cancel_event.is_set():
            return ('AIDE-Prüfung vom Benutzer abgebrochen. Das Teilergebnis ist '
                    'unvollständig und nicht als vollständige Integritätsprüfung zu werten.')
    except Exception as exc:
        return f'AIDE konnte nicht mit Administratorrechten gestartet werden: {exc}'
    output = (out + ('\n' + err if err else '')).strip()
    if proc.returncode != 0:
        detail = output or 'Keine weitere Fehlermeldung erhalten.'
        if proc.returncode in (126, 127):
            return ('AIDE-Prüfung nicht gestartet. Die Administratorabfrage wurde '
                    'abgebrochen oder konnte nicht geöffnet werden.\n' + detail)
        return f'AIDE-Prüfung fehlgeschlagen (Exit-Code {proc.returncode}).\n{detail}'
    low = output.lower()
    if ('database' in low and any(term in low for term in ('not found', 'does not exist', 'no such file'))):
        output += ('\n\nAIDE-Basisdatenbank fehlt. Lege sie erst nach Prüfung des '
                   'sauberen Systemzustands mit sudo aideinit an und aktiviere die '
                   'erzeugte Referenzdatenbank gemäß den Debian-Hinweisen.')
    return output or 'AIDE-Prüfung beendet. Das Prüfprogramm hat keine Textausgabe geliefert.'

def _admin_capture(args, timeout=60):
    """Run one read-only diagnostic command with an explicit PolicyKit prompt."""
    exe = shutil.which(args[0])
    if not exe:
        return None, '', f"Nicht installiert: {args[0]}"
    pkexec = shutil.which('pkexec')
    if not pkexec:
        return None, '', 'pkexec ist nicht installiert; Administratorrechte können nicht angefordert werden.'
    try:
        proc = subprocess.run([pkexec, exe, *args[1:]], capture_output=True, text=True, timeout=timeout)
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return None, '', f"Zeitüberschreitung bei {' '.join(args)}."
    except Exception as exc:
        return None, '', f"Fehler bei {' '.join(args)}: {exc}"


def network_audit():
    """Run a single elevated, read-only network/firewall audit and summarize it."""
    helper = Path('/usr/lib/lunasecurity/network-audit-helper')
    if not helper.is_file():
        # Also support running directly from an unpacked source archive.
        helper = Path(__file__).resolve().parent.parent / 'scripts' / 'network-audit-helper'
    if not helper.is_file():
        return ('NETZWERK- UND FIREWALL-CHECK\n\n'
                'NICHT VOLLSTÄNDIG GEPRÜFT – das Admin-Prüfprogramm fehlt. '
                'Bitte LunaSecurity vollständig installieren.')
    pkexec = shutil.which('pkexec')
    if not pkexec:
        return ('NETZWERK- UND FIREWALL-CHECK\n\n'
                'NICHT VOLLSTÄNDIG GEPRÜFT – pkexec ist nicht installiert. '
                'Die Administratorabfrage kann nicht gestartet werden.')
    try:
        proc = subprocess.run([pkexec, str(helper)], capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired:
        return 'NETZWERK- UND FIREWALL-CHECK\n\nNICHT VOLLSTÄNDIG GEPRÜFT – Zeitüberschreitung bei der Administratorprüfung.'
    except Exception as exc:
        return f'NETZWERK- UND FIREWALL-CHECK\n\nNICHT VOLLSTÄNDIG GEPRÜFT – Administratorprüfung fehlgeschlagen: {exc}'
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or '').strip()
        return ('NETZWERK- UND FIREWALL-CHECK\n\n'
                'NICHT VOLLSTÄNDIG GEPRÜFT – Administratorrechte wurden nicht erteilt '
                f'(Exit-Code {proc.returncode}).\n{detail}')

    def extract(begin, end, status_prefix):
        output = proc.stdout
        if begin not in output or end not in output or status_prefix not in output:
            return None, '', 'Ungültige oder unvollständige Ausgabe des Admin-Prüfprogramms.'
        chunk = output.split(begin, 1)[1].split(end, 1)[0].strip()
        status_line = next((line for line in output.splitlines() if line.startswith(status_prefix)), '')
        try:
            code = int(status_line.split('=', 1)[1])
        except (ValueError, IndexError):
            return None, chunk, 'Exit-Code konnte nicht gelesen werden.'
        return code, chunk, ''

    ss_code, ss_out, ss_error = extract('__LUNA_SS_BEGIN__', '__LUNA_SS_END__', '__LUNA_SS_STATUS__')
    nft_code, nft_out, nft_error = extract('__LUNA_NFT_BEGIN__', '__LUNA_NFT_END__', '__LUNA_NFT_STATUS__')
    sections = [
        'NETZWERK- UND FIREWALL-CHECK',
        'Administratorprüfung erfolgreich. Beide Teilprüfungen wurden in einer einzigen Passwortabfrage gestartet.',
        'Es werden ausschließlich Informationen gelesen; Firewall-Regeln werden nicht verändert.'
    ]
    sections.append('### 1. Lauschende Netzwerkports und Prozesse')
    entries = []
    if ss_code != 0:
        sections.append('ERGEBNIS: NICHT VOLLSTÄNDIG PRÜFBAR\n' + (ss_error or ss_out or f'ss Exit-Code: {ss_code}'))
    else:
        lines = [line for line in ss_out.splitlines() if line.strip()]
        entries = lines[1:] if lines and lines[0].lstrip().startswith('Netid') else lines
        wildcard = [line for line in entries if ('0.0.0.0:' in line or '[::]:' in line or '*:' in line)]
        sections.append(f'ERGEBNIS: {len(entries)} lauschende Socket(s) gefunden; davon {len(wildcard)} an allgemeinen Netzwerkadressen gebunden.')
        sections.append('Ein offener Listener ist nicht automatisch gefährlich. Wichtig sind Dienst, Bind-Adresse und Firewall-Regeln.')
        sections.append(ss_out or 'Keine lauschenden Ports gemeldet.')

    sections.append('### 2. Firewall-Regeln (nftables)')
    nft_ok = nft_code == 0
    input_policies = []
    if not nft_ok:
        sections.append('ERGEBNIS: NICHT VOLLSTÄNDIG PRÜFBAR\n' + (nft_error or nft_out or f'nft Exit-Code: {nft_code}'))
    else:
        import re
        # nft prints base-chain declaration and policy on one line in normal output.
        for line in nft_out.splitlines():
            if re.search(r'\bhook\s+input\b', line):
                match = re.search(r'\bpolicy\s+(drop|reject|accept)\b', line)
                input_policies.append(match.group(1).lower() if match else 'unbekannt')
        if not nft_out.strip():
            firewall_status = 'WARNUNG'
            firewall_reason = 'Der nftables-Regelsatz ist leer. Eine aktive nftables-Eingangsfilterung ist nicht nachgewiesen.'
        elif not input_policies:
            firewall_status = 'WARNUNG'
            firewall_reason = 'Es wurde keine nftables-Eingangskette (hook input) gefunden. Eine Eingangsfilterung ist nicht nachgewiesen.'
        elif all(policy in ('drop', 'reject') for policy in input_policies):
            firewall_status = 'GUT'
            firewall_reason = 'Alle erkannten nftables-Eingangsketten verwenden standardmäßig DROP/REJECT.'
        elif any(policy == 'accept' for policy in input_policies):
            firewall_status = 'WARNUNG'
            firewall_reason = 'Mindestens eine nftables-Eingangskette verwendet standardmäßig ACCEPT. Einzelne Sperrregeln können trotzdem vorhanden sein.'
        else:
            firewall_status = 'PRÜFEN'
            firewall_reason = 'Die Standardrichtlinie mindestens einer Eingangskette ließ sich nicht eindeutig bestimmen.'
        sections.append(f'ERGEBNIS: {firewall_status} – {firewall_reason}')
        sections.append(f'Erkannte nftables-Eingangsketten: {len(input_policies)}; Richtlinien: {", ".join(input_policies) if input_policies else "keine"}')
        sections.append(nft_out or 'Keine nftables-Regeln vorhanden.')

    # Ergänzende lokale Diagnose: Adressen, IPv4-/IPv6-Routen und DNS.
    for title, begin, end in (
        ('3. Netzwerkschnittstellen und IP-Adressen', '__LUNA_ADDR_BEGIN__', '__LUNA_ADDR_END__'),
        ('4. Standard- und IPv6-Routen', '__LUNA_ROUTE_BEGIN__', '__LUNA_ROUTE_END__'),
        ('5. DNS-Konfiguration', '__LUNA_DNS_BEGIN__', '__LUNA_DNS_END__'),
    ):
        if begin in proc.stdout and end in proc.stdout:
            content = proc.stdout.split(begin, 1)[1].split(end, 1)[0].strip()
            sections.append(f'### {title}\n' + (content or 'Keine Informationen geliefert.'))
        else:
            sections.append(f'### {title}\nNICHT VOLLSTÄNDIG GEPRÜFT – Diagnoseabschnitt fehlt.')

    sections.append('### GESAMTBEWERTUNG')
    if ss_code != 0 or not nft_ok:
        sections.append('NICHT VOLLSTÄNDIG GEPRÜFT – mindestens eine Teilprüfung war nicht erfolgreich. Bitte pkexec, nftables und iproute2 prüfen.')
    elif firewall_status == 'GUT':
        sections.append('GUT – die lokalen Eingangsketten blockieren standardmäßig nicht ausdrücklich erlaubten Verkehr. Die gefundenen Ports und Dienste trotzdem prüfen.')
    else:
        sections.append(f'{firewall_status} – {firewall_reason}')
    # Konkrete, bewusst nicht automatisch ausgeführte Handlungsempfehlungen.
    sections.append('### KONKRETE VERBESSERUNGSVORSCHLÄGE')
    tips = []
    if ss_code != 0:
        tips.append('Die Portprüfung war nicht vollständig. Erst die Ursache beheben und danach erneut prüfen. Diagnose: `sudo ss -tulpen`.')
    else:
        if wildcard:
            tips.append(
                f'{len(wildcard)} Listener sind an allen IPv4-/IPv6-Adressen gebunden. '
                'Prüfe jeden Prozess mit `sudo ss -tulpen`. Wird ein Dienst nur lokal benötigt, '
                'stelle ihn in seiner Dienstkonfiguration auf 127.0.0.1 bzw. ::1 um. '
                'Wenn er im LAN erreichbar sein muss, beschränke den Zugriff auf benötigte Quelladressen.'
            )
        else:
            tips.append('Es wurde kein Listener an einer allgemeinen Netzwerkadresse erkannt. '
                        'Prüfe trotzdem regelmäßig, ob neu installierte Dienste zusätzliche Ports öffnen.')
        ssh_listener = any(re.search(r'(?<!\\d)(?:\\*|0\\.0\\.0\\.0|\\[::\\]|\\[::\\]):22\\b', line) for line in entries)
        if ssh_listener:
            tips.append(
                'SSH lauscht offenbar auf einer allgemeinen Netzwerkadresse. Falls SSH benötigt wird: '
                'Zugriff möglichst auf vertrauenswürdige LAN-/VPN-Adressen begrenzen, '
                'Schlüsselanmeldung einrichten und erst nach erfolgreichem Test '
                '`PasswordAuthentication no` in einer SSH-Konfigurationsdatei erwägen. '
                'Vor Änderungen eine bestehende Sitzung offen halten und `sudo sshd -t` ausführen.'
            )
    if nft_ok:
        if not nft_out.strip() or not input_policies:
            tips.append(
                'Eine wirksame nftables-Eingangsfilterung ist nicht nachgewiesen. Prüfe zuerst '
                '`sudo systemctl status nftables` und `sudo nft list ruleset`. '
                'Richte anschließend eine passende Standardrichtlinie und ausdrücklich benötigte '
                'Freigaben ein. Nicht blind Regeln übernehmen: Bei SSH-/Fernzugriff besteht Aussperrgefahr.'
            )
        elif any(policy == 'accept' for policy in input_policies):
            tips.append(
                'Mindestens eine Eingangs-Basiskette erlaubt standardmäßig Pakete. Prüfe, ob dies '
                'beabsichtigt ist, und plane eine restriktive Allowlist: zuerst Loopback und '
                'ESTABLISHED/RELATED berücksichtigen, danach nur benötigte Dienste/Quellnetze freigeben. '
                'Regeln vor dem Aktivieren auf Syntax und Fernzugriff testen.'
            )
        elif all(policy in ('drop', 'reject') for policy in input_policies):
            tips.append(
                'Die erkannten Eingangsrichtlinien sind restriktiv (DROP/REJECT). Prüfe zusätzlich, '
                'ob jede benötigte Freigabe eng auf Port, Protokoll und Quellnetz begrenzt ist.'
            )
    else:
        tips.append('Die Firewall-Regeln konnten nicht vollständig gelesen werden. Prüfe nftables-Installation, '
                    'Dienststatus und die Administratorabfrage; bewerte die Firewall bis dahin nicht als sicher.')
    tips.append(
        'LunaSecurity nimmt keine dieser Änderungen automatisch vor. Sichere zuerst die aktuelle Konfiguration '
        '(`sudo nft list ruleset > ~/nftables-backup.txt`) und ändere Regeln nur, wenn du den Zweck kennst.'
    )
    sections.extend(f'• {tip}' for tip in tips)

    sections.append('Prüfumfang: lokale Socket-Listener/Prozesse, nftables-Regelsatz, Schnittstellen/IP-Adressen, IPv4-/IPv6-Routen und lokale DNS-Konfiguration. Nicht geprüft werden Router-/Provider-Firewalls, externe Erreichbarkeit aus dem Internet, DNS-Manipulation außerhalb des lokalen Systems oder die Sicherheit einzelner Dienste. Ein grünes Ergebnis ist keine vollständige Sicherheitsgarantie.')
    return '\n\n'.join(sections)

def firewall_guard_action(action, port=None, protocol=None):
    """Apply, persist, or roll back LunaSecurity-owned nftables port blocks."""
    helper = Path('/usr/lib/lunasecurity/network-audit-helper')
    if not helper.is_file():
        helper = Path(__file__).resolve().parent.parent / 'scripts' / 'network-audit-helper'
    if not helper.is_file():
        return 'Das Firewall-Hilfsprogramm fehlt. Bitte LunaSecurity vollständig installieren.'
    if action == 'block-port':
        if protocol not in ('tcp', 'udp') or not isinstance(port, int) or not 1 <= port <= 65535:
            return 'Ungültiger Port oder Protokoll.'
        if port == 22:
            return 'Port 22 (SSH) wird aus Sicherheitsgründen nicht automatisch gesperrt.'
        args = [str(helper), action, protocol, str(port)]
    elif action in ('persist', 'rollback'):
        args = [str(helper), action]
    else:
        return 'Unbekannte Firewall-Aktion.'
    pkexec = shutil.which('pkexec')
    if not pkexec:
        return 'pkexec ist nicht installiert; Administratorrechte können nicht angefordert werden.'
    try:
        proc = subprocess.run([pkexec, *args], capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return 'Zeitüberschreitung bei der Firewall-Aktion.'
    except Exception as exc:
        return f'Firewall-Aktion fehlgeschlagen: {exc}'
    output = (proc.stdout + '\\n' + proc.stderr).strip()
    if proc.returncode:
        return (output or f'Firewall-Aktion mit Exit-Code {proc.returncode} fehlgeschlagen.')
    return output or 'Firewall-Aktion abgeschlossen.'


def yara_scan(target):
    if not shutil.which('yara'):
        return 'YARA ist nicht installiert. Installiere yara und hinterlege eigene/verifizierte Regeldateien.'
    rules_dir = Path('/etc/lunasecurity/yara-rules')
    rules = sorted(rules_dir.glob('*.yar')) + sorted(rules_dir.glob('*.yara'))
    if not rules:
        return (f'Keine YARA-Regeln gefunden in {rules_dir}. '
                'Bitte zuerst in LunaSecurity auf „YARA-Regeln aktualisieren“ klicken.')
    output = [f'YARA-Regelsatz: {len(rules)} Regeldateien', f'Scan-Ziel: {target}', '']
    for rule in rules:
        result = run_command(['yara', '-r', str(rule), str(target)], 3600)
        if result:
            output.append(f'[{rule.name}]\\n{result}')
    output.append('YARA-Scan abgeschlossen. Treffer müssen anhand der Regelbeschreibung geprüft werden; sie sind nicht automatisch bestätigte Infektionen.')
    return '\\n'.join(output)


def detection_path(detail):
    """Extract a ClamAV/YARA-style FOUND path from a detection log line."""
    line = str(detail).strip()
    if not line.endswith("FOUND"):
        return None
    # ClamAV prints: /path/to/file: Signature-Name FOUND
    prefix = line[:-len("FOUND")].rstrip()
    if ": " not in prefix:
        return None
    candidate = prefix.rsplit(": ", 1)[0].strip()
    if not candidate or candidate.startswith("ERROR"):
        return None
    return candidate

def delete_detected_file(path):
    candidate = Path(path).expanduser()
    if candidate.is_symlink():
        raise ValueError("Symbolische Links werden nicht gelöscht.")
    source = candidate.resolve(strict=True)
    if not source.is_file():
        raise ValueError("Nur reguläre Dateien können gelöscht werden.")
    source.unlink()
    return f"Datei gelöscht: {source}"

def _ensure_quarantine_db():
    DATA.mkdir(parents=True, exist_ok=True, mode=0o700)
    QUARANTINE.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        DATA.chmod(0o700)
        QUARANTINE.chmod(0o700)
    except OSError:
        pass
    with sqlite3.connect(DB) as db:
        db.execute('CREATE TABLE IF NOT EXISTS quarantine (id INTEGER PRIMARY KEY, original TEXT, stored TEXT, sha256 TEXT, created INTEGER)')

def quarantine_entries():
    if not DB.exists():
        return []
    with sqlite3.connect(DB) as db:
        db.row_factory = sqlite3.Row
        rows = db.execute('SELECT id, original, stored, sha256, created FROM quarantine ORDER BY created DESC').fetchall()
    return [{
        "id": row["id"], "original": row["original"], "stored": row["stored"],
        "sha256": row["sha256"],
        "created_text": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(row["created"]))
    } for row in rows if Path(row["stored"]).is_file()]

def _quarantine_record(entry_id):
    if not DB.exists():
        raise ValueError("Quarantäne ist leer.")
    with sqlite3.connect(DB) as db:
        row = db.execute('SELECT id, original, stored, sha256 FROM quarantine WHERE id=?', (int(entry_id),)).fetchone()
    if not row:
        raise ValueError("Quarantäne-Eintrag wurde nicht gefunden.")
    stored = Path(row[2])
    # Never follow symlinks or act on files outside the quarantine directory.
    if stored.is_symlink() or stored.parent.resolve() != QUARANTINE.resolve():
        raise ValueError("Ungültiger Quarantänepfad; Aktion verweigert.")
    if not stored.is_file():
        raise FileNotFoundError("Die isolierte Datei ist nicht mehr vorhanden.")
    return row, stored

def restore_quarantined(entry_id):
    row, stored = _quarantine_record(entry_id)
    original = Path(row[1])
    if original.exists() or original.is_symlink():
        raise FileExistsError(f"Am ursprünglichen Ort existiert bereits eine Datei: {original}")
    original.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(stored), str(original))
    try:
        original.chmod(0o600)
    except OSError:
        pass
    with sqlite3.connect(DB) as db:
        db.execute('DELETE FROM quarantine WHERE id=?', (int(entry_id),))
    return f"Datei wiederhergestellt: {original}"

def delete_quarantined(entry_id):
    row, stored = _quarantine_record(entry_id)
    stored.unlink()
    with sqlite3.connect(DB) as db:
        db.execute('DELETE FROM quarantine WHERE id=?', (int(entry_id),))
    return f"Isolierte Datei endgültig gelöscht: {row[1]}"

def quarantine_file(path):
    candidate = Path(path).expanduser()
    if candidate.is_symlink():
        raise ValueError('Symbolische Links werden aus Sicherheitsgründen nicht in Quarantäne verschoben.')
    source = candidate.resolve(strict=True)
    if not source.is_file():
        raise ValueError('Nur reguläre Dateien können in Quarantäne verschoben werden.')
    _ensure_quarantine_db()
    digest_obj = hashlib.sha256()
    with source.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest_obj.update(chunk)
    digest = digest_obj.hexdigest()
    dest = QUARANTINE / f'{int(time.time())}_{digest[:16]}_{source.name}'
    counter = 1
    while dest.exists():
        dest = QUARANTINE / f'{int(time.time())}_{digest[:16]}_{counter}_{source.name}'
        counter += 1
    shutil.move(str(source), str(dest))
    os.chmod(dest, 0o600)
    with sqlite3.connect(DB) as db:
        db.execute('INSERT INTO quarantine(original,stored,sha256,created) VALUES(?,?,?,?)',
                   (str(source), str(dest), digest, int(time.time())))
    return f'In Quarantäne verschoben:\\n{source}\\nSHA-256: {digest}\\nAblage: {dest}'

def quarantine_list():
    if not DB.exists(): return 'Quarantäne ist leer.'
    with sqlite3.connect(DB) as db:
        rows=db.execute('SELECT original,stored,sha256,created FROM quarantine ORDER BY created DESC').fetchall()
    if not rows: return 'Quarantäne ist leer.'
    return '\n'.join(f'{r[0]} -> {r[1]} | SHA256 {r[2]} | {time.strftime("%Y-%m-%d %H:%M",time.localtime(r[3]))}' for r in rows)

def system_audit(worker=None):
    checks = [
      ('Autostart / systemd user units', ['systemctl','--user','list-unit-files','--state=enabled']),
      ('Systemdienste', ['systemctl','list-unit-files','--state=enabled']),
      ('Cronjobs des Benutzers', ['crontab','-l']),
      ('Lokale Login-Konten', ['getent','passwd']),
      ('Fehlgeschlagene SSH-Anmeldungen (journal)', ['journalctl','-u','ssh','--since','24 hours ago','--no-pager']),
    ]
    results = []
    for title, command in checks:
        if worker is not None and worker._cancel_event.is_set():
            results.append("System-Audit vom Benutzer abgebrochen.")
            break
        result = worker.run_command(command, 120) if worker is not None else run_command(command, 120)
        results.append(f"### {title}\\n{result}")
    return "\\n\\n".join(results)

