import socket
import struct

# UDP-Empfänger konfigurieren
UDP_IP = "0.0.0.0"
UDP_PORT = 20777

# Byte-Längen (bits: multiply by 8)
BYTES_U8 = 1
BYTES_U16 = 2
BYTES_U32 = 4
BYTES_U64 = 8
BYTES_FLOAT = 4

# Offsets (in Bytes) für PacketHeader (little-endian)
OFF_PACKET_FORMAT = 0               # uint16 (2 Bytes)
OFF_GAME_MAJOR = OFF_PACKET_FORMAT + BYTES_U16  # uint8 (1 Byte)
OFF_GAME_MINOR = OFF_GAME_MAJOR + BYTES_U8      # uint8 (1 Byte)
OFF_PACKET_VERSION = OFF_GAME_MINOR + BYTES_U8  # uint8 (1 Byte)
OFF_PACKET_ID = OFF_PACKET_VERSION + BYTES_U8   # uint8 (1 Byte)
OFF_SESSION_UID = OFF_PACKET_ID + BYTES_U8      # uint64 (8 Bytes)
OFF_SESSION_TIME = OFF_SESSION_UID + BYTES_U64  # float (4 Bytes)
OFF_FRAME_IDENTIFIER = OFF_SESSION_TIME + BYTES_FLOAT  # uint32 (4 Bytes)
OFF_PLAYER_CAR_INDEX = OFF_FRAME_IDENTIFIER + BYTES_U32  # uint8 (1 Byte)
OFF_SECOND_PLAYER_CAR_INDEX = OFF_PLAYER_CAR_INDEX + BYTES_U8  # uint8 (1 Byte)

HEADER_LEN = OFF_SECOND_PLAYER_CAR_INDEX + BYTES_U8  # = 24 Bytes


def u16_le(data: bytes, off: int) -> int:
    """Liest 16 Bit (2 Bytes) little-endian und gibt uint16 zurück."""
    return int.from_bytes(data[off:off+BYTES_U16], 'little')


def u8_le(data: bytes, off: int) -> int:
    """Liest 8 Bit (1 Byte) little-endian und gibt uint8 zurück."""
    return data[off]


# Kürzere Hilfsfunktionen für andere Typen
u32_le = lambda data, off: int.from_bytes(data[off:off+BYTES_U32], 'little')
u64_le = lambda data, off: int.from_bytes(data[off:off+BYTES_U64], 'little')
f32_le = lambda data, off: struct.unpack_from('<f', data, off)[0]


def parse_packet_header(data: bytes) -> dict:
    """Parst die ersten 24 Bytes laut PacketHeader-Struktur und gibt ein Dict zurück.

    Erwartete Felder (mit Offsets, little-endian):
      0:  uint16  m_packetFormat             (2 Bytes)  # 2022
      2:  uint8   m_gameMajorVersion         (1 Byte)   # Game major version - "X.00"
      3:  uint8   m_gameMinorVersion         (1 Byte)   # Game minor version - "1.XX"
      4:  uint8   m_packetVersion            (1 Byte)   # Version of this packet type, all start from 1
      5:  uint8   m_packetId                 (1 Byte)   # Identifier for the packet type
      6:  uint64  m_sessionUID               (8 Bytes)  # Unique identifier for the session
      14: float   m_sessionTime              (4 Bytes)  # Session timestamp
      18: uint32  m_frameIdentifier          (4 Bytes)  # Identifier for the frame the data was retrieved on
      22: uint8   m_playerCarIndex           (1 Byte)   # Index of player's car in the array
      23: uint8   m_secondaryPlayerCarIndex  (1 Byte)   # Index of secondary player's car (255 if none)

    Raises ValueError wenn data zu kurz ist.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("data must be bytes or bytearray")
    if len(data) < HEADER_LEN:
        raise ValueError(f"packet too short for PacketHeader: need {HEADER_LEN} bytes, got {len(data)}")

    # kompakte, klare Struct-Interpretation (little-endian):
    # Format: H (uint16)  B B B B (4 uint8)  Q (uint64)  f (float32)  I (uint32)  B B (2 uint8)
    vals = struct.unpack_from('<HBBBBQfIBB', data, 0)
    (m_packetFormat, m_gameMajorVersion, m_gameMinorVersion,
     m_packetVersion, m_packetId, m_sessionUID,
     m_sessionTime, m_frameIdentifier,
     m_playerCarIndex, m_secondaryPlayerCarIndex) = vals

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


def log_header(h: dict):
    print('--- PacketHeader ---')
    rows = [
        ('m_packetFormat', h['m_packetFormat']),
        ('m_gameMajorVersion', h['m_gameMajorVersion']),
        ('m_gameMinorVersion', h['m_gameMinorVersion']),
        ('m_packetVersion', h['m_packetVersion']),
        ('m_packetId', h['m_packetId']),
        ('m_sessionUID', f"{h['m_sessionUID']} (0x{h['m_sessionUID']:016X})"),
        ('m_sessionTime', h['m_sessionTime']),
        ('m_frameIdentifier', f"{h['m_frameIdentifier']} (0x{h['m_frameIdentifier']:08X})"),
        ('m_playerCarIndex', h['m_playerCarIndex']),
        ('m_secondaryPlayerCarIndex', h['m_secondaryPlayerCarIndex']),
    ]
    for name, val in rows:
        print(f"{name}: {val}")
    print('--- end PacketHeader ---')


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    print(f"🎧 Lausche auf UDP-Port {UDP_PORT}... (interpretiere alles als little-endian)")

    try:
        while True:
            data, addr = sock.recvfrom(4096)
            print(f"📦 Paket von {addr}: {len(data)} Bytes")
            try:
                header = parse_packet_header(data)
            except (ValueError, TypeError) as e:
                print(f"⚠️ Kann PacketHeader nicht parsen: {e}")
                print(data)
                continue
            log_header(header)
            if len(data) > HEADER_LEN:
                print(f"Rest ({len(data)-HEADER_LEN} Bytes): {data[HEADER_LEN:]}")
    except KeyboardInterrupt:
        print("\nBeendet durch Benutzer.")
    finally:
        sock.close()


if __name__ == '__main__':
    main()
