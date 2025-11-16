# tests/test_m_extension_more.py
from src.numeric_core.bits import from_hex_string, to_hex_string
from src.numeric_core.mdu import divu_unsigned, rem_signed, remu_unsigned

def hx(b): return to_hex_string(b, width_multiple=8)

def test_divu_basic():
    a = from_hex_string('0x80000000', width=32)
    b = from_hex_string('0x00000003', width=32)
    q, r, flg, _ = divu_unsigned(a,b, trace=True)
    assert hx(q).endswith('2AAAAAAA') and hx(r).endswith('00000002')

def test_divu_by_zero():
    a = from_hex_string('0x12345678', width=32)
    b = from_hex_string('0x00000000', width=32)
    q, r, flg, _ = divu_unsigned(a,b)
    assert hx(q).endswith('FFFFFFFF') and r==a

def test_rem_signed_same_as_spec():
    a = from_hex_string('0xFFFFFFF9', width=32) # -7
    b = from_hex_string('0x00000003', width=32) # +3
    r, flg, _ = rem_signed(a,b, trace=True)
    assert hx(r).endswith('FFFFFFFF')

def test_remu_basic():
    a = from_hex_string('0x80000007', width=32)
    b = from_hex_string('0x00000003', width=32)
    r, flg, _ = remu_unsigned(a,b)
    assert hx(r).endswith('00000000')  # remainder must be 0

