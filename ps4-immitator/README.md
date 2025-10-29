Dieses kleine Projekt enthält zwei Hilfsprogramme für das Aufzeichnen und Wiedergabe von UDP-Paketen (z. B. von einer PS4):

1) savePS4packets.py
- Lauscht auf einem UDP-Port und schreibt jedes empfangene Paket als JSON-Zeile (JSONL) in eine Datei.
- Jede Zeile enthält: timestamp (epoch float), from (IP:Port), length, payload_b64 (Base64-kodiert).

2) playPS4packets.py
- Liest die JSONL-Datei und sendet die Pakete über UDP in ungefähr den gleichen Intervallen wie beim Empfang.
- Optionen:
  --in-file    Pfad zur JSONL-Datei (default: ps4_packets.jsonl)
  --dest-ip    Ziel-IP zum Senden (default: 127.0.0.1)
  --dest-port  Ziel-Port (default: 20777)
  --speed      Geschwindigkeitsfaktor (1.0 = originalgeschwindigkeit)

Beispiele:

# Paketaufzeichnung starten (Port 20777 auf allen Schnittstellen)
python savePS4packets.py --port 20777 --out-file ps4_packets.jsonl

# Wiedergabe (an localhost:20777, originale Intervalle)
python playPS4packets.py --in-file ps4_packets.jsonl --dest-ip 127.0.0.1 --dest-port 20777 --speed 1.0

Hinweise:
- Die Datei ist JSONL: jede Zeile ein JSON-Objekt. Base64 wird verwendet, um Binärdaten sicher in Textdatei zu speichern.
- Wenn die Datei sehr groß wird, kann man sie rotieren oder in ein echtes DB-Format (sqlite) migrieren.
- Die Wiedergabe respektiert die ursprünglichen Zeitabstände zwischen den Paketen. Der Parameter `--speed` erlaubt Beschleunigung/Verlangsamung.

