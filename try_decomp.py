"""
Patch bot bytecode to add RETURN instruction at end of each function.
This fixes unluac's 'Function doesn't end with implicit return' error.

Lua 5.1 function structure:
  [source name - byte string]
  linedefined: int32
  numparams: byte
  is_vararg: byte
  maxstacksize: byte
  n_upvalues: byte
  n_instructions: uint32
  [instructions x n_instructions]
  n_constants: uint32
  [constants]
  n_upvalues: uint32
  [upvalues]
  n_locals: uint32
  [locals]
  n_functions: uint32
  [nested functions...]
"""
import struct, os, sys, zipfile, io

BOT_DIR = r"d:\FileD\dota\dgame.app\data\bot"
UNLUAC_CP = r"d:\FileD\dota\dgame.app\python_scripts\unluac_src2\unluac-master\bin"
OPMAP = r"d:\FileD\dota\dgame.app\python_scripts\bot_opmap_full.map"


def read_lua_string(data, pos):
    """Read a Lua string: length byte + content. Returns (string_bytes, new_pos)."""
    if pos >= len(data):
        return b"", pos
    sz = data[pos]
    pos += 1
    if sz == 0:
        return b"", pos
    if sz == 0xFF:
        # Long string: 4-byte length
        if pos + 4 > len(data):
            return b"", pos
        sz = struct.unpack("<I", data[pos:pos+4])[0]
        pos += 4
    if pos + sz > len(data):
        return data[pos:], len(data)
    return data[pos:pos+sz], pos + sz


def skip_constant(data, pos):
    """Skip one constant. Returns new position."""
    if pos >= len(data):
        return pos
    t = data[pos]
    pos += 1
    if t == 0:  # NIL
        pass
    elif t == 1:  # BOOLEAN
        pass
    elif t == 3:  # NUMBER
        pos += 8
    elif t == 4:  # STRING
        _, pos = read_lua_string(data, pos)
    elif t == 0x53:  # INTEGER (Lua 5.3+)
        pos += 8
    return pos


def skip_upvalue(data, pos):
    """Skip one upvalue record."""
    if pos >= len(data):
        return pos
    pos += 1  # in_stack flag
    # idx is a string (in_stack=true) or int (in_stack=false)
    # For simplicity, try to skip as string
    try:
        s, pos = read_lua_string(data, pos)
    except:
        pos += 1
    return pos


def skip_local(data, pos):
    """Skip one local variable record."""
    if pos >= len(data):
        return pos
    pos += 1  # startpc (byte or int)
    if pos >= len(data):
        return pos
    pos += 1  # endpc (byte or int)
    if pos >= len(data):
        return pos
    # name (string)
    try:
        _, pos = read_lua_string(data, pos)
    except:
        pos += 1
    return pos


