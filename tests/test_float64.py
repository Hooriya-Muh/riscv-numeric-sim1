# tests/test_float64.py
from adapters.floatpack import pack_f64_from_python, bits_to_hex64
from src.numeric_core.fpu import fadd_f64, fmul_f64

def test_f64_add_basic():
    a = pack_f64_from_python(1.5)
    b = pack_f64_from_python(2.25)
    r, flg = fadd_f64(a,b)
    assert bits_to_hex64(r).endswith('400E000000000000')

def test_f64_mul_basic():
    a = pack_f64_from_python(3.0)
    b = pack_f64_from_python(1.25)
    r, flg = fmul_f64(a,b)
    assert bits_to_hex64(r).endswith('400E000000000000')
