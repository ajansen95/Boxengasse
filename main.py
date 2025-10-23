import socket

# UDP-Empfänger konfigurieren
UDP_IP = "0.0.0.0"   # Lauscht auf allen Netzwerkinterfaces
UDP_PORT = 20777     # Der gewünschte Port

# Socket erstellen
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print(f"🎧 Lausche auf UDP-Port {UDP_PORT}...")

try:
    while True:
        data, addr = sock.recvfrom(4096)  # max. 4096 Bytes pro Paket
        print(f"📦 Paket von {addr}: {len(data)} Bytes")
        print(data)
except KeyboardInterrupt:
    print("\nBeendet durch Benutzer.")
finally:
    sock.close()