def patch_function(data, pos, out_data):
    """Parse one function, add RETURN if missing, return new position."""
    func_start = pos

    # Function header (12 bytes - same format as main header)
    if pos + 12 > len(data):
        out_data.extend(data[pos:])
        return len(data)

    # Read all 12 header bytes
    func_header = data[pos:pos+12]
    out_data.extend(func_header)
    pos += 12

    # Source name
    src_bytes, pos = read_lua_string(data, pos)
    out_data.append(len(src_bytes) if len(src_bytes) < 0xFF else 0xFF)
    if len(src_bytes) >= 0xFF:
        out_data.extend(struct.pack("<I", len(src_bytes)))
    out_data.extend(src_bytes)

    # linedefined (int32)
    if pos + 4 <= len(data):
        out_data.extend(data[pos:pos+4])
        pos += 4

    # numparams, is_vararg, maxstacksize, n_upvalues (each 1 byte)
    for _ in range(4):
        if pos < len(data):
            out_data.append(data[pos])
            pos += 1

    # n_instructions (uint32)
    if pos + 4 > len(data):
        return len(data)
    n_inst = struct.unpack("<I", data[pos:pos+4])[0]
    out_data.extend(data[pos:pos+4])
    pos += 4

    # Copy instructions
    inst_start = pos
    for j in range(n_inst):
        if pos + 4 <= len(data):
            out_data.extend(data[pos:pos+4])
            pos += 4

    # RETURN instruction (opcode 28, A=0, B=1, C=0)
    # In standard Lua 5.1: RETURN op has A=0 (ret from base), B=1 (1 return value)
    # Instruction format: [opcode:6][A:8][C:9][B:9]
    # RETURN: opcode=28=0x1C, A=0, B=1, C=0
    # Layout: bits: [5:0]=opcode, [13:6]=A, [22:14]=C, [31:23]=B
    return_inst = struct.pack("<I", 0x0000001C)  # opcode=28, A=0, B=1, C=0
    out_data.extend(return_inst)
    n_inst += 1

    # Patch n_instructions count
    inst_count_pos = len(out_data) - 4 - 4 - n_inst * 4 - 4
    # out_data currently has: header(12) + src + linedef(4) + numparams+vararg+maxstack+upvalues(4) + n_inst(4)
    # We need to patch the n_inst we just wrote
    # Last 4 bytes of out_data is the n_inst count we wrote
    # But we need to patch the ORIGINAL n_inst, not the one we just appended

    # Find where n_inst was written in out_data
    # It was written at out_data position len(out_data) - 4 (before we added RETURN)
    # Wait, let me trace more carefully...

    # Actually, we need to patch the n_inst count BEFORE adding RETURN
    # Let me restructure:
    # 1. Save position of n_inst in output
    # 2. Write instructions
    # 3. Overwrite n_inst with n_inst + 1

    inst_count_patch_pos = len(out_data) - 4 - n_inst * 4 - 4
    # Actually no. Let me think again.

    # We need to patch byte-by-byte. Let me rebuild the logic.

    # The issue: I'm writing n_inst (old value) then RETURN. I need to write n_inst+1.
    # But I've already written the old value. I need to overwrite the last 4 bytes.
    # n_inst is at position: len(out_data) - 4 (after writing it, before RETURN)
    # After writing RETURN, n_inst is at len(out_data) - 4 - 4 = len(out_data) - 8

    n_inst_patch_pos = len(out_data) - 4 - 4  # position of n_inst in out_data
    new_n_inst = struct.pack("<I", n_inst)
    out_data[n_inst_patch_pos:n_inst_patch_pos+4] = new_n_inst

    # n_constants (uint32)
    if pos + 4 > len(data):
        return pos
    n_const = struct.unpack("<I", data[pos:pos+4])[0]
    out_data.extend(data[pos:pos+4])
    pos += 4

    # Skip constants
    const_start = pos
    for j in range(n_const):
        pos = skip_constant(data, pos)
    out_data.extend(data[const_start:pos])

    # n_upvalues (uint32)
    if pos + 4 > len(data):
        return pos
    n_up = struct.unpack("<I", data[pos:pos+4])[0]
    out_data.extend(data[pos:pos+4])
    pos += 4

    # Skip upvalues
    up_start = pos
    for j in range(n_up):
        pos = skip_upvalue(data, pos)
    out_data.extend(data[up_start:pos])

    # n_locals (uint32)
    if pos + 4 > len(data):
        return pos
    n_loc = struct.unpack("<I", data[pos:pos+4])[0]
    out_data.extend(data[pos:pos+4])
    pos += 4

    # Skip locals
    loc_start = pos
    for j in range(n_loc):
        pos = skip_local(data, pos)
    out_data.extend(data[loc_start:pos])

    # n_functions (uint32)
    if pos + 4 > len(data):
        return pos
    n_funcs = struct.unpack("<I", data[pos:pos+4])[0]
    out_data.extend(data[pos:pos+4])
    pos += 4

    # Recursively process nested functions
    for j in range(n_funcs):
        pos = patch_function(data, pos, out_data)

    return pos


def patch_bot_luac(luac_data):
    """Add RETURN instruction to each function in the bytecode."""
    data = bytearray(luac_data)
    out = bytearray()

    # Lua header (12 bytes)
    if len(data) < 12:
        return bytes(data)
    out.extend(data[:12])
    pos = 12

    # Process main (top-level) function
    pos = patch_function(data, pos, out)

    return bytes(out)


