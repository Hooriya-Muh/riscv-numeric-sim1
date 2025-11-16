# src/numeric_core/mdu.py
from .adder import ripple_add, twos_negate
from .alu import msb
from .bits import from_hex_string

def _is_zero(bits):
    for b in bits:
        if b == 1:
            return False
    return True

def _invert(bits):
    return [1 - x for x in bits]

def _sub_bits(a, b):
    inv = _invert(b)
    one = [0] * (len(b) - 1) + [1]
    t, _ = ripple_add(inv, one, 0)
    s, c = ripple_add(a, t, 0)  # c==1 => no borrow
    return s, c

def _addu(a, b):
    s, _ = ripple_add(a, b, 0)
    return s

def mul_shift_add_64(a, b, trace=False):
    n = len(a)
    acc = [0] * (2 * n)
    mulcand = [0] * n + a[:]
    mult = b[:]
    steps = []
    for i in range(n):
        if mult[-1] == 1:
            acc, _ = ripple_add(acc, mulcand, 0)
        if trace:
            steps.append({
                'i': i,
                'acc': ''.join(map(str, acc)),
                'mulcand': ''.join(map(str, mulcand)),
                'mult': ''.join(map(str, mult)),
            })
        mulcand = mulcand[1:] + [0]
        mult = [0] + mult[:-1]
    return acc, (steps if trace else None)

def mul_low32(rs1, rs2, trace=False):
    n = len(rs1)
    s1 = msb(rs1); s2 = msb(rs2)
    neg = 1 if (s1 ^ s2) else 0
    a = rs1 if s1 == 0 else twos_negate(rs1)
    b = rs2 if s2 == 0 else twos_negate(rs2)
    acc, steps = mul_shift_add_64(a, b, trace=trace)
    if neg:
        acc = twos_negate(acc)
    low32 = acc[-n:]
    sign = low32[0]
    hi = acc[:-n]
    overflow = 0
    for bit in hi:
        if bit != sign:
            overflow = 1
            break
    return low32, {'overflow': overflow}, steps if trace else None

def mulh_signed(rs1, rs2):
    n = len(rs1)
    s1 = msb(rs1); s2 = msb(rs2)
    neg = 1 if (s1 ^ s2) else 0
    a = rs1 if s1 == 0 else twos_negate(rs1)
    b = rs2 if s2 == 0 else twos_negate(rs2)
    acc, _ = mul_shift_add_64(a, b, trace=False)
    if neg:
        acc = twos_negate(acc)
    return acc[:-n]

def mulhu_unsigned(rs1, rs2):
    n = len(rs1)
    acc, _ = mul_shift_add_64(rs1, rs2, trace=False)
    return acc[:-n]

def mulhsu(rs1, rs2):
    n = len(rs1)
    s1 = msb(rs1)
    a = rs1 if s1 == 0 else twos_negate(rs1)  # signed abs
    b = rs2[:]                                 # unsigned
    acc, _ = mul_shift_add_64(a, b, trace=False)
    if s1 == 1:
        acc = twos_negate(acc)
    return acc[:-n]

def div_signed(rs1, rs2, trace=False):
    n = len(rs1)
    s1 = msb(rs1); s2 = msb(rs2)

    if _is_zero(rs2):
        q = [1] * n
        r = rs1[:]
        return q, r, {'div_by_zero': 1, 'overflow': 0}, [{'event': 'div_by_zero'}] if trace else None

    # INT_MIN/-1 special
    is_int_min = (rs1[0] == 1 and all(x == 0 for x in rs1[1:]))
    is_neg_one = (rs2 == [1] * n)
    if is_int_min and is_neg_one:
        q = rs1[:]
        r = [0] * n
        return q, r, {'div_by_zero': 0, 'overflow': 1}, [] if trace else None

    # magnitudes
    a = rs1 if s1 == 0 else twos_negate(rs1)
    b = rs2 if s2 == 0 else twos_negate(rs2)

    rem = [0] * n
    quo = [0] * n
    steps = []
    for i in range(n):
        rem = rem[1:] + [a[i]]
        rem_t, carry = _sub_bits(rem, b)
        if carry == 1:  # no borrow => rem >= b
            rem = rem_t
            quo = quo[1:] + [1]
            act = 'sub'
        else:
            quo = quo[1:] + [0]
            act = 'restore'
        if trace:
            steps.append({'i': i, 'rem': ''.join(map(str, rem)), 'quo': ''.join(map(str, quo)), 'action': act})

    q_neg = 1 if (s1 ^ s2) else 0
    r_neg = s1
    if q_neg:
        quo = twos_negate(quo)
    if r_neg and not _is_zero(rem):
        rem = twos_negate(rem)

    return quo, rem, {'div_by_zero': 0, 'overflow': 0}, steps if trace else None

# unsigned DIV/REM (RV32M)
def divu_unsigned(rs1, rs2, trace=False):
    """Unsigned restoring division. rs1, rs2 are bit arrays (MSB at index 0)."""
    n = len(rs1)
    # If divisor is zero: q=all1, r=dividend (RISC-V semantics)
    if _is_zero(rs2):
        return [1]*n, rs1[:], {'div_by_zero':1}, ([] if not trace else [{'step':0,'rem':rs1[:],'q':([1]*n),'op':'/0'}])

    rem = [0]*n
    q = [0]*n
    tr = []

    for i in range(n):
        # Bring down next dividend bit
        next_bit = rs1[i]
        rem = rem[1:] + [next_bit]    # left shift rem by 1 and OR in bit
        # Try subtracting divisor
        diff, c = _sub_bits(rem, rs2) # c==1 => no borrow => rem >= rs2
        if c == 1:
            rem = diff
            q[i] = 1
            op = 'sub'
        else:
            # restore
            op = 'restore'
        if trace:
            tr.append({'step': i, 'rem': rem[:], 'q': q[:], 'op': op})

    flags = {'overflow':0}
    return q, rem, flags, tr

def rem_signed(rs1, rs2, trace=False):
    q, r, flg, tr = div_signed(rs1, rs2, trace=trace)
    return r, flg, tr

def remu_unsigned(rs1, rs2, trace=False):
    q, r, flg, tr = divu_unsigned(rs1, rs2, trace=trace)
    return r, flg, tr

