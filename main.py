import socket
import struct

# UDP-Empfänger konfigurieren
UDP_IP = "0.0.0.0"   # Lauscht auf allen Netzwerkinterfaces
UDP_PORT = 20777     # Der gewünschte Port

HEADER_FMT = '<HBBBBQfIBB'  # little-endian: uint16, 4*uint8, uint64, float, uint32, 2*uint8
HEADER_LEN = struct.calcsize(HEADER_FMT)


def parse_packet_header(data: bytes):
    """Parst die ersten 24 Bytes laut PacketHeader-Struktur und gibt ein Dict mit benannten Feldern zurück.

    Erwartete Felder (mit Offsets, little-endian):
      0: uint16    m_packetFormat            # 2022
      2: uint8     m_gameMajorVersion        # Game major version - "X.00"
      3: uint8     m_gameMinorVersion        # Game minor version - "1.XX"
      4: uint8     m_packetVersion           # Version of this packet type, all start from 1
      5: uint8     m_packetId                # Identifier for the packet type
      6: uint64    m_sessionUID              # Unique identifier for the session
      14: float    m_sessionTime             # Session timestamp
      18: uint32   m_frameIdentifier         # Identifier for the frame the data was retrieved on
      22: uint8    m_playerCarIndex          # Index of player's car in the array
      23: uint8    m_secondaryPlayerCarIndex # Index of secondary player's car in the array (splitscreen)
                                             # 255 if no second player

    Raises ValueError wenn data zu kurz ist.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("data must be bytes or bytearray")
    if len(data) < HEADER_LEN:
        raise ValueError(f"packet too short for PacketHeader: need {HEADER_LEN} bytes, got {len(data)}")
    (m_packetFormat, m_gameMajorVersion, m_gameMinorVersion, m_packetVersion,
     m_packetId, m_sessionUID, m_sessionTime, m_frameIdentifier,
     m_playerCarIndex, m_secondaryPlayerCarIndex) = struct.unpack_from(HEADER_FMT, data, 0)
    return {
        'm_packetFormat': m_packetFormat,
        'm_gameMajorVersion': m_gameMajorVersion,
        'm_gameMinorVersion': m_gameMinorVersion,
        'm_packetVersion': m_packetVersion,
        'm_packetId': m_packetId,
        'm_sessionUID': m_sessionUID,
        'm_sessionTime': m_sessionTime,
        'm_frameIdentifier': m_frameIdentifier,
        'm_playerCarIndex': m_playerCarIndex,
        'm_secondaryPlayerCarIndex': m_secondaryPlayerCarIndex,
    }


def main():
    # Socket erstellen
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    print(f"🎧 Lausche auf UDP-Port {UDP_PORT}... (interpretiere erstes uint16 immer als little-endian)")

    try:
        while True:
            data, addr = sock.recvfrom(4096)  # max. 4096 Bytes pro Paket
            print(f"📦 Paket von {addr}: {len(data)} Bytes")

            try:
                header = parse_packet_header(data)
            except (ValueError, TypeError) as e:
                print(f"⚠️ Kann PacketHeader nicht parsen: {e}")
                print(data)
                continue

            # Logge alle Felder mit Namen
            print("--- PacketHeader ---")
            print(f"m_packetFormat: {header['m_packetFormat']}")
            print(f"m_gameMajorVersion: {header['m_gameMajorVersion']}")
            print(f"m_gameMinorVersion: {header['m_gameMinorVersion']}")
            print(f"m_packetVersion: {header['m_packetVersion']}")
            print(f"m_packetId: {header['m_packetId']}")
            print(f"m_sessionUID: {header['m_sessionUID']} (0x{header['m_sessionUID']:016X})")
            print(f"m_sessionTime: {header['m_sessionTime']}")
            print(f"m_frameIdentifier: {header['m_frameIdentifier']} (0x{header['m_frameIdentifier']:08X})")
            print(f"m_playerCarIndex: {header['m_playerCarIndex']}")
            print(f"m_secondaryPlayerCarIndex: {header['m_secondaryPlayerCarIndex']}")
            print("--- end PacketHeader ---")

            # Optional: zeige Rest der Daten (ab Byte 24)
            if len(data) > HEADER_LEN:
                print(f"Rest ({len(data)-HEADER_LEN} Bytes): {data[HEADER_LEN:]}")
    except KeyboardInterrupt:
        print("\nBeendet durch Benutzer.")
    finally:
        sock.close()


if __name__ == '__main__':
    main()
