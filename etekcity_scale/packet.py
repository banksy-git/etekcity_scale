from collections import namedtuple
import struct
import binascii
import time
import logging

log = logging.getLogger(__name__)

MAGIC_BYTE = 0x15

HelloPacket = namedtuple("HelloPacket", "mac unknown")
WeightMeasurement = namedtuple("WeightMeasurement", "weight_kg final r1 r2")
UnknownPacket = namedtuple("UnknownPacket", "type raw_value")

def encode_raw_packet(type: int, value: bytes) -> bytes:
    packet = bytes([type, len(value) + 4, MAGIC_BYTE]) + value
    packet += bytes([(sum(packet) & 0xFF)])
    log.debug("SEND %s", binascii.hexlify(packet))
    return packet


def decode_raw_packet(packet: bytes) -> tuple[int, bytes]:
    log.debug("RECV %s", binascii.hexlify(packet))
    if len(packet) != packet[1]:
        raise ValueError("Packet length is incorrect. Expected %d bytes got %d bytes" % (
            packet[1], len(packet)))
    if (sum(packet[0:-1]) & 0xFF) != packet[-1]:
        raise ValueError("Packet checksum is incorrect")
    if packet[2] != MAGIC_BYTE:
        raise ValueError("MAGIC_BYTE not as expected! Assumption incorrect!")
    return int(packet[0]), packet[3:-1]


def init_packet(display_units="KG"):
    unit_decode = {
        "KG": 1,
        "LB": 2,
        "WE": 4,
        "STONE": 8,
    }
    return encode_raw_packet(0x13, bytes([
        unit_decode[display_units],
        0x10, 0xbe, 0x34, 0x00]))


def set_time_packet(timestamp=None):
    Y2K_START = 946684800  # in seconds
    if timestamp is None:
        timestamp = time.time() - Y2K_START
    return encode_raw_packet(0x20, struct.pack("<I", int(timestamp)))


def init2_packet():
    return encode_raw_packet(0x22, b"")


def finish_measurement():
    return encode_raw_packet(0x1f, b"\x10")


def decode_packet(packet: bytes):

    packet_type, raw_value = decode_raw_packet(packet)

    if packet_type == 0x10:  # Weight data packet
        weight_10g, final, r1, r2 = struct.unpack(">HBHH", raw_value)
        return WeightMeasurement(weight_10g / 100.0, final, r1, r2)
    if packet_type == 0x12:  # Hello from device packet
        return HelloPacket(
            binascii.hexlify(raw_value[5::-1]),
            raw_value[6:]
        )
    else:
        return UnknownPacket(packet_type, raw_value)


if __name__ == "__main__":
    decode_raw_packet(encode_raw_packet(88, b"testpacket"))
    print(decode_packet(binascii.unhexlify("100b150000000000000030")))
    print(decode_packet(binascii.unhexlify("100b1528e60101f801afe8")))
