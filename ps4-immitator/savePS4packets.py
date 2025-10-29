import argparse
import socket
import time
import json
import base64
import os

def main():
    parser = argparse.ArgumentParser(description="UDP-Paket-Empfänger, der Pakete persistent in einer JSONL-Datei speichert.")
    parser.add_argument("--bind-ip", default="0.0.0.0", help="IP zum Binden (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=20777, help="UDP-Port zum Lauschen (default: 20777)")
    parser.add_argument("--out-file", default="recordings/ps4_packets.jsonl", help="Datei zum Anhängen der empfangenen Pakete (default: recordings/ps4_packets.jsonl)")
    parser.add_argument("--flush-every", type=int, default=100, help="Flush nach N Paketen (default: 100)")
    parser.add_argument("--flush-interval", type=float, default=1.0, help="Flush mindestens alle T Sekunden (default: 1.0)")
    parser.add_argument("--fsync-every-seconds", type=float, default=10.0, help="Führe os.fsync() alle S Sekunden aus (0 = deaktiviert, default: 10.0)")
    parser.add_argument("--fsync-every-packets", type=int, default=0, help="Führe os.fsync() nach N Paketen aus (0 = deaktiviert, default: 0)")
    args = parser.parse_args()

    # lowercase variable names to follow PEP8 / function-local naming conventions
    udp_ip = args.bind_ip
    udp_port = args.port
    out_file = args.out_file

    os.makedirs(os.path.dirname(out_file) or '.', exist_ok=True)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((udp_ip, udp_port))

    print(f"🎧 Lausche auf UDP {udp_ip}:{udp_port}... (Pakete werden in '{out_file}' gespeichert)")

    # Datei im Anhängemodus öffnen (Text-Modus ist in Ordnung, wir schreiben JSON-Text)
    f = open(out_file, "a", encoding="utf-8")

    last_ts = None
    last_flush_time = time.time()
    last_fsync_time = time.time()
    count_since_flush = 0
    count_since_fsync = 0
    total_packets = 0

    flush_every = max(1, args.flush_every)
    flush_interval = max(0.0, args.flush_interval)
    fsync_every_seconds = max(0.0, args.fsync_every_seconds)
    fsync_every_packets = max(0, args.fsync_every_packets)

    try:
        while True:
            data, addr = sock.recvfrom(65535)
            ts = time.time()
            interval = ts - last_ts if last_ts is not None else 0.0
            record = {
                "timestamp": ts,
                "interval": interval,
                "from": f"{addr[0]}:{addr[1]}",
                "length": len(data),
                "payload_b64": base64.b64encode(data).decode("ascii")
            }

            # Schreibe in Datei (gepuffert)
            f.write(json.dumps(record, separators=(",", ":")) + "\n")
            total_packets += 1
            count_since_flush += 1
            count_since_fsync += 1
            last_ts = ts

            now = time.time()
            # Entscheide, ob wir flushen sollten
            if (flush_every and count_since_flush >= flush_every) or (flush_interval and (now - last_flush_time) >= flush_interval):
                try:
                    f.flush()
                except (OSError, ValueError) as e:
                    print(f"Warnung: flush fehlgeschlagen: {e}")
                last_flush_time = now
                count_since_flush = 0

            # Entscheide, ob wir fsync sollten
            do_fsync = False
            if 0.0 < fsync_every_seconds <= (now - last_fsync_time):
                do_fsync = True
            if fsync_every_packets and 0 < fsync_every_packets <= count_since_fsync:
                do_fsync = True

            if do_fsync:
                try:
                    f.flush()
                    os.fsync(f.fileno())
                except (OSError, ValueError) as e:
                    print(f"Warnung: fsync fehlgeschlagen: {e}")
                last_fsync_time = now
                count_since_fsync = 0

            print(f"📦 {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))} - Paket von {addr}: {len(data)} Bytes (intervall={interval:.3f}s) -> gespeichert (total={total_packets})")

    except KeyboardInterrupt:
        print("\nBeendet durch Benutzer. Flushing verbleibender Daten...")
        # am Ende noch einmal flush + fsync falls gewünscht
        try:
            f.flush()
            if fsync_every_seconds > 0.0 or fsync_every_packets > 0:
                try:
                    os.fsync(f.fileno())
                except (OSError, ValueError) as e:
                    print(f"Warnung: fsync beim Beenden fehlgeschlagen: {e}")
        except (OSError, ValueError) as e:
            print(f"Warnung: finaler flush fehlgeschlagen: {e}")
    finally:
        try:
            f.close()
        except OSError:
            pass
        try:
            sock.close()
        except OSError:
            pass


if __name__ == '__main__':
    main()
