# Simple RV32I CPU simulator in Python
# Single-cycle style, runs prog.hex files.

from typing import List


# ---------------- helpers ----------------

def mask32(x: int) -> int:
    return x & 0xFFFFFFFF


def sign_extend(x: int, bits: int) -> int:
    sign_bit = 1 << (bits - 1)
    if x & sign_bit:
        x = x | (~((1 << bits) - 1))
    return mask32(x)


# -------------- instruction decode --------------

def decode_fields(inst: int):
    opcode = inst & 0x7F
    rd = (inst >> 7) & 0x1F
    funct3 = (inst >> 12) & 0x7
    rs1 = (inst >> 15) & 0x1F
    rs2 = (inst >> 20) & 0x1F
    funct7 = (inst >> 25) & 0x7F
    return opcode, rd, funct3, rs1, rs2, funct7


def imm_i(inst: int) -> int:
    imm = (inst >> 20) & 0xFFF
    return sign_extend(imm, 12)


def imm_s(inst: int) -> int:
    imm_4_0 = (inst >> 7) & 0x1F
    imm_11_5 = (inst >> 25) & 0x7F
    imm = (imm_11_5 << 5) | imm_4_0
    return sign_extend(imm, 12)


def imm_b(inst: int) -> int:
    bit11 = (inst >> 7) & 0x1
    bit4_1 = (inst >> 8) & 0xF
    bit10_5 = (inst >> 25) & 0x3F
    bit12 = (inst >> 31) & 0x1
    imm = (bit12 << 12) | (bit11 << 11) | (bit10_5 << 5) | (bit4_1 << 1)
    return sign_extend(imm, 13)


def imm_u(inst: int) -> int:
    return inst & 0xFFFFF000


def imm_j(inst: int) -> int:
    bit20 = (inst >> 31) & 0x1
    bit10_1 = (inst >> 21) & 0x3FF
    bit11 = (inst >> 20) & 0x1
    bit19_12 = (inst >> 12) & 0xFF
    imm = (bit20 << 20) | (bit19_12 << 12) | (bit11 << 11) | (bit10_1 << 1)
    return sign_extend(imm, 21)


# ---------------- register file ----------------

class RegFile:
    def __init__(self):
        self.regs: List[int] = [0] * 32

    def read(self, idx: int) -> int:
        if idx == 0:
            return 0
        return self.regs[idx]

    def write(self, idx: int, value: int):
        if idx == 0:
            return
        self.regs[idx] = mask32(value)

    def dump(self):
        for i in range(32):
            print(f"x{i:02d} = 0x{self.read(i):08X}")


# ---------------- memory models ----------------

class InstrMemory:
    def __init__(self, words: List[int]):
        self.words = words

    def fetch(self, pc: int) -> int:
        idx = pc // 4
        if idx < 0 or idx >= len(self.words):
            return 0
        return self.words[idx]


class DataMemory:
    def __init__(self):
        self.mem = {}  # address -> 32-bit word

    def load_word(self, addr: int) -> int:
        addr = addr & 0xFFFFFFFF
        if addr % 4 != 0:
            # simple: treat unaligned as zero
            return 0
        return self.mem.get(addr, 0)

    def store_word(self, addr: int, value: int):
        addr = addr & 0xFFFFFFFF
        if addr % 4 != 0:
            return
        self.mem[addr] = mask32(value)

    def dump_region(self, base: int, count: int):
        for i in range(count):
            addr = base + 4 * i
            v = self.mem.get(addr, 0)
            print(f"[0x{addr:08X}] = 0x{v:08X}")


# ---------------- CPU core ----------------

