"""
Parse bot disassembly into clean Lua source with local variable names.

Bot opcode conventions:
  op54 = settable  - format: t[kB] = rC  (B is const, C is register)
  op56 = gettable  - format: t = rB[rC]    (both are registers)
  op61 = gettable  - format: t = rB[kC]    (B is register, C is const)
  op63 = newtable  - standard Lua newtable
"""
import re
import os


def resolve(arg, constants, locals_map):
    """Resolve register or constant to readable name."""
    arg = arg.strip()
    if not arg:
        return "?"

    if arg.startswith('k'):
        try:
            idx = int(arg[1:])
            if idx in constants:
                v = constants[idx]
                if isinstance(v, str):
                    return '"' + v + '"'
                elif v is True:
                    return "true"
                elif v is False:
                    return "false"
                elif v is None:
                    return "nil"
                elif isinstance(v, float) and v == int(v):
                    return str(int(v))
                else:
                    return str(v)
            return arg
        except ValueError:
            return arg

    if arg.startswith('r'):
        try:
            rnum = int(arg[1:])
            if rnum in locals_map:
                return locals_map[rnum]
            return "r" + str(rnum)
        except ValueError:
            return arg

    return arg


def parse_function(lines, i):
    """Parse one function. Returns (output_lines, next_i)."""
    constants = {}
    locals_map = {}
    output = []
    func_name = ""

    # Get function name
    parts = re.split(r'\s+', lines[i].strip())
    if len(parts) >= 2:
        func_name = parts[1]
    output.append("function " + func_name + "()")
    i += 1

    # Collect ALL metadata (locals, upvalues, constants) BEFORE instructions
    while i < len(lines):
        meta = lines[i].strip()
        i += 1

        # Break when we hit actual instructions (.line NNN opcode ...)
        # Check longer prefixes FIRST to avoid .linedefined matching .line
        if meta.startswith('.linedefined') or meta.startswith('.lastlinedefined') or \
           meta.startswith('.source') or meta.startswith('.numparams') or \
           meta.startswith('.is_vararg') or meta.startswith('.maxstacksize'):
            continue

        if meta.startswith('.line'):
            i -= 1
            break

        if meta.startswith('.local'):
            parts2 = re.split(r'\s+', meta)
            if len(parts2) >= 4:
                local_name = parts2[1].strip().replace('"', '')
                try:
                    start_reg = int(parts2[2])
                    end_reg = int(parts2[3])
                    for r in range(start_reg, end_reg + 1):
                        locals_map[r] = local_name
                except ValueError:
                    pass
            continue

        if meta.startswith('.upvalue'):
            parts2 = meta.split('\t')
            if len(parts2) >= 2:
                up_name = parts2[1].strip().replace('"', '')
                output.append("  -- upvalue " + up_name)
            continue

        if meta.startswith('.constant'):
            parts2 = meta.split('\t')
            if len(parts2) >= 3:
                k_name = parts2[1].strip()
                k_val = parts2[2].strip()
                try:
                    k_idx = int(k_name[1:])
                    if k_val.startswith('"') and k_val.endswith('"'):
                        constants[k_idx] = k_val[1:-1]
                    elif k_val == 'true':
                        constants[k_idx] = True
                    elif k_val == 'false':
                        constants[k_idx] = False
                    elif k_val == 'nil':
                        constants[k_idx] = None
                    else:
                        try:
                            if '.' in k_val:
                                constants[k_idx] = float(k_val)
                            else:
                                constants[k_idx] = int(k_val)
                        except ValueError:
                            constants[k_idx] = k_val
                except ValueError:
                    pass
            continue

    # Now process all .line instructions for this function
    while i < len(lines):
        raw = lines[i].strip()
        i += 1

        if raw.startswith('.function'):
            i -= 1
            break

        if not raw.startswith('.line'):
            continue

        comment = ""
        if ';' in raw:
            parts_ln = raw.split(';', 1)
            raw = parts_ln[0].strip()
            comment = " ;" + parts_ln[1].strip()

        parts = re.split(r'\s+', raw.strip())
        if len(parts) < 4:
            continue

        opcode = parts[2]
        args = parts[3:]
        result = ""

        if opcode == 'op54':
            if len(args) >= 3:
                t = resolve(args[0], constants, locals_map)
                key = resolve(args[1], constants, locals_map)
                val = resolve(args[2], constants, locals_map)
                result = f"{t}[{key}] = {val}"

        elif opcode == 'op56':
            if len(args) >= 3:
                t = resolve(args[0], constants, locals_map)
                obj = resolve(args[1], constants, locals_map)
                key = resolve(args[2], constants, locals_map)
                result = f"{t} = {obj}[{key}]"

        elif opcode == 'op61':
            if len(args) >= 3:
                t = resolve(args[0], constants, locals_map)
                obj = resolve(args[1], constants, locals_map)
                key = resolve(args[2], constants, locals_map)
                result = f"{t} = {obj}[{key}]"

        elif opcode == 'op63':
            if len(args) >= 1:
                t = resolve(args[0], constants, locals_map)
                result = f"{t} = {{}}"

        elif opcode == 'lt':
            if len(args) >= 3:
                b = resolve(args[1], constants, locals_map)
                c = resolve(args[2], constants, locals_map)
                result = f"if not ({b} < {c}) then goto skip"

        elif opcode == 'le':
            if len(args) >= 3:
                b = resolve(args[1], constants, locals_map)
                c = resolve(args[2], constants, locals_map)
                result = f"if not ({b} <= {c}) then goto skip"

        elif opcode == 'eq':
            if len(args) >= 3:
                b = resolve(args[1], constants, locals_map)
                c = resolve(args[2], constants, locals_map)
                result = f"if not ({b} == {c}) then goto skip"

        elif opcode == 'loadk':
            if len(args) >= 2:
                t = resolve(args[0], constants, locals_map)
                v = resolve(args[1], constants, locals_map)
                result = f"{t} = {v}"

        elif opcode == 'loadbool':
            if len(args) >= 3:
                t = resolve(args[0], constants, locals_map)
                val = "true" if args[1] != '0' else "false"
                result = f"{t} = {val}"

        elif opcode == 'loadnil':
            if len(args) >= 2:
                t = resolve(args[0], constants, locals_map)
                result = f"{t} = nil"

        elif opcode == 'getglobal':
            if len(args) >= 2:
                t = resolve(args[0], constants, locals_map)
                k = resolve(args[1], constants, locals_map)
                result = f"{t} = _G[{k}]"

        elif opcode == 'setglobal':
            if len(args) >= 2:
                t = resolve(args[0], constants, locals_map)
                k = resolve(args[1], constants, locals_map)
                result = f"_G[{k}] = {t}"

        elif opcode == 'getupval':
            if len(args) >= 2:
                t = resolve(args[0], constants, locals_map)
                result = f"{t} = upval{args[1]}"

        elif opcode == 'setupval':
            if len(args) >= 2:
                t = resolve(args[0], constants, locals_map)
                result = f"upval{args[1]} = {t}"

        elif opcode == 'newtable':
            if len(args) >= 1:
                t = resolve(args[0], constants, locals_map)
                result = f"{t} = {{}}"

        elif opcode == 'closure':
            if len(args) >= 2:
                t = resolve(args[0], constants, locals_map)
                result = f"{t} = function() -- {args[1]}"

        elif opcode == 'move':
            if len(args) >= 2:
                t = resolve(args[0], constants, locals_map)
                s = resolve(args[1], constants, locals_map)
                result = f"{t} = {s}"

        elif opcode in ('add', 'sub', 'mul', 'div', 'mod', 'pow'):
            if len(args) >= 3:
                syms = {'add': '+', 'sub': '-', 'mul': '*', 'div': '/', 'mod': '%', 'pow': '^'}
                t = resolve(args[0], constants, locals_map)
                b = resolve(args[1], constants, locals_map)
                c = resolve(args[2], constants, locals_map)
                result = f"{t} = {b} {syms[opcode]} {c}"

        elif opcode in ('unm', 'not', 'len'):
            if len(args) >= 2:
                syms = {'unm': '-', 'not': 'not ', 'len': '#'}
                t = resolve(args[0], constants, locals_map)
                b = resolve(args[1], constants, locals_map)
                result = f"{t} = {syms[opcode]}{b}"

        elif opcode == 'concat':
            if len(args) >= 3:
                t = resolve(args[0], constants, locals_map)
                b = resolve(args[1], constants, locals_map)
                c = resolve(args[2], constants, locals_map)
                result = f"{t} = {b} .. {c}"

        elif opcode == 'call':
            if len(args) >= 3:
                t = resolve(args[0], constants, locals_map)
                nb = str(int(args[1]) - 1) if args[1] != '0' else 'var'
                nc = str(int(args[2]) - 1) if args[2] != '0' else 'var'
                result = f"{t}({nb} args) -- returns {nc}"

        elif opcode == 'tailcall':
            if len(args) >= 2:
                t = resolve(args[0], constants, locals_map)
                nb = str(int(args[1]) - 1) if args[1] != '0' else 'var'
                result = f"return {t}({nb} args)"

        elif opcode == 'return':
            if len(args) >= 3:
                nb = str(int(args[1]) - 1) if args[1] != '0' else 'var'
                result = f"return -- {nb} values"
            elif len(args) >= 2:
                nb = str(int(args[1]) - 1) if args[1] != '0' else 'var'
                result = f"return -- {nb} values"
            else:
                result = "return"

        elif opcode == 'test':
            if len(args) >= 2:
                t = resolve(args[0], constants, locals_map)
                result = f"if not {t} then goto skip"

        elif opcode == 'testset':
            if len(args) >= 3:
                t = resolve(args[0], constants, locals_map)
                s = resolve(args[1], constants, locals_map)
                result = f"if {s} then {t} = {s} else skip"

        elif opcode == 'forprep':
            if len(args) >= 2:
                result = f"-- for init, goto {args[1]}"
        elif opcode == 'forloop':
            if len(args) >= 2:
                result = f"-- for loop, goto {args[1]}"
        elif opcode == 'tforloop':
            if len(args) >= 2:
                result = f"-- tforloop, goto {args[1]}"

        elif opcode == 'setlist':
            if len(args) >= 3:
                result = f"-- t[{args[2]}] = {args[1]} elements"

        elif opcode == 'vararg':
            if len(args) >= 2:
                t = resolve(args[0], constants, locals_map)
                result = f"{t} = ..."

        elif opcode == 'self':
            if len(args) >= 3:
                t = resolve(args[0], constants, locals_map)
                b = resolve(args[1], constants, locals_map)
                c = resolve(args[2], constants, locals_map)
                result = f"{t} = {b} -- self, {b} = {c}"

        elif opcode == 'jmp':
            if len(args) >= 2:
                result = f"goto {args[1]}"
            elif len(args) >= 1:
                result = f"goto {args[0]}"

        elif opcode == 'close':
            if args:
                t = resolve(args[0], constants, locals_map)
                result = f"close {t}"

        else:
            resolved_args = [resolve(a, constants, locals_map) for a in args]
            result = opcode + " " + ", ".join(resolved_args)

        if result:
            output.append("  " + result + comment)

    output.append("end")
    return output, i


