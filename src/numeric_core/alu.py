# AI-BEGIN
# src/numeric_core/alu.py
# RV32 ADD/SUB with flags N,Z,C,V using ripple-carry adder only.

from .adder import ripple_add, sub

def msb(bits):
    return bits[0] if bits else 0

def is_zero(bits):
    for b in bits:
        if b == 1:
            return 0
    return 1

def alu_add(bitsA, bitsB):
    n = len(bitsA)
    s, c = ripple_add(bitsA, bitsB, 0)
    a_s = msb(bitsA)
    b_s = msb(bitsB)
    r_s = msb(s)
    # Signed overflow for ADD: sign(a)==sign(b) and sign(result)!=sign(a)
    v = 1 if (a_s == b_s and r_s != a_s) else 0
    nflag = r_s
    zflag = is_zero(s)
    cflag = c  # carry out of MSB
    return s, {'N':nflag,'Z':zflag,'C':cflag,'V':v}

def alu_sub(bitsA, bitsB):
    s, c = sub(bitsA, bitsB)
    a_s = bitsA[0]
    b_s = bitsB[0]
    r_s = s[0]
    # Signed overflow for SUB: sign(a)!=sign(b) and sign(result)!=sign(a)
    v = 1 if (a_s != b_s and r_s != a_s) else 0
    nflag = r_s
    zflag = is_zero(s)
    cflag = c  # in two's complement, C=1 => no borrow
    return s, {'N':nflag,'Z':zflag,'C':cflag,'V':v}
# AI-END
