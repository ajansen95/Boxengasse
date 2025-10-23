import socket
from typing import Literal

# UDP-Empfänger konfigurieren
UDP_IP = "0.0.0.0"   # Lauscht auf allen Netzwerkinterfaces
UDP_PORT = 20777     # Der gewünschte Port

# Wir interpretieren immer little-endian
BYTE_ORDER: Literal['little'] = 'little'


def main():
    # Socket erstellen
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    print(f"🎧 Lausche auf UDP-Port {UDP_PORT}... (interpretiere erstes uint16 immer als {BYTE_ORDER}-endian)")

    try:
        while True:
            data, addr = sock.recvfrom(4096)  # max. 4096 Bytes pro Paket
            print(f"📦 Paket von {addr}: {len(data)} Bytes")

            if len(data) < 2:
                print("⚠️ Paket enthält weniger als 2 Bytes — kein uint16 auslesbar.")
                print(data)
                continue

            # Erste 2 Bytes als uint16 interpretieren (immer little-endian)
            first_two = data[:2]
            uint16 = int.from_bytes(first_two, byteorder=BYTE_ORDER, signed=False)

            # Ausgabe ähnlich zu C uint16 (0..65535)
            print(f"Erste 2 Bytes (hex): {first_two.hex()} -> uint16 ({BYTE_ORDER}-endian): {uint16} (0x{uint16:04X})")

            # Optional: zeige Rest der Daten (ab Byte 2)
            if len(data) > 2:
                print(f"Rest ({len(data)-2} Bytes): {data[2:]}")
    except KeyboardInterrupt:
        print("\nBeendet durch Benutzer.")
    finally:
        sock.close()


if __name__ == '__main__':
    main()
