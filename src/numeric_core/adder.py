# AI-BEGIN
# src/numeric_core/adder.py
# Full-adder based ripple-carry add/sub without using + - * / << >> on numeric values.

def full_adder(a,b,cin):
    # sum = a XOR b XOR cin; cout = majority(a,b,cin)
    axb = (a ^ b) & 1
    s = (axb ^ cin) & 1
    cout = ((a & b) | (a & cin) | (b & cin)) & 1
    return s, cout

def ripple_add(bitsA, bitsB, cin=0):
    """Add two same-length bit-vectors (MSB at index 0).
    Returns (sum_bits, carry_out)."""
    assert len(bitsA) == len(bitsB)
    n = len(bitsA)
    out = [0]*n
    c = cin & 1
    # process from LSB to MSB (right to left)
    for i in range(n-1, -1, -1):
        s, c = full_adder(bitsA[i], bitsB[i], c)
        out[i] = s
    return out, c

def invert(bits):
    return [1-b for b in bits]

def twos_negate(bits):
    inv = invert(bits)
    # add one
    one = [0]*(len(bits)-1) + [1]
    s, c = ripple_add(inv, one, 0)
    return s

def sub(bitsA, bitsB):
    # A - B = A + (~B + 1)
    invB = invert(bitsB)
    one = [0]*(len(bitsB)-1) + [1]
    tmp, _ = ripple_add(invB, one, 0)
    s, c = ripple_add(bitsA, tmp, 0)
    # For subtraction, carry-out==1 implies no borrow in two's complement convention
    return s, c
# AI-END
