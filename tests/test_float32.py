# tests/test_float32.py
from adapters.floatpack import pack_f32_from_python, bits_to_hex32
from src.numeric_core.fpu import fadd_f32, fsub_f32, fmul_f32

def test_f32_add_simple():
    a = pack_f32_from_python(1.5)
    b = pack_f32_from_python(2.25)
    r, flg = fadd_f32(a,b)
    assert bits_to_hex32(r).endswith('40700000')

def test_f32_add_decimal_rounding():
    a = pack_f32_from_python(0.1)
    b = pack_f32_from_python(0.2)
    r, flg = fadd_f32(a,b)
    assert bits_to_hex32(r).endswith('3E99999A')

def test_f32_mul_simple():
    a = pack_f32_from_python(3.0)
    b = pack_f32_from_python(1.25)
    r, flg = fmul_f32(a,b)
    assert bits_to_hex32(r).endswith('40700000')
