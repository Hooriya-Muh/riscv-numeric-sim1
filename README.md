# RISC-V Numeric Operations Simulator

This project implements a bit-vector–based numeric core for a RISC-V simulator.  
All arithmetic is performed using explicit bit arrays (0/1 lists), and the
implementation follows the full constraints of the assignment:

- **No built-in arithmetic operators** inside the core (`+ - * / % << >>` prohibited)
- Manual two’s-complement operations
- Ripple-carry full-adder chains for integer ADD/SUB
- Manual shifting logic (no Python shifting)
- Shift-add multiplier (RV32M)
- Restoring divider (RV32M)
- IEEE-754 float32 operations (pack/unpack/add/sub/mul)
- **Float64 operations for extra credit**
- Manual rounding (RNE)
- Full exception flags: invalid, overflow, underflow, inexact
- Bit-vector based internal state and optional traces

A separate lightweight CLI is included for basic demos, but the entire numeric
core is deterministic and free of side effects so it can be plugged into a
multi-cycle CPU later.

All unit tests pass.

---

## Project Structure
src/numeric_core/
bits.py # bit-vector helpers, manual hex ↔ bits lookup tables
adder.py # ripple-carry add/sub, two’s complement negate
shifter.py # logical and arithmetic shifts using lists (no << >>)
alu.py # RV32I ADD/SUB with N, Z, C, V flags
mdu.py # RV32M shift-add multiplication and restoring division
fpu.py # IEEE-754 float32 + float64 add/sub/mul with rounding + flags

tools/
cli.py # simple demo CLI

tests/
test_hex_helpers.py
test_alu_add_sub.py
test_m_extension.py
test_float32.py
test_float64.py


---

## Features

### ✔ Two’s-Complement (32-bit)
- Encoding/decoding
- Overflow detection
- Sign-extend / zero-extend helpers

### ✔ RV32I ADD/SUB
- Implemented using ripple-carry adder
- Flags:
  - **N** negative  
  - **Z** zero  
  - **C** carry  
  - **V** overflow  
- Edge behaviors fully match the spec (e.g., 0x7FFFFFFF + 1 → overflow)

### ✔ RV32M Multiply/Divide
- `MUL`, `DIV`, `REM`, `DIVU`, `REMU`
- Handles special cases:
  - divide-by-zero rules  
  - INT_MIN / -1  
- 32-bit shift-add multiplier
- Restoring division algorithm
- Optional trace output for debugging

### ✔ IEEE-754 Float32
- Pack/unpack
- Align → add/sub → normalize → round → repack
- Special values: ±0, ±∞, NaN
- RNE rounding matches expectations:
  - 0.1 + 0.2 → **0x3E99999A**
- Overflow/underflow flags set correctly

### ✔ Float64 (Extra Credit)
- Full 64-bit pack/unpack and arithmetic

---

## Running Tests

Install pytest:


pip install pytest


Run:


pytest -q


All tests should pass:
- Integer ADD/SUB reference cases  
- RV32M multiply/divide edge cases  
- Float32 rounding tests  
- Float64 extra-credit tests  

---

## CLI Usage (demo only)


python tools/cli.py add 0x7FFFFFFF 0x1
python tools/cli.py sub 0x80000000 0x1
python tools/cli.py mul 0x0000000D 0xFFFFFFF3
python tools/cli.py div 0xFFFFFFF9 0x00000003


---

## Notes

- No built-in numeric helpers (`hex()`, `format()`, `bin()`, `int(...,base)`) were used inside `src/numeric_core`.
- Tests are allowed to use Python arithmetic for expected values.
- The core is modular and cleanly merges into a multi-cycle datapath/CPU.

---

## Academic Integrity & AI Usage

See **AI_USAGE.md** for a summary of where AI was used in a limited, allowed way.
