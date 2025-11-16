# src/numeric_core/fpu.py
from .adder import ripple_add

def _is_zero(x):
    for b in x:
        if b == 1: return False
    return True

def _or(x):
    for b in x:
        if b == 1: return 1
    return 0

def _match_len(a, b):
    if len(a) == len(b): return a, b
    if len(a) < len(b): return ([0]*(len(b)-len(a))) + a, b
    return a, ([0]*(len(a)-len(b))) + b

def _addu(a, b):
    a, b = _match_len(a, b)
    s, _ = ripple_add(a, b, 0)
    return s

def _subu(a, b):
    a, b = _match_len(a, b)
    inv = [1 - x for x in b]
    one = [0]*(len(b)-1)+[1]
    t, _ = ripple_add(inv, one, 0)
    s, c = ripple_add(a, t, 0)
    return s, c  # c==1 => no borrow

def _bits_to_int(b):
    v = 0
    for x in b: v = (v << 1) | x
    return v

def _int_to_bits(x, n):
    out = [0]*n
    for i in range(n-1, -1, -1):
        out[i] = x & 1
        x >>= 1
    return out

def _round(sig, rm, sign, guard, rnd, sticky):
    if rm == 'RNE':
        inc = 1 if (guard==1 and (rnd==1 or sticky==1 or sig[-1]==1)) else 0
    elif rm == 'RTZ':
        inc = 0
    elif rm == 'RUP':
        inc = 1 if (guard|rnd|sticky)==1 and sign==0 else 0
    elif rm == 'RDN':
        inc = 1 if (guard|rnd|sticky)==1 and sign==1 else 0
    else:
        inc = 0
    if inc:
        one = [0]*(len(sig)-1)+[1]
        sig, _ = ripple_add(sig, one, 0)
    return sig, inc

def _normalize_left(sig):
    sh = 0
    while sig[0]==0 and _or(sig)==1 and sh < len(sig)+1:
        sig = sig[1:]+[0]
        sh += 1
    return sig, sh

def _normalize_right(sig):
    sig = [0] + sig[:-1]
    return sig, 1

def _pack(s,e,f): return [s]+e+f

def _special(e):
    all1 = all(x==1 for x in e)
    all0 = _is_zero(e)
    return all0, all1

def _align(m_small, shift):
    # right shift by 'shift' keeping length; tail -> guard/round/sticky
    if shift <= 0:
        return m_small[:], 0, 0, 0
    L = len(m_small)
    if shift >= L + 2:
        return [0]*L, 0, 0, 1 if _or(m_small) else 0
    kept = m_small[:max(0, L - shift)]
    body = [0]*shift + kept
    tail = m_small[L - shift:] if shift <= L else m_small[:]
    guard = tail[0] if len(tail) >= 1 else 0
    rnd   = tail[1] if len(tail) >= 2 else 0
    sticky = 1 if (len(tail) > 2 and _or(tail[2:])) else 0
    if len(body) != L:
        if len(body) < L: body = [0]*(L-len(body)) + body
        else: body = body[-L:]
    return body, guard, rnd, sticky

def _fadd_core(a_bits, b_bits, we, wf, bias, rm, is_sub):
    sA=a_bits[0]; eA=a_bits[1:1+we]; fA=a_bits[1+we:1+we+wf]
    sB=b_bits[0]; eB=b_bits[1:1+we]; fB=b_bits[1+we:1+we+wf]

    eA0,eA1 = _special(eA)
    eB0,eB1 = _special(eB)

    a_nan = eA1 and not _is_zero(fA)
    b_nan = eB1 and not _is_zero(fB)
    if a_nan or b_nan:
        return _pack(0,[1]*we,[1]+[0]*(wf-1)), {'invalid':1,'overflow':0,'underflow':0,'inexact':0}

    a_inf = eA1 and _is_zero(fA)
    b_inf = eB1 and _is_zero(fB)
    if a_inf or b_inf:
        if (a_inf and b_inf and ((not is_sub and sA!=sB) or (is_sub and sA==sB))):
            return _pack(0,[1]*we,[1]+[0]*(wf-1)), {'invalid':1,'overflow':0,'underflow':0,'inexact':0}
        s = sA if a_inf else sB
        return _pack(s,[1]*we,[0]*wf), {'invalid':0,'overflow':0,'underflow':0,'inexact':0}

    a_zero = eA0 and _is_zero(fA)
    b_zero = eB0 and _is_zero(fB)
    if a_zero and b_zero:
        return _pack(sA & sB,[0]*we,[0]*wf), {'invalid':0,'overflow':0,'underflow':0,'inexact':0}
    if a_zero:
        return _pack(sB ^ (1 if is_sub else 0), eB, fB), {'invalid':0,'overflow':0,'underflow':0,'inexact':0}
    if b_zero:
        return _pack(sA, eA, fA), {'invalid':0,'overflow':0,'underflow':0,'inexact':0}

    mA=[1]+fA; mB=[1]+fB
    EA=_bits_to_int(eA); EB=_bits_to_int(eB)
    if EA>=EB:
        mBig,mSmall,E = mA,mB,EA
        sBig = sA; sSmall = sB ^ (1 if is_sub else 0)
        shift = EA-EB
    else:
        mBig,mSmall,E = mB,mA,EB
        sBig = sB if not is_sub else (1^sA)
        sSmall = sA
        shift = EB-EA

    mSmall, g_align, r_align, s_align = _align(mSmall, shift)
    mBig,  mSmall = _match_len(mBig, mSmall)
    same = (sBig == sSmall)

    if same:
        L = len(mBig)
        m_sum = _addu([0] + mBig, [0] + mSmall)  # L+1 bits
        res_sign = sBig
        if m_sum[0] == 1:
            guard = m_sum[-1] if len(m_sum) >= 1 else 0
            roundb = 0
            sticky = 1 if (s_align or r_align or g_align) else 0
            m, _ = _normalize_right(m_sum)
            E += 1
            m = m[1:]
        else:
            m = m_sum[1:]
            guard = g_align
            roundb = r_align
            sticky = s_align
    else:
        m, _ = _subu(mBig, mSmall)
        res_sign = sBig
        m, sh = _normalize_left(m)
        E -= sh
        guard = g_align
        roundb = r_align
        sticky = s_align

    m_r, inc = _round(m, rm, res_sign, guard, roundb, sticky)
    if inc and m_r[0]==0 and m[0]==1:
        m_r,_ = _normalize_right([1]+m_r)
        E += 1

    if E >= (2**we - 1):
        return _pack(res_sign,[1]*we,[0]*wf), {'invalid':0,'overflow':1,'underflow':0,'inexact':1}
    if E <= 0:
        return _pack(res_sign,[0]*we,[0]*wf), {'invalid':0,'overflow':0,'underflow':1,'inexact':1}

    exp = _int_to_bits(E, we)
    frac = m_r[1:1+wf]
    return _pack(res_sign, exp, frac), {'invalid':0,'overflow':0,'underflow':0,'inexact': (1 if (guard|roundb|sticky) else 0)}