def patch_bot_luac_v2(luac_data):
    """Simpler approach: find instruction count fields and pad."""
    data = bytearray(luac_data)
    out = bytearray()
    pos = 0

    # Copy global header (12 bytes)
    if len(data) < 12:
        return bytes(data)
    out.extend(data[:12])
    pos = 12

    def copy_and_patch(data, pos, out):
        """Copy function data, adding RETURN at end."""
        start = pos

        # Copy header (12 bytes)
        if pos + 12 > len(data):
            out.extend(data[pos:])
            return len(data)
        out.extend(data[pos:pos+12])
        pos += 12

        # Source name (byte string)
        if pos < len(data):
            sz = data[pos]
            out.append(sz)
            pos += 1
            if sz == 0:
                pass
            elif sz == 0xFF:
                if pos + 4 <= len(data):
                    out.extend(data[pos:pos+4])
                    pos += 4
            else:
                end = min(pos + sz, len(data))
                out.extend(data[pos:end])
                pos = end

        # Copy 4 bytes: linedefined(int32) + numparams(byte) + is_vararg(byte) + maxstacksize(byte)
        if pos + 4 > len(data):
            return len(data)
        out.extend(data[pos:pos+4])
        pos += 4

        # Copy n_upvalues (byte)
        if pos < len(data):
            out.append(data[pos])
            pos += 1

        # n_instructions (uint32) - need to patch this
        if pos + 4 > len(data):
            return len(data)
        n_inst = struct.unpack("<I", data[pos:pos+4])[0]
        n_inst_pos = len(out)
        out.extend(data[pos:pos+4])
        pos += 4

        # Copy instructions
        inst_start = pos
        for j in range(n_inst):
            if pos + 4 <= len(data):
                out.extend(data[pos:pos+4])
                pos += 4

        # ===== ADD RETURN INSTRUCTION =====
        # RETURN opcode = 28, A=0, B=1, C=0
        return_inst = struct.pack("<I", 0x0000001C)
        out.extend(return_inst)
        # Patch n_inst count
        new_n = struct.pack("<I", n_inst + 1)
        out[n_inst_pos:n_inst_pos+4] = new_n

        # Copy n_constants
        if pos + 4 > len(data):
            return pos
        n_const = struct.unpack("<I", data[pos:pos+4])[0]
        out.extend(data[pos:pos+4])
        pos += 4

        # Copy constants
        for j in range(n_const):
            if pos >= len(data):
                break
            t = data[pos]
            out.append(t)
            pos += 1
            if t == 0:  # NIL
                pass
            elif t == 1:  # BOOLEAN
                pass
            elif t == 3:  # NUMBER
                if pos + 8 <= len(data):
                    out.extend(data[pos:pos+8])
                    pos += 8
            elif t == 4:  # STRING
                if pos < len(data):
                    sz2 = data[pos]
                    out.append(sz2)
                    pos += 1
                    if sz2 == 0xFF:
                        if pos + 4 <= len(data):
                            out.extend(data[pos:pos+4])
                            pos += 4
                    elif sz2 > 0 and sz2 < 0xFF:
                        end = min(pos + sz2, len(data))
                        out.extend(data[pos:end])
                        pos = end

        # Copy n_upvalues
        if pos + 4 > len(data):
            return pos
        out.extend(data[pos:pos+4])
        pos += 4

        # Copy upvalues (each: 1 byte flag + name string)
        n_up_actual = struct.unpack("<I", out[len(out)-4:len(out)-4+4])[0] if len(out) >= 4 else 0
        for j in range(n_up_actual):
            if pos >= len(data):
                break
            out.append(data[pos])
            pos += 1
            # Try to skip name string
            if pos < len(data):
                sz2 = data[pos]
                out.append(sz2)
                pos += 1
                if sz2 == 0xFF and pos + 4 <= len(data):
                    out.extend(data[pos:pos+4])
                    pos += 4
                elif sz2 > 0 and sz2 < 0xFF:
                    end = min(pos + sz2, len(data))
                    out.extend(data[pos:end])
                    pos = end

        # Copy n_locals
        if pos + 4 > len(data):
            return pos
        out.extend(data[pos:pos+4])
        pos += 4

        # Copy locals (each: 1 byte startpc + 1 byte endpc + string name)
        n_loc_actual = struct.unpack("<I", out[len(out)-4:len(out)-4+4])[0] if len(out) >= 4 else 0
        for j in range(n_loc_actual):
            if pos >= len(data):
                break
            out.append(data[pos]); pos += 1
            if pos < len(data):
                out.append(data[pos]); pos += 1
            if pos < len(data):
                sz2 = data[pos]
                out.append(sz2); pos += 1
                if sz2 == 0xFF and pos + 4 <= len(data):
                    out.extend(data[pos:pos+4]); pos += 4
                elif sz2 > 0 and sz2 < 0xFF:
                    end = min(pos + sz2, len(data))
                    out.extend(data[pos:end]); pos = end

        # Copy n_functions
        if pos + 4 > len(data):
            return pos
        out.extend(data[pos:pos+4])
        pos += 4

        return pos

    # Process main function
    pos = copy_and_patch(data, pos, out)

    return bytes(out)


def main():
    name = "bot2"
    abc_path = os.path.join(BOT_DIR, f"{name}.abc")

    # Descramble
    with open(abc_path, "rb") as f:
        encrypted = f.read()
    size = len(encrypted)
    buffer = bytearray(size)
    key = f"{name}.abc".encode("utf-8")
    key_len = len(key)
    pos = 0
    for i in range(size):
        dest = pos % size
        buffer[dest] = encrypted[i] ^ key[i % key_len]
        pos += 10007
    data = bytes(buffer)

    # ZIP
    pwd = f"cocos2d: ERROR: Invalid filename {name}".encode("utf-8")
    zf = zipfile.ZipFile(io.BytesIO(data))
    luac_data = zf.read("data", pwd=pwd)

    print(f"Original .luac: {len(luac_data)} bytes")

    # Patch
    patched = patch_bot_luac_v2(luac_data)
    print(f"Patched .luac: {len(patched)} bytes")

    # Save
    patched_path = os.path.join(BOT_DIR, f"{name}_patched.luac")
    with open(patched_path, "wb") as f:
        f.write(patched)

    # Try unluac decompile
    out_path = os.path.join(BOT_DIR, f"{name}_decomp.lua")
    import subprocess
    cmd = [
        "java", "-cp", UNLUAC_CP, "unluac.Main",
        "--opmap", OPMAP,
        "--output", out_path,
        patched_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(f"\nunluac RC: {result.returncode}")
    if result.stderr:
        print(f"STDERR: {result.stderr[:500]}")
    if result.stdout:
        print(f"STDOUT: {result.stdout[:500]}")

    if os.path.exists(out_path):
        with open(out_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        print(f"\nDecompiled ({len(content)} chars):")
        print(content[:5000])


if __name__ == "__main__":
    main()
