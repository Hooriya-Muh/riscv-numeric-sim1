# adapters/twos.py
from src.numeric_core.bits import from_hex_string, to_hex_string, pretty_bin
from src.numeric_core.shifter import sll
from src.numeric_core.adder import ripple_add, twos_negate

XLEN = 32

def _const_u32(hx): return from_hex_string(hx, width=XLEN)
_DIGITS = { d:_const_u32(f"0x0000000{d}") for d in "0123456789" }

def _add_u32(a,b): s,_ = ripple_add(a,b,0); return s

def _mul10_u32(a):
    x8 = sll(a, 3)
    x2 = sll(a, 1)
    s,_ = ripple_add(x8, x2, 0)
    return s

def _decstr_to_u32_bits(s):
    neg = False
    s = s.strip()
    if s.startswith('+'): s = s[1:]
    elif s.startswith('-'): s = s[1:]; neg = True
    acc = _const_u32('0x00000000')
    for ch in s:
        if ch not in _DIGITS: raise ValueError('bad decimal digit')
        acc = _mul10_u32(acc)
        acc = _add_u32(acc, _DIGITS[ch])
    if neg:
        acc = twos_negate(acc)
    return acc

def encode_twos_complement(value):
    s = str(value)
    bits = _decstr_to_u32_bits(s)
    return {'bin': pretty_bin(bits), 'hex': to_hex_string(bits, width_multiple=8), 'overflow_flag': 0}

def decode_twos_complement(bits_hex):
    bits = from_hex_string(bits_hex, width=XLEN)
    sign = bits[0]
    mag = bits[:] if sign==0 else twos_negate(bits[:])
    val = 0
    for b in mag:
        val = (val << 1) | (1 if b else 0)
    if sign==1:
        val = -val
    return {'value': val}