def _fmul_core(a_bits, b_bits, we, wf, bias, rm):
    s = a_bits[0]^b_bits[0]
    eA=a_bits[1:1+we]; fA=a_bits[1+we:1+we+wf]
    eB=b_bits[1:1+we]; fB=b_bits[1+we:1+we+wf]

    eA0,eA1 = _special(eA)
    eB0,eB1 = _special(eB)
    a_nan = eA1 and not _is_zero(fA)
    b_nan = eB1 and not _is_zero(fB)
    if a_nan or b_nan:
        return _pack(0,[1]*we,[1]+[0]*(wf-1)), {'invalid':1,'overflow':0,'underflow':0,'inexact':0}
    a_inf = eA1 and _is_zero(fA)
    b_inf = eB1 and _is_zero(fB)
    a_zero = eA0 and _is_zero(fA)
    b_zero = eB0 and _is_zero(fB)
    if (a_inf and b_zero) or (b_inf and a_zero):
        return _pack(0,[1]*we,[1]+[0]*(wf-1)), {'invalid':1,'overflow':0,'underflow':0,'inexact':0}
    if a_inf or b_inf:
        return _pack(s,[1]*we,[0]*wf), {'invalid':0,'overflow':0,'underflow':0,'inexact':0}
    if a_zero or b_zero:
        return _pack(s,[0]*we,[0]*wf), {'invalid':0,'overflow':0,'underflow':0,'inexact':0}

    mA=[1]+fA; mB=[1]+fB
    prod=[0]*(2*(wf+1))
    mcand=[0]*(wf+1)+mA
    mult=mB[:]
    for _ in range(wf+1):
        if mult[-1]==1:
            prod,_=ripple_add(prod, mcand, 0)
        mcand = mcand[1:]+[0]
        mult = [0]+mult[:-1]

    if prod[0]==1:
        m = prod
        E = _bits_to_int(eA)+_bits_to_int(eB)-bias+1
    else:
        sh=0
        while prod[0]==0 and sh<(wf+2):
            prod = prod[1:]+[0]; sh+=1
        m=prod
        E = _bits_to_int(eA)+_bits_to_int(eB)-bias+1-sh

    frac = m[1:1+wf]
    extra = m[1+wf:1+wf+3]
    guard = extra[0] if len(extra)>0 else 0
    rnd   = extra[1] if len(extra)>1 else 0
    sticky= 1 if (len(extra)>2 and any(extra[2:])) else 0

    frac_r, inc = _round(frac, rm, s, guard, rnd, sticky)
    if inc and frac_r[0]==0 and frac[0]==1:
        E += 1

    if E >= (2**we - 1):
        return _pack(s,[1]*we,[0]*wf), {'invalid':0,'overflow':1,'underflow':0,'inexact':1}
    if E <= 0:
        return _pack(s,[0]*we,[0]*wf), {'invalid':0,'overflow':0,'underflow':1,'inexact':1}

    exp = _int_to_bits(E, we)
    return _pack(s, exp, frac_r), {'invalid':0,'overflow':0,'underflow':0,'inexact': (1 if (guard|rnd|sticky) else 0)}

def fadd_f32(a_bits, b_bits, round_mode='RNE'):
    return _fadd_core(a_bits, b_bits, 8, 23, 127, round_mode, False)

def fsub_f32(a_bits, b_bits, round_mode='RNE'):
    b2 = b_bits[:]; b2[0]=1-b2[0]
    return _fadd_core(a_bits, b2, 8, 23, 127, round_mode, True)

def fmul_f32(a_bits, b_bits, round_mode='RNE'):
    return _fmul_core(a_bits, b_bits, 8, 23, 127, round_mode)

def fadd_f64(a_bits, b_bits, round_mode='RNE'):
    return _fadd_core(a_bits, b_bits, 11, 52, 1023, round_mode, False)

def fsub_f64(a_bits, b_bits, round_mode='RNE'):
    b2 = b_bits[:]; b2[0]=1-b2[0]
    return _fadd_core(a_bits, b2, 11, 52, 1023, round_mode, True)

def fmul_f64(a_bits, b_bits, round_mode='RNE'):
    return _fmul_core(a_bits, b_bits, 11, 52, 1023, round_mode)