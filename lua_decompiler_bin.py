"""
Lua Decompiler from Binary Bytecode for data\\bot files.
Reads .luac binary directly and produces clean Lua source code.
"""
import struct
import re
import os


# Opcode names (standard Lua 5.1 + known bot remappings)
OPCODES = {
    0: 'MOVE', 1: 'LOADK', 2: 'LOADBOOL', 3: 'LOADNIL', 4: 'GETUPVAL',
    5: 'GETGLOBAL', 6: 'SETGLOBAL', 7: 'SETUPVAL', 8: 'SETTABLE',
    9: 'NEWTABLE', 10: 'SELF', 11: 'ADD', 12: 'SUB', 13: 'MUL',
    14: 'DIV', 15: 'MOD', 16: 'POW', 17: 'UNM', 18: 'NOT', 19: 'LEN',
    20: 'CONCAT', 21: 'JMP', 22: 'EQ', 23: 'LT', 24: 'LE',
    25: 'TEST', 26: 'TESTSET', 27: 'CALL', 28: 'TAILCALL',
    29: 'RETURN', 30: 'FORLOOP', 31: 'FORPREP', 32: 'TFORLOOP',
    33: 'SETLIST', 34: 'CLOSE', 35: 'CLOSURE', 36: 'VARARG',
    37: 'EQ', 38: 'ADD', 42: 'LT', 43: 'LE', 44: 'SETGLOBAL',
    45: 'SELF', 46: 'CONCAT', 47: 'EQ', 48: 'SETGLOBAL',
    49: 'MOVE', 50: 'LT', 51: 'LE', 52: 'LT', 53: 'LE',
    54: 'SETTABLE', 55: 'SELF', 56: 'GETTABLE', 57: 'GETTABLE',
    58: 'EQ', 59: 'SELF', 60: 'SETGLOBAL', 61: 'GETTABLE',
    62: 'MOVE', 63: 'NEWTABLE',
}


def decode_instruction(data, pos):
    if pos + 4 > len(data):
        return None, pos + 4
    w = struct.unpack("<I", data[pos:pos+4])[0]
    opcode = w & 0x3F
    a = (w >> 6) & 0xFF
    c = (w >> 14) & 0x1FF
    b = (w >> 23) & 0x1FF
    bx = (w >> 6) & 0x3FFFF
    return {
        'raw': w,
        'opcode': opcode,
        'a': a, 'b': b, 'c': c, 'bx': bx,
        'name': OPCODES.get(opcode, 'OP%d' % opcode),
    }, pos + 4


def read_luastring(data, pos):
    if pos >= len(data):
        return None, pos
    sz = data[pos]
    pos += 1
    if sz == 0:
        return b"", pos
    if sz == 0xFF:
        if pos + 4 > len(data):
            return None, pos
        sz = struct.unpack("<I", data[pos:pos+4])[0]
        pos += 4
    if pos + sz > len(data):
        return data[pos:], len(data)
    return data[pos:pos+sz], pos + sz


def skip_constant(data, pos):
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
        _, pos = read_luastring(data, pos)
    elif t == 0x53:  # INTEGER
        pos += 8
    return pos


def skip_upvalue(data, pos):
    if pos >= len(data):
        return pos
    pos += 1
    try:
        _, pos = read_luastring(data, pos)
    except:
        pos += 1
    return pos


def skip_local(data, pos):
    if pos >= len(data):
        return pos
    pos += 1
    if pos >= len(data):
        return pos
    pos += 1
    try:
        _, pos = read_luastring(data, pos)
    except:
        pos += 1
    return pos


