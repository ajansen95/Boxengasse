import argparse
import socket
import time
import json
import base64


def main():
    parser = argparse.ArgumentParser(description="Sende aufgezeichnete PS4-UDP-Pakete wieder (mit originalen Intervallen).")
    parser.add_argument("--in-file", default="ps4_packets.jsonl", help="Eingabedatei mit aufgezeichneten Paketen (JSONL)")
    parser.add_argument("--dest-ip", default="127.0.0.1", help="Ziel-IP zum Senden der Pakete")
    parser.add_argument("--dest-port", type=int, default=20777, help="Ziel-Port")
    parser.add_argument("--speed", type=float, default=1.0, help="Geschwindigkeitsfaktor: 1.0 = originale Intervalle, 2.0 = doppelte Geschwindigkeit (Intervalle halbiert)")
    args = parser.parse_args()

    records = []
    with open(args.in_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception as e:
                print(f"Fehler beim Parsen einer Zeile: {e}", flush=True)
                continue
            records.append(rec)

    if not records:
        print("Keine Pakete in der Datei gefunden.", flush=True)
        return

    # Sortieren nach Timestamp, falls nötig
    records.sort(key=lambda r: r.get("timestamp", 0))

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print(f"Starte Wiedergabe von {len(records)} Paketen an {args.dest_ip}:{args.dest_port} (speed={args.speed})", flush=True)

    # Sende erstes Paket sofort
    prev_ts = records[0].get("timestamp", 0)

    try:
        for i, rec in enumerate(records):
            # Erster Datensatz: keine Wartezeit
            if i == 0:
                interval = 0.0
            else:
                # Bevorzuge gespeichertes 'interval' wenn vorhanden (abwärtskompatibel)
                if rec.get("interval") is not None:
                    try:
                        interval = float(rec.get("interval", 0.0)) / args.speed
                    except Exception:
                        interval = 0.0
                else:
                    # Fallback: berechne aus timestamps
                    ts = rec.get("timestamp", prev_ts)
                    interval = (ts - prev_ts) / args.speed
                    if interval < 0:
                        interval = 0.0

            if interval > 0:
                try:
                    time.sleep(interval)
                except KeyboardInterrupt:
                    raise

            b64 = rec.get("payload_b64")
            if not b64:
                print(f"[{i+1}/{len(records)}] Kein payload_b64 gefunden, übersprungen.", flush=True)
                prev_ts = rec.get("timestamp", prev_ts)
                continue

            try:
                payload = base64.b64decode(b64)
            except Exception as e:
                print(f"[{i+1}/{len(records)}] Fehler beim Decodieren von Base64: {e}", flush=True)
                prev_ts = rec.get("timestamp", prev_ts)
                continue

            try:
                sock.sendto(payload, (args.dest_ip, args.dest_port))
            except Exception as e:
                print(f"[{i+1}/{len(records)}] Fehler beim Senden: {e}", flush=True)
                prev_ts = rec.get("timestamp", prev_ts)
                continue

            prev_ts = rec.get("timestamp", prev_ts)
            print(f"[{i+1}/{len(records)}] Gesendet {len(payload)} Bytes (sleep={interval:.3f}s)", flush=True)

    except KeyboardInterrupt:
        print("\nWiedergabe beendet durch Benutzer.", flush=True)
    finally:
        sock.close()


if __name__ == '__main__':
    main()
