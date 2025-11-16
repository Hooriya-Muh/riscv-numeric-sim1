# adapters/floatpack.py
import struct
from src.numeric_core.bits import to_hex_string

def pack_f32_from_python(x: float):
    b = struct.pack('>f', float(x))
    bits = []
    for byte in b:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits

def pack_f64_from_python(x: float):
    b = struct.pack('>d', float(x))
    bits = []
    for byte in b:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits

def bits_to_hex32(bits):
    return to_hex_string(bits, width_multiple=8)

def bits_to_hex64(bits):
    return to_hex_string(bits, width_multiple=16)