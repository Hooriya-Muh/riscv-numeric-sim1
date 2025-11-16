# AI-BEGIN
# tests/test_hex_helpers.py
from src.numeric_core.bits import from_hex_string, to_hex_string, pretty_bin

def test_hex_roundtrip_32():
    b = from_hex_string('0x7FFFFFFF', width=32)
    assert len(b) == 32
    h = to_hex_string(b, width_multiple=8)
    assert h.endswith('7FFFFFFF')

def test_pretty_bin_groups():
    b = from_hex_string('0x0000000D', width=32)
    s = pretty_bin(b)
    assert '_' in s
# AI-END
