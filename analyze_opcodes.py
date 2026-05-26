import re
from collections import defaultdict

def read_raw_instructions(filename):
    opcodes = defaultdict(list)
    with open(filename, 'r') as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 6:
                try:
                    opcode = int(parts[0])
                    a = int(parts[1])
                    b = int(parts[2])
                    c = int(parts[3])
                    bx = int(parts[4])
                    sbx = int(parts[5])
                    raw = int(parts[-1]) if len(parts) == 7 else None
                    opcodes[opcode].append((a, b, c, bx, sbx))
                except ValueError:
                    pass
    return opcodes

opcodes = read_raw_instructions('ai_raw_int.txt')
print("Total unique opcodes:", len(opcodes))
for op, insts in sorted(opcodes.items()):
    # Find max A, B, C, Bx, sBx to infer format
    max_a = max((i[0] for i in insts), default=0)
    max_b = max((i[1] for i in insts), default=0)
    max_c = max((i[2] for i in insts), default=0)
    max_bx = max((i[3] for i in insts), default=0)
    
    # Check if B or C is often > 255 (meaning it uses RK(B) or RK(C))
    b_is_rk = any(i[1] >= 256 for i in insts)
    c_is_rk = any(i[2] >= 256 for i in insts)
    
    # Check if sBx is used
    uses_sbx = any(i[4] != -131071 and i[4] != 0 for i in insts) # sBx = Bx - 131071. If Bx=0, sBx=-131071.
    
    print(f"Opcode {op:2d}: count={len(insts):4d}, maxA={max_a:3d}, maxB={max_b:3d}, maxC={max_c:3d}, b_rk={b_is_rk}, c_rk={c_is_rk}, uses_sbx={uses_sbx}")
