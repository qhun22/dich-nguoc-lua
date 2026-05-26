"""Debug disassembly parsing v2."""
with open(r"d:\FileD\dota\dgame.app\data\bot\bot2.dis.txt", 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

# Find .line instructions
print("First 15 .line lines:")
count = 0
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith('.line'):
        print(f"  [{i:3d}] {stripped[:70]}")
        count += 1
        if count >= 15:
            break

# Check the parser output by running it and printing first 10 instructions
import re
import sys
sys.path.insert(0, r"d:\FileD\dota\dgame.app\python_scripts")
import lua_decompiler

with open(r"d:\FileD\dota\dgame.app\data\bot\bot2.dis.txt", 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

# Manually parse main()
print("\n\n=== Manually parsing main ===")
i = 0
while i < len(lines):
    stripped = lines[i].strip()
    if stripped.startswith('.function'):
        parts = re.split(r'\s+', stripped)
        func_name = parts[1] if len(parts) >= 2 else '?'
        print(f"Found function: {func_name} at line {i}")
        i += 1
        break
    i += 1

constants = {}
locals_map = {}
instructions = []

while i < len(lines):
    stripped = lines[i].strip()
    i += 1

    if stripped.startswith('.linedefined') or stripped.startswith('.lastlinedefined') or \
       stripped.startswith('.source') or stripped.startswith('.numparams') or \
       stripped.startswith('.is_vararg') or stripped.startswith('.maxstacksize'):
        print(f"  Meta: {stripped}")
        continue
    if stripped.startswith('.line'):
        i -= 1
        print(f"  Found .line at {i-1}, breaking")
        break
    if stripped.startswith('.local'):
        print(f"  Local: {stripped}")
        parts2 = re.split(r'\s+', stripped)
        if len(parts2) >= 4:
            local_name = parts2[1].strip().replace('"', '')
            try:
                s = int(parts2[2])
                e = int(parts2[3])
                print(f"    -> {local_name}: r{s}-r{e}")
                for r in range(s, e + 1):
                    locals_map[r] = local_name
            except ValueError as ex:
                print(f"    -> PARSE ERROR: {ex}")
        continue
    if stripped.startswith('.constant'):
        parts2 = stripped.split('\t')
        if len(parts2) >= 3:
            kn = parts2[1].strip()
            kv = parts2[2].strip()
            try:
                ki = int(kn[1:])
                print(f"  Const k{ki} = {kv[:30]}")
                if kv.startswith('"') and kv.endswith('"'):
                    constants[ki] = kv[1:-1]
                elif kv == 'true': constants[ki] = True
                elif kv == 'false': constants[ki] = False
                elif kv == 'nil': constants[ki] = None
                else:
                    try: constants[ki] = int(kv) if '.' not in kv else float(kv)
                    except: constants[ki] = kv
            except ValueError as ex:
                print(f"    PARSE ERROR: {ex}")
        continue

print(f"\nCollected {len(constants)} constants, {len(locals_map)} locals")
print(f"\nNow parsing instructions from line {i}...")

count = 0
while i < len(lines):
    raw = lines[i].strip()
    i += 1
    if raw.startswith('.function'):
        i -= 1
        print(f"  Next function at {i-1}")
        break
    if not raw.startswith('.line'):
        continue
    parts = re.split(r'\s+', raw.strip())
    if len(parts) < 4:
        continue
    try:
        line_num = int(parts[1])
        opcode = parts[2]
        args = parts[3:]
        instructions.append({'line': line_num, 'opcode': opcode, 'args': args})
        count += 1
        if count <= 15:
            print(f"  Inst {count}: {opcode} {args[:3]}")
    except (ValueError, IndexError):
        pass

print(f"\nTotal instructions parsed: {len(instructions)}")
