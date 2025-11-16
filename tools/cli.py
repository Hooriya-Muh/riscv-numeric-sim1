# AI-BEGIN
# tools/cli.py - simple demo CLI (not part of core) that can call core functions and print traces.
# Usage examples:
#   python tools/cli.py add 0x7FFFFFFF 0x1
#   python tools/cli.py sub 0x80000000 0x1
#   python tools/cli.py mul 0x0000000D 0xFFFFFFF3
#   python tools/cli.py div 0xFFFFFFF9 0x00000003

import sys
from src.numeric_core.bits import from_hex_string, to_hex_string, pretty_bin
from src.numeric_core.alu import alu_add, alu_sub
from src.numeric_core.mdu import mul_low32, div_signed

def hx(b): return to_hex_string(b, width_multiple=8)

def main():
    if len(sys.argv)<4:
        print("Usage: python tools/cli.py <add|sub|mul|div> <hexA> <hexB>"); sys.exit(1)
    op, A, B = sys.argv[1], sys.argv[2], sys.argv[3]
    a = from_hex_string(A, width=32)
    b = from_hex_string(B, width=32)
    if op=='add':
        r,f = alu_add(a,b)
        print("A:", hx(a))
        print("B:", hx(b))
        print("R:", hx(r))
        print("FLAGS:", f)
        print("BIN:", pretty_bin(r))
    elif op=='sub':
        r,f = alu_sub(a,b)
        print("A:", hx(a)); print("B:", hx(b)); print("R:", hx(r)); print("FLAGS:", f)
    elif op=='mul':
        r,flg,trace = mul_low32(a,b, trace=True)
        print("A:", hx(a)); print("B:", hx(b)); print("R(low):", hx(r)); print("MUL overflow:", flg['overflow'])
        if trace:
            print("TRACE (first 5 steps):")
            for step in trace[:5]:
                print(step)
    elif op=='div':
        q,r,flg,trace = div_signed(a,b, trace=True)
        print("A:", hx(a)); print("B:", hx(b)); print("Q:", hx(q)); print("R:", hx(r)); print("DIV flags:", flg)
        if trace:
            print("TRACE (first 8 steps):")
            for step in trace[:8]:
                print(step)
    else:
        print("Unknown op:", op); sys.exit(2)

if __name__=='__main__':
    main()
# AI-END
