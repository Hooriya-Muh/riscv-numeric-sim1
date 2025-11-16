# AI-BEGIN
# src/numeric_core/shifter.py
# Skeleton for SLL/SRL/SRA without using << or >>.
# Implement either an iterative shift register or a barrel shifter using list ops.

def sll(bits, shamt):
    # Left logical: drop MSBs, insert zeros at LSB side.
    n = len(bits)
    # Build result purely with slicing (no <<)
    k = shamt % n
    res = bits[k:] + [0]*k
    return res

def srl(bits, shamt):
    n = len(bits)
    k = shamt % n
    res = [0]*k + bits[:n-k]
    return res

def sra(bits, shamt):
    n = len(bits)
    k = shamt % n
    sign = bits[0] if n>0 else 0
    res = [sign]*k + bits[:n-k]
    return res
# AI-END