def parse_function_proto(data, pos, indent=0):
    out = []
    prefix = "  " * indent

    # Function header (12 bytes)
    if pos + 12 > len(data):
        return out, len(data)
    pos += 12

    # Source name
    src_bytes, pos = read_luastring(data, pos)
    try:
        src_name = src_bytes.decode('utf-8', errors='replace')
    except:
        src_name = repr(src_bytes)
    if src_name:
        out.append("%s-- source: %s" % (prefix, src_name))

    # linedefined
    if pos + 4 > len(data):
        return out, pos
    linedef = struct.unpack("<i", data[pos:pos+4])[0]
    pos += 4

    # numparams, is_vararg, maxstacksize, n_upvalues
    if pos + 4 > len(data):
        return out, pos
    numparams = data[pos]
    is_vararg = data[pos+1]
    maxstacksize = data[pos+2]
    n_upvalues = data[pos+3]
    pos += 4

    # n_instructions
    if pos + 4 > len(data):
        return out, pos
    n_inst = struct.unpack("<I", data[pos:pos+4])[0]
    pos += 4

    # Decode all instructions
    instructions = []
    for j in range(n_inst):
        inst, pos = decode_instruction(data, pos)
        if inst:
            instructions.append(inst)

    # n_constants
    if pos + 4 > len(data):
        return out, pos
    n_const = struct.unpack("<I", data[pos:pos+4])[0]
    pos += 4

    # Parse constants
    constants = {}
    for j in range(n_const):
        if pos >= len(data):
            break
        t = data[pos]
        pos += 1
        if t == 0:  # NIL
            constants[j] = None
        elif t == 1:  # BOOLEAN
            constants[j] = bool(data[pos])
            pos += 1
        elif t == 3:  # NUMBER
            val = struct.unpack("<d", data[pos:pos+8])[0]
            pos += 8
            constants[j] = val
        elif t == 4:  # STRING
            s, pos = read_luastring(data, pos)
            try:
                constants[j] = s.decode('utf-8', errors='replace')
            except:
                constants[j] = s
        elif t == 0x53:  # INTEGER
            val = struct.unpack("<q", data[pos:pos+8])[0]
            pos += 8
            constants[j] = val
        else:
            pos += 8
            constants[j] = None

    # n_upvalues
    if pos + 4 > len(data):
        return out, pos
    n_up = struct.unpack("<I", data[pos:pos+4])[0]
    pos += 4
    upvalues = ["upval%d" % j for j in range(n_up)]
    for j in range(n_up):
        pos = skip_upvalue(data, pos)

    # n_locals
    if pos + 4 > len(data):
        return out, pos
    n_loc = struct.unpack("<I", data[pos:pos+4])[0]
    pos += 4
    locals_info = []
    for j in range(n_loc):
        if pos >= len(data):
            break
        startpc = data[pos]; pos += 1
        if pos >= len(data):
            break
        endpc = data[pos]; pos += 1
        if pos >= len(data):
            break
        name_bytes, pos = read_luastring(data, pos)
        try:
            name = name_bytes.decode('utf-8', errors='replace')
        except:
            name = repr(name_bytes)
        locals_info.append({'name': name, 'start': startpc, 'end': endpc})

    # n_functions
    if pos + 4 > len(data):
        return out, pos
    n_funcs = struct.unpack("<I", data[pos:pos+4])[0]
    pos += 4

    # Decompile this function
    func_source = decompile_function_proto(
        instructions, constants, locals_info, upvalues,
        linedef, numparams, is_vararg, maxstacksize, indent
    )
    out.extend(func_source)

    # Recursively process nested functions
    for j in range(n_funcs):
        nested_out, pos = parse_function_proto(data, pos, indent)
        out.extend(nested_out)

    return out, pos


def decompile_function_proto(instructions, constants, locals_info, upvalues,
                             linedef, numparams, is_vararg, maxstacksize, indent):
    out = []
    prefix = "  " * indent

    # Function name
    func_name = "main"
    if linedef > 0:
        func_name = "f%d" % linedef

    # Upvalue declarations
    for uv in upvalues:
        out.append("%slocal %s = ..." % (prefix, uv))

    out.append("%sfunction %s()" % (prefix, func_name))

    # Build locals map
    locals_map = {}
    for loc in locals_info:
        for r in range(loc['start'], loc['end'] + 1):
            locals_map[r] = loc['name']

    # Decompile instructions
    i = 0
    while i < len(instructions):
        inst = instructions[i]
        op = inst['name']
        a = inst['a']
        b = inst['b']
        c = inst['c']
        bx = inst['bx']

        def rn(reg):
            return locals_map.get(reg, "r%d" % reg)

        def const_val(idx):
            if idx in constants:
                v = constants[idx]
                if v is None: return "nil"
                if isinstance(v, bool): return "true" if v else "false"
                if isinstance(v, str): return '"%s"' % v
                return str(v)
            return "k%d" % idx

        def rv(idx):
            return const_val(idx & 0xFF)

        # Custom bot opcodes
        if inst['opcode'] == 54:  # op54 settable
            t = rn(a)
            key = const_val(b)
            val = const_val(c)
            out.append("%s  %s[%s] = %s" % (prefix, t, key, val))
        elif inst['opcode'] == 56:  # op56 gettable
            t = rn(a)
            obj = rn(b)
            key = rn(c)
            out.append("%s  %s = %s[%s]" % (prefix, t, obj, key))
        elif inst['opcode'] == 61:  # op61 gettable
            t = rn(a)
            obj = rn(b)
            key = const_val(c)
            out.append("%s  %s = %s[%s]" % (prefix, t, obj, key))
        elif inst['opcode'] == 63:  # op63 newtable
            out.append("%s  %s = {}" % (prefix, rn(a)))

        # Standard opcodes
        elif op == 'LT':
            out.append("%s  if not (%s < %s) then goto skip_%d" % (prefix, rn(b), rn(c), i))
        elif op == 'LE':
            out.append("%s  if not (%s <= %s) then goto skip_%d" % (prefix, rn(b), rn(c), i))
        elif op == 'EQ':
            out.append("%s  if not (%s == %s) then goto skip_%d" % (prefix, rv(b), rv(c), i))
        elif op == 'LOADK':
            out.append("%s  %s = %s" % (prefix, rn(a), const_val(bx)))
        elif op == 'LOADBOOL':
            val = "true" if b else "false"
            out.append("%s  %s = %s" % (prefix, rn(a), val))
        elif op == 'LOADNIL':
            out.append("%s  %s = nil" % (prefix, rn(a)))
        elif op == 'GETGLOBAL':
            name = constants.get(bx, "k%d" % bx)
            if isinstance(name, str):
                out.append("%s  %s = %s" % (prefix, rn(a), name))
            else:
                out.append("%s  %s = _G[%s]" % (prefix, rn(a), const_val(bx)))
        elif op == 'SETGLOBAL':
            name = constants.get(bx, "k%d" % bx)
            if isinstance(name, str):
                out.append("%s  %s = %s" % (prefix, name, rn(a)))
            else:
                out.append("%s  _G[%s] = %s" % (prefix, const_val(bx), rn(a)))
        elif op == 'MOVE':
            if a != b:
                out.append("%s  %s = %s" % (prefix, rn(a), rn(b)))
        elif op == 'GETUPVAL':
            out.append("%s  %s = _ENV[%d]" % (prefix, rn(a), b))
        elif op == 'SETUPVAL':
            out.append("%s  _ENV[%d] = %s" % (prefix, b, rn(a)))
        elif op == 'SELF':
            out.append("%s  %s = %s; %s = %s[%s]" % (prefix, rn(a+1), rn(b), rn(a), rn(b), const_val(c)))
        elif op == 'ADD':
            out.append("%s  %s = %s + %s" % (prefix, rn(a), rv(b), rv(c)))
        elif op == 'SUB':
            out.append("%s  %s = %s - %s" % (prefix, rn(a), rv(b), rv(c)))
        elif op == 'MUL':
            out.append("%s  %s = %s * %s" % (prefix, rn(a), rv(b), rv(c)))
        elif op == 'DIV':
            out.append("%s  %s = %s / %s" % (prefix, rn(a), rv(b), rv(c)))
        elif op == 'MOD':
            out.append("%s  %s = %s %% %s" % (prefix, rn(a), rv(b), rv(c)))
        elif op == 'POW':
            out.append("%s  %s = %s ^ %s" % (prefix, rn(a), rv(b), rv(c)))
        elif op == 'UNM':
            out.append("%s  %s = -%s" % (prefix, rn(a), rv(b)))
        elif op == 'NOT':
            out.append("%s  %s = not %s" % (prefix, rn(a), rv(b)))
        elif op == 'LEN':
            out.append("%s  %s = #%s" % (prefix, rn(a), rv(b)))
        elif op == 'CONCAT':
            out.append("%s  %s = %s .. %s" % (prefix, rn(a), rv(b), rv(c)))
        elif op == 'JMP':
            out.append("%s  goto skip_%d -- jmp %+d" % (prefix, i + 1 + bx, bx))
        elif op == 'CALL':
            nb = b - 1 if b > 0 else 0
            nc = c - 1 if c > 0 else 0
            out.append("%s  %s(%d args) -- %d returns" % (prefix, rn(a), nb, nc))
        elif op == 'TAILCALL':
            nb = b - 1 if b > 0 else 0
            out.append("%s  return %s(%d args)" % (prefix, rn(a), nb))
        elif op == 'RETURN':
            out.append("%s  return" % prefix)
        elif op == 'TEST':
            out.append("%s  if not %s then goto skip_%d" % (prefix, rn(a), i))
        elif op == 'TESTSET':
            out.append("%s  if %s then %s = %s else goto skip_%d" % (prefix, rv(b), rn(a), rv(b), i))
        elif op == 'FORPREP':
            out.append("%s  -- for init, goto %+d" % (prefix, bx))
        elif op == 'FORLOOP':
            out.append("%s  -- for loop, goto %+d" % (prefix, bx))
        elif op == 'TFORLOOP':
            out.append("%s  -- tfor loop" % prefix)
        elif op == 'SETLIST':
            n = c * 50 if c > 0 else 0
            out.append("%s  -- t[%d] = %d elements" % (prefix, n, b))
        elif op == 'CLOSURE':
            out.append("%s  %s = function() -- nested" % (prefix, rn(a)))
        elif op == 'VARARG':
            out.append("%s  %s = ..." % (prefix, rn(a)))
        elif op == 'CLOSE':
            out.append("%s  close(%s)" % (prefix, rn(a)))
        elif op == 'NEWTABLE':
            out.append("%s  %s = {}" % (prefix, rn(a)))
        else:
            out.append("%s  -- %s r%d r%d r%d (opcode=%d)" % (prefix, op, a, b, c, inst['opcode']))

        i += 1

    out.append("%send" % prefix)
    return out


def decompile_luac(luac_data):
    data = bytearray(luac_data)
    if len(data) < 12:
        return ""
    if data[:4] != b'\x1bLua':
        return "-- Invalid Lua signature: %s" % data[:4].hex()

    out = []
    out.append("-- ==============================================================")
    out.append("-- BOT MODULE - Decompiled from binary .luac")
    out.append("-- ==============================================================\n")

    func_lines, pos = parse_function_proto(data, 12, indent=0)
    out.extend(func_lines)

    return "\n".join(out)


def main():
    bot_dir = r"d:\FileD\dota\dgame.app\data\bot"
    files = ["bot2", "botpvp", "botPvpBattle", "botpvpserver",
             "down", "ipconfig", "queue", "tools", "up"]

    for name in files:
        luac_path = os.path.join(bot_dir, "%s.luac" % name)
        if not os.path.exists(luac_path):
            print("  SKIP: %s.luac not found" % name)
            continue

        with open(luac_path, 'rb') as f:
            luac_data = f.read()

        lua_path = os.path.join(bot_dir, "%s_bin.lua" % name)
        source = decompile_luac(luac_data)

        with open(lua_path, 'w', encoding='utf-8') as f:
            f.write(source)

        print("  %s: %d chars -> %s" % (name, len(source), lua_path))


if __name__ == "__main__":
    main()