def parse_dis_file(input_path, output_path):
    """Parse full disassembly file to Lua source."""
    with open(input_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    output = []
    i = 0

    while i < len(lines):
        if lines[i].strip().startswith('.function'):
            func_lines, i = parse_function(lines, i)
            output.extend(func_lines)
            output.append("")
        else:
            i += 1

    header = "-- ==============================================================\n"
    header += "-- BOT MODULE - Decompiled from .abc\n"
    header += "-- Bot opcode map: op54=settable, op56=gettable, op61=gettable, op63=newtable\n"
    header += "-- ==============================================================\n\n"

    result = header + "\n".join(output)
    result += "\n\n-- END OF FILE\n"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)

    return result.count('\n')


def main():
    bot_dir = r"d:\FileD\dota\dgame.app\data\bot"
    files = [
        "bot2", "botpvp", "botPvpBattle", "botpvpserver",
        "down", "ipconfig", "queue", "tools", "up"
    ]

    print("Bot Disassembly -> Lua Parser (with local names)")
    print("=" * 50)

    for name in files:
        dis_path = os.path.join(bot_dir, f"{name}.dis.txt")
        lua_path = os.path.join(bot_dir, f"{name}.lua")

        if not os.path.exists(dis_path):
            print(f"  SKIP: {name}.dis.txt not found")
            continue

        n_lines = parse_dis_file(dis_path, lua_path)
        size = os.path.getsize(lua_path)
        print(f"  {name}: {n_lines} lines, {size:,} bytes")


if __name__ == "__main__":
    main()
