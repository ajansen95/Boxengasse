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
    parser.add_argument("--out-file", default="ps4_packets.jsonl", help="Datei zum Anhängen der empfangenen Pakete (default: ps4_packets.jsonl)")
    args = parser.parse_args()

    UDP_IP = args.bind_ip
    UDP_PORT = args.port
    out_file = args.out_file

    os.makedirs(os.path.dirname(out_file) or '.', exist_ok=True)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    print(f"🎧 Lausche auf UDP {UDP_IP}:{UDP_PORT}... (Pakete werden in '{out_file}' gespeichert, little-endian Annahme irrelevant für Raw-Pakete)")

    # Datei im Anhängemodus öffnen
    f = open(out_file, "a", encoding="utf-8")

    last_ts = None
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
            f.write(json.dumps(record, separators=(",", ":")) + "\n")
            f.flush()
            last_ts = ts

            print(f"📦 {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))} - Paket von {addr}: {len(data)} Bytes (intervall={interval:.3f}s) -> gespeichert")
    except KeyboardInterrupt:
        print("\nBeendet durch Benutzer.")
    finally:
        f.close()
        sock.close()


if __name__ == '__main__':
    main()