class CPU:
    def __init__(self, imem: InstrMemory, dmem: DataMemory):
        self.imem = imem
        self.dmem = dmem
        self.regs = RegFile()
        self.pc = 0
        self.running = True
        self.step_count = 0

    def step(self):
        inst = self.imem.fetch(self.pc)
        self.step_count += 1

        # halt on 0 or on jal x0,0 (0x0000006F from sample)
        if inst == 0 or inst == 0x0000006F:
            self.running = False
            return

        opcode, rd, funct3, rs1, rs2, funct7 = decode_fields(inst)

        pc_next = self.pc + 4  # default

        rs1_val = self.regs.read(rs1)
        rs2_val = self.regs.read(rs2)

        if opcode == 0x33:  # R-type
            if funct3 == 0x0:
                if funct7 == 0x00:  # add
                    res = rs1_val + rs2_val
                elif funct7 == 0x20:  # sub
                    res = rs1_val - rs2_val
                else:
                    res = 0
                self.regs.write(rd, res)
            elif funct3 == 0x7:  # and
                self.regs.write(rd, rs1_val & rs2_val)
            elif funct3 == 0x6:  # or
                self.regs.write(rd, rs1_val | rs2_val)
            elif funct3 == 0x4:  # xor
                self.regs.write(rd, rs1_val ^ rs2_val)
            elif funct3 == 0x1:  # sll
                shamt = rs2_val & 0x1F
                self.regs.write(rd, mask32(rs1_val << shamt))
            elif funct3 == 0x5:
                shamt = rs2_val & 0x1F
                if funct7 == 0x00:  # srl
                    self.regs.write(rd, (rs1_val & 0xFFFFFFFF) >> shamt)
                elif funct7 == 0x20:  # sra
                    v = sign_extend(rs1_val & 0xFFFFFFFF, 32)
                    self.regs.write(rd, v >> shamt)
        elif opcode == 0x13:  # I-type ALU (addi and, or, xor, shifts if needed)
            imm = imm_i(inst)
            if funct3 == 0x0:  # addi
                self.regs.write(rd, rs1_val + imm)
            elif funct3 == 0x7:  # andi
                self.regs.write(rd, rs1_val & imm)
            elif funct3 == 0x6:  # ori
                self.regs.write(rd, rs1_val | imm)
            elif funct3 == 0x4:  # xori
                self.regs.write(rd, rs1_val ^ imm)
            elif funct3 == 0x1:  # slli
                shamt = imm & 0x1F
                self.regs.write(rd, mask32(rs1_val << shamt))
            elif funct3 == 0x5:
                shamt = imm & 0x1F
                if (imm >> 10) & 0x3F == 0x00:  # srlI
                    self.regs.write(rd, (rs1_val & 0xFFFFFFFF) >> shamt)
                elif (imm >> 10) & 0x3F == 0x10:  # sraI
                    v = sign_extend(rs1_val & 0xFFFFFFFF, 32)
                    self.regs.write(rd, v >> shamt)
        elif opcode == 0x03:  # loads
            imm = imm_i(inst)
            addr = rs1_val + imm
            if funct3 == 0x2:  # lw
                v = self.dmem.load_word(addr)
                self.regs.write(rd, v)
        elif opcode == 0x23:  # stores
            imm = imm_s(inst)
            addr = rs1_val + imm
            if funct3 == 0x2:  # sw
                self.dmem.store_word(addr, rs2_val)
        elif opcode == 0x63:  # branches
            imm = imm_b(inst)
            if funct3 == 0x0:  # beq
                if mask32(rs1_val) == mask32(rs2_val):
                    pc_next = self.pc + imm
            elif funct3 == 0x1:  # bne
                if mask32(rs1_val) != mask32(rs2_val):
                    pc_next = self.pc + imm
        elif opcode == 0x6F:  # jal
            imm = imm_j(inst)
            self.regs.write(rd, self.pc + 4)
            pc_next = self.pc + imm
        elif opcode == 0x67:  # jalr
            imm = imm_i(inst)
            self.regs.write(rd, self.pc + 4)
            target = (rs1_val + imm) & ~1
            pc_next = mask32(target)
        elif opcode == 0x37:  # lui
            imm = imm_u(inst)
            self.regs.write(rd, imm)
        elif opcode == 0x17:  # auipc
            imm = imm_u(inst)
            self.regs.write(rd, self.pc + imm)
        else:
            # unknown opcode -> stop
            self.running = False

        self.pc = mask32(pc_next)

    def run(self, max_steps: int = 100000):
        while self.running and self.step_count < max_steps:
            self.step()


# ---------------- .hex loader + main ----------------

def load_hex_file(path: str) -> List[int]:
    words = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # assume 8 hex chars, no 0x
            try:
                w = int(line, 16)
            except ValueError:
                continue
            words.append(w & 0xFFFFFFFF)
    return words


def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python cpu.py prog.hex")
        sys.exit(1)

    prog_path = sys.argv[1]
    words = load_hex_file(prog_path)
    imem = InstrMemory(words)
    dmem = DataMemory()
    cpu = CPU(imem, dmem)

    cpu.run()
    print("Finished. Final register state:")
    cpu.regs.dump()

    # Example: show memory around 0x00010000
    print("\nData memory around 0x00010000:")
    dmem.dump_region(0x00010000, 4)


if __name__ == "__main__":
    main()