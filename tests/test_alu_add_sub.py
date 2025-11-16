# AI-BEGIN
# tests/test_alu_add_sub.py
from src.numeric_core.bits import from_hex_string, to_hex_string
from src.numeric_core.alu import alu_add, alu_sub

def bits_to_hex32(b): return to_hex_string(b, width_multiple=8)

def test_add_overflow_case():
    a = from_hex_string('0x7FFFFFFF', width=32)
    b = from_hex_string('0x00000001', width=32)
    r, f = alu_add(a,b)
    assert bits_to_hex32(r).endswith('80000000')
    assert f['V']==1 and f['C']==0 and f['N']==1 and f['Z']==0

def test_sub_overflow_case():
    a = from_hex_string('0x80000000', width=32)
    b = from_hex_string('0x00000001', width=32)
    r, f = alu_sub(a,b)
    assert bits_to_hex32(r).endswith('7FFFFFFF')
    assert f['V']==1 and f['C']==1 and f['N']==0 and f['Z']==0

def test_add_negative_numbers():
    a = from_hex_string('0xFFFFFFFF', width=32)  # -1
    b = from_hex_string('0xFFFFFFFF', width=32)  # -1
    r, f = alu_add(a,b)
    assert bits_to_hex32(r).endswith('FFFFFFFE')  # -2
    assert f['V']==0 and f['C']==1 and f['N']==1 and f['Z']==0

def test_add_cancel_to_zero():
    a = from_hex_string('0x0000000D', width=32)  # +13
    b = from_hex_string('0xFFFFFFF3', width=32)  # -13
    r, f = alu_add(a,b)
    assert bits_to_hex32(r).endswith('00000000')
    assert f['Z']==1
# AI-END
