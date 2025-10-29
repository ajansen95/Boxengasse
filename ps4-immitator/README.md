# 📦 PS4-Imitator — Paketaufzeichnung & Wiedergabe

Dieses kleine Projekt enthält zwei Hilfsprogramme zum Aufzeichnen und zur Wiedergabe von UDP-Paketen (z. B. von einer PS4).

## 📝 Übersicht

- `savePS4packets.py` — Lauscht auf einem UDP-Port und speichert empfangene Pakete in einer JSONL-Datei.
- `playPS4packets.py` — Liest die JSONL-Datei und sendet die Pakete in ähnlichen Zeitabständen wieder aus (Replay / Imitation).

## 📁 Format der Persistenz (JSONL)

Jede Zeile in der Datei ist ein JSON-Objekt (JSONL). Felder pro Eintrag:

- `timestamp` — Epoch-Zeit (float), Zeitpunkt des Empfangs (time.time()).
- `interval` — Sekunden seit dem vorherigen Paket (float). Nützlich für Replay.
- `from` — Quelladresse als `IP:Port` (string).
- `length` — Länge des Payloads in Bytes (int).
- `payload_b64` — Payload binär, Base64-kodiert (string).

Hinweis: Base64 vergrößert Binärdaten um ~33% (4/3).

## ⚙️ `savePS4packets.py` — Optionen & Verhalten

Beschreibung: Lauscht auf UDP (standard: `0.0.0.0:20777`) und schreibt empfangene Pakete in eine Datei unter `ps4-immitator/recordings` (Standarddatei: `recordings/ps4_packets.jsonl`).

Wichtige CLI-Optionen:

- `--bind-ip` (default: `0.0.0.0`) — IP zum Binden.
- `--port` (default: `20777`) — UDP-Port.
- `--out-file` (default: `recordings/ps4_packets.jsonl`) — Zieldatei (innerhalb des `ps4-immitator/recordings`-Ordners als Standard).

Schreib-/Durability-Optionen (neu hinzugefügt, empfohlen für längere Läufe):

- `--flush-every N` (default: `100`) — Führe `f.flush()` nach N Paketen aus.
- `--flush-interval T` (default: `1.0`) — Mindestens alle T Sekunden flushen.
- `--fsync-every-seconds S` (default: `10.0`) — Führe `os.fsync()` alle S Sekunden aus (0 = deaktiviert).
- `--fsync-every-packets M` (default: `0`) — Führe `os.fsync()` nach M Paketen aus (0 = deaktiviert).

Standardverhalten: Das Skript puffert Writes und führt nicht nach jedem Paket `flush()`/`fsync()` aus — dadurch werden Syscalls reduziert und die Performance bei hoher Paketrate verbessert. Beim Beenden (Strg+C) wird ein finaler `flush()` und ggf. `fsync()` ausgeführt.

Tipps:
- Für typische Läufe (20 Hz, ~1 Stunde, 100k Pakete) sind die Default-Werte sinnvoll. Wenn du maximale Sicherheit gegen Datenverlust bei Crash willst, erhöhe `--fsync-every-seconds` oder setze `--fsync-every-packets` (>0), beachte aber höhere I/O-Kosten.
- Wenn du eine Rotation brauchst, kannst du das Skript erweitern (nicht standardmäßig implementiert).

## ▶️ `playPS4packets.py` — Optionen & Verhalten

Beschreibung: Liest eine JSONL-Datei (standardmäßig aus `recordings/ps4_packets.jsonl`) und sendet die Pakete über UDP an die angegebene Zieladresse. Die Wiedergabe respektiert die gespeicherten `interval`-Werte (falls vorhanden) — sonst werden Intervalle aus `timestamp` berechnet.

Wichtige CLI-Optionen:

- `--in-file` (default: `recordings/ps4_packets.jsonl`) — Eingabedatei.
- `--dest-ip` (default: `127.0.0.1`) — Ziel-IP für das Senden.
- `--dest-port` (default: `20777`) — Ziel-Port.
- `--speed` (default: `1.0`) — Geschwindigkeitsfaktor: `1.0` = Originalintervalle, `2.0` = doppelt so schnell (Intervalle halbiert), `0.5` = halb so schnell (Intervalle verdoppelt).

Hinweise:
- Das Skript sendet nur den Payload an die konfigurierte Zieladresse; es simuliert nicht die originale Quelladresse (Source-IP Spoofing ist nicht im Scope).
- Negative Intervalle werden auf 0 gesetzt (schützt vor nicht-monotonen Zeitstempeln).

## 🛠️ Beispiele

Aufzeichnen (Standardport 20777):

```bash
python savePS4packets.py --port 20777 --out-file recordings/ps4_packets.jsonl
```

Wiedergabe lokal (originale Geschwindigkeit):

```bash
python playPS4packets.py --in-file recordings/ps4_packets.jsonl --dest-ip 127.0.0.1 --dest-port 20777 --speed 1.0
```

Wiedergabe doppelt so schnell:

```bash
python playPS4packets.py --in-file recordings/ps4_packets.jsonl --dest-ip 127.0.0.1 --dest-port 20777 --speed 2.0
```

Beispiel für robustes Schreiben (häufiges Logging, aber seltener fsync):

```bash
python savePS4packets.py --out-file recordings/ps4_packets.jsonl --flush-every 200 --flush-interval 2.0 --fsync-every-seconds 30
```

## ❗ Wichtige Hinweise & Troubleshooting

- Stoppen: Beende `savePS4packets.py` mit Strg+C — das löst einen finalen Flush (und fsync falls konfiguriert) aus.
- Performance: Bei 20 Hz ist das Skript mit Standard-Pufferwerten gut geeignet; bei deutlich höheren Raten empfiehlt sich ein Background-Writer (Queue + Thread) oder Speicherung in sqlite.
- Crash-Sicherheit: `f.flush()` gibt Daten an das OS, `os.fsync()` schreibt sie auf das physische Medium. `fsync` ist teurer, aber sicherer.
- Große Dateien: Für sehr große Archive (mehrere 100s MB oder mehr) empfiehlt sich Rotation oder Migration zu SQLite.

## 📌 Weiteres / Roadmap

- Optional: Rotation (`--max-size`, timestamped files).
- Optional: Background-Writer (Queue + Thread) für maximale Entkopplung von Empfang und Disk.
- Optional: SQLite-Mode für bessere Abfragen und ACID-Sicherheit.

---

Wenn du möchtest, implementiere ich die Rotation oder die Background-Writer-Option als nächsten Schritt — welche hättest du lieber?
