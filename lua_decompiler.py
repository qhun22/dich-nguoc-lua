"""
Clean Lua Decompiler for data\\bot files.
Converts unluac disassembly into readable Lua source code with CFG analysis.
"""
import re
import os


def resolve(arg, constants, locals_map):
    arg = arg.strip()
    if not arg:
        return "?"
    if arg.startswith('k'):
        try:
            idx = int(arg[1:])
            if idx in constants:
                v = constants[idx]
                if isinstance(v, str): return '"%s"' % v
                elif v is True: return "true"
                elif v is False: return "false"
                elif v is None: return "nil"
                elif isinstance(v, float) and v == int(v): return str(int(v))
                return str(v)
            return arg
        except ValueError:
            return arg
    if arg.startswith('r'):
        try:
            rnum = int(arg[1:])
            if rnum in locals_map:
                return locals_map[rnum]
            return "r%d" % rnum
        except ValueError:
            return arg
    return arg


def resolve_name(arg, constants, locals_map):
    r = resolve(arg, constants, locals_map)
    return r.strip('"')


def decompile_inst(opcode, args, constants, locals_map):
    lines = []
    def r(i): return resolve(args[i], constants, locals_map) if i < len(args) else "?"
    def rn(i): return resolve_name(args[i], constants, locals_map) if i < len(args) else "?"

    if opcode == 'op54':
        if len(args) >= 3: lines.append("%s[%s] = %s" % (r(0), r(1), r(2)))
    elif opcode == 'op56':
        if len(args) >= 3: lines.append("%s = %s[%s]" % (r(0), r(1), r(2)))
    elif opcode == 'op61':
        if len(args) >= 3: lines.append("%s = %s[%s]" % (r(0), r(1), r(2)))
    elif opcode == 'op63':
        if args: lines.append("%s = {}" % rn(0))
    elif opcode == 'op57':
        if len(args) >= 3: lines.append("-- op57: %s = %s[%s]" % (rn(0), rn(1), rn(2)))
    elif opcode == 'op58':
        if len(args) >= 3: lines.append("-- op58: %s = %s[%s]" % (rn(0), rn(1), rn(2)))
    elif opcode == 'op59':
        if len(args) >= 3: lines.append("-- op59: %s = %s[%s]" % (rn(0), rn(1), r(2)))
    elif opcode == 'lt':
        if len(args) >= 3: lines.append("-- cmp %s < %s" % (r(1), r(2)))
    elif opcode == 'le':
        if len(args) >= 3: lines.append("-- cmp %s <= %s" % (r(1), r(2)))
    elif opcode == 'eq':
        if len(args) >= 3: lines.append("-- cmp %s == %s" % (r(1), r(2)))
    elif opcode == 'loadk':
        if len(args) >= 2: lines.append("%s = %s" % (rn(0), r(1)))
    elif opcode == 'loadbool':
        if len(args) >= 2:
            val = "true" if args[1] != '0' else "false"
            lines.append("%s = %s" % (rn(0), val))
    elif opcode == 'loadnil':
        lines.append("%s = nil" % rn(0))
    elif opcode == 'getglobal':
        if len(args) >= 2:
            k = resolve(args[1], constants, locals_map)
            if k.startswith('"') and '_G' not in k:
                lines.append("%s = %s" % (rn(0), k.strip('"')))
            else:
                lines.append("%s = _G[%s]" % (rn(0), k))
    elif opcode == 'setglobal':
        if len(args) >= 2:
            k = resolve(args[1], constants, locals_map)
            if k.startswith('"') and '_G' not in k:
                lines.append("%s = %s" % (k.strip('"'), rn(0)))
            else:
                lines.append("_G[%s] = %s" % (k, rn(0)))
    elif opcode == 'move':
        if len(args) >= 2 and rn(0) != rn(1):
            lines.append("%s = %s" % (rn(0), rn(1)))
    elif opcode == 'getupval':
        if args: lines.append("%s = _ENV[%s]" % (rn(0), args[1]))
    elif opcode == 'setupval':
        if args: lines.append("_ENV[%s] = %s" % (args[1], rn(0)))
    elif opcode == 'newtable':
        if args: lines.append("%s = {}" % rn(0))
    elif opcode in ('add', 'sub', 'mul', 'div', 'mod', 'pow'):
        syms = {'add': '+', 'sub': '-', 'mul': '*', 'div': '/', 'mod': '%', 'pow': '^'}
        if len(args) >= 3: lines.append("%s = %s %s %s" % (rn(0), r(1), syms[opcode], r(2)))
    elif opcode in ('unm', 'not', 'len'):
        syms = {'unm': '-', 'not': 'not ', 'len': '#'}
        if len(args) >= 2: lines.append("%s = %s%s" % (rn(0), syms[opcode], r(1)))
    elif opcode == 'concat':
        if len(args) >= 3: lines.append("%s = %s .. %s" % (rn(0), r(1), r(2)))
    elif opcode == 'call':
        if args: lines.append("%s(%s)" % (rn(0), str(int(args[1]) - 1) if args[1] != '0' else ''))
    elif opcode == 'tailcall':
        if args: lines.append("return %s(%s)" % (rn(0), str(int(args[1]) - 1) if args[1] != '0' else ''))
    elif opcode == 'return':
        if len(args) >= 2 and args[1] != '0':
            lines.append("return -- %d values" % (int(args[1]) - 1))
        else:
            lines.append("return")
    elif opcode == 'test':
        if args: lines.append("-- test %s" % r(0))
    elif opcode == 'testset':
        if len(args) >= 3: lines.append("if %s then %s = %s end" % (rn(1), rn(0), rn(1)))
    elif opcode in ('forprep', 'forloop', 'tforloop'):
        lines.append("-- %s" % opcode)
    elif opcode == 'setlist':
        lines.append("-- t[%s] = %s" % (args[2] if len(args) >= 3 else '?', args[1] if len(args) >= 2 else '?'))
    elif opcode == 'vararg':
        if args: lines.append("%s = ..." % rn(0))
    elif opcode == 'self':
        if len(args) >= 3: lines.append("%s = %s; %s = %s[%s]" % (rn(0), rn(1), rn(1), rn(1), r(2)))
    elif opcode == 'close':
        lines.append("close(%s)" % rn(0))
    elif opcode == 'closure':
        if len(args) >= 2: lines.append("%s = function() -- nested" % rn(0))
    elif opcode == 'jmp':
        lines.append("-- jmp %s" % (args[0] if args else '?'))
    else:
        resolved = [resolve(a, constants, locals_map) for a in args]
        lines.append("-- %s %s" % (opcode, ', '.join(resolved)))

    return lines


def parse_function(lines, start_idx):
    constants = {}
    locals_map = {}
    upvalues = []
    instructions = []
    func_name = ""
    i = start_idx

    parts = re.split(r'\s+', lines[i].strip())
    if len(parts) >= 2:
        func_name = parts[1]
    i += 1

    while i < len(lines):
        meta = lines[i].strip()
        i += 1

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
                    s = int(parts2[2])
                    e = int(parts2[3])
                    for r in range(s, e + 1):
                        locals_map[r] = local_name
                except ValueError:
                    pass
            continue
        if meta.startswith('.upvalue'):
            parts2 = meta.split('\t')
            if len(parts2) >= 2:
                up_name = parts2[1].strip().replace('"', '')
                upvalues.append(up_name)
            continue
        if meta.startswith('.constant'):
            parts2 = meta.split('\t')
            if len(parts2) >= 3:
                kn = parts2[1].strip()
                kv = parts2[2].strip()
                try:
                    ki = int(kn[1:])
                    if kv.startswith('"') and kv.endswith('"'):
                        constants[ki] = kv[1:-1]
                    elif kv == 'true': constants[ki] = True
                    elif kv == 'false': constants[ki] = False
                    elif kv == 'nil': constants[ki] = None
                    else:
                        try: constants[ki] = int(kv) if '.' not in kv else float(kv)
                        except: constants[ki] = kv
                except ValueError:
                    pass
            continue

    while i < len(lines):
        raw = lines[i].strip()
        i += 1
        if raw.startswith('.function'):
            i -= 1
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
        except (ValueError, IndexError):
            continue

    return {
        'name': func_name,
        'constants': constants,
        'locals': locals_map,
        'upvalues': upvalues,
        'instructions': instructions,
    }, i


def build_cfg(instructions):
    """Build basic blocks and identify control flow structures."""
    n = len(instructions)
    if n == 0:
        return []

    # Find all jump targets
    jump_targets = set([0])  # entry block
    jmp_info = {}  # position -> target position

    for idx, inst in enumerate(instructions):
        op = inst['opcode']
        args = inst['args']

        if op in ('lt', 'le', 'eq', 'test'):
            # Look ahead for jmp
            for j in range(idx + 1, min(idx + 5, n)):
                if instructions[j]['opcode'] == 'jmp':
                    try:
                        offset = int(instructions[j]['args'][0])
                        target = j + 1 + offset
                        jmp_info[idx] = (j, target)
                        jump_targets.add(idx)
                        if 0 <= target < n:
                            jump_targets.add(target)
                    except (ValueError, IndexError):
                        pass
                    break
        elif op == 'jmp':
            try:
                offset = int(args[0])
                target = idx + 1 + offset
                jmp_info[idx] = (idx, target)
                if 0 <= target < n:
                    jump_targets.add(target)
            except (ValueError, IndexError):
                pass

    # Sort targets
    targets = sorted(jump_targets)

    # Build blocks
    blocks = []
    block_map = {}  # position -> block index

    for idx, target in enumerate(targets):
        block_map[target] = idx

    for i, target in enumerate(targets):
        block_end = targets[i + 1] if i + 1 < len(targets) else n
        block = {
            'start': target,
            'end': block_end,
            'instructions': instructions[target:block_end],
            'is_loop_header': False,
            'loop_type': None,  # 'while', 'repeat', 'for'
            'condition': None,
            'body': None,
            'else_body': None,
            'skip_target': None,
        }
        blocks.append(block)

    # Identify loop headers (targets that are jumped to from later instructions)
    for idx, inst in enumerate(instructions):
        if idx in jmp_info:
            jmp_pos, target = jmp_info[idx]
            if target < idx:
                # Backward jump = loop
                for b in blocks:
                    if b['start'] == target:
                        b['is_loop_header'] = True
                        b['loop_type'] = 'while'

    return blocks


def decompile_function_cfg(func_data):
    """Decompile function with full CFG analysis."""
    name = func_data['name']
    constants = func_data['constants']
    locals_map = func_data['locals']
    upvalues = func_data['upvalues']
    instructions = func_data['instructions']

    output = []
    output.append("function %s()" % name)

    for uv in upvalues:
        output.append("  local %s = ..." % uv)

    if not instructions:
        output.append("end")
        return output

    n = len(instructions)

    # Build CFG: identify if-then blocks
    # Pattern: comparison (lt/le/eq) followed by jmp
    # The jmp target = skip target (where we go if condition is FALSE)
    # The fall-through = body (where we go if condition is TRUE)

    processed = [False] * n
    skip_counter = 0

    i = 0
    while i < n:
        if processed[i]:
            i += 1
            continue

        inst = instructions[i]
        op = inst['opcode']
        args = inst['args']

        # Check for if-then pattern: comparison -> jmp
        if op in ('lt', 'le', 'eq', 'test') and len(args) >= 2:
            # Find the jmp
            jmp_idx = None
            jmp_target = None

            for j in range(i + 1, min(i + 5, n)):
                if instructions[j]['opcode'] == 'jmp':
                    try:
                        offset = int(instructions[j]['args'][0])
                        jmp_idx = j
                        jmp_target = j + 1 + offset
                    except (ValueError, IndexError):
                        pass
                    break

            if jmp_idx is not None:
                # Determine if this is if-then or while loop
                if jmp_target > i:
                    # Forward jump = if-then (skip body if condition is FALSE)
                    # But check: does the body jump back? (if-then-else)
                    # Look at what comes between jmp target and current pos
                    body_end = jmp_target

                    # Check if there's a jmp back to 'i' at end of body
                    is_if_else = False
                    if body_end < n:
                        # Look for backward jmp within the body
                        for k in range(max(jmp_idx + 1, body_end - 3), body_end):
                            if k >= n:
                                break
                            if instructions[k]['opcode'] == 'jmp':
                                try:
                                    off = int(instructions[k]['args'][0])
                                    target = k + 1 + off
                                    if target <= i:
                                        is_if_else = True
                                        break
                                except:
                                    pass

                    # Generate if-then or if-then-else
                    syms = {'lt': '<', 'le': '<=', 'eq': '=='}
                    if op == 'test':
                        cond = "not %s" % resolve(args[0], constants, locals_map)
                    elif len(args) >= 3:
                        cond = "not (%s %s %s)" % (
                            resolve(args[1], constants, locals_map),
                            syms.get(op, op),
                            resolve(args[2], constants, locals_map)
                        )
                    else:
                        cond = "not %s" % resolve(args[0], constants, locals_map)

                    output.append("  if %s then" % cond)

                    # Mark comparison and jmp as processed
                    processed[i] = True
                    processed[jmp_idx] = True

                    # Body: instructions between comparison and jmp
                    for k in range(i + 1, jmp_idx):
                        processed[k] = True

                    # Decompile body
                    for k in range(i + 1, jmp_idx):
                        for line in decompile_inst(
                                instructions[k]['opcode'],
                                instructions[k]['args'],
                                constants, locals_map):
                            output.append("    %s" % line)

                    # If there's an else block
                    if is_if_else:
                        output.append("  else")
                        # Find and decompile else block
                        # The else block is from jmp_target to the backward jmp
                        for k in range(jmp_idx + 1, body_end):
                            if k >= n:
                                break
                            processed[k] = True
                            for line in decompile_inst(
                                    instructions[k]['opcode'],
                                    instructions[k]['args'],
                                    constants, locals_map):
                                output.append("    %s" % line)

                    output.append("  end")
                    i = jmp_idx + 1
                    continue

                else:
                    # Backward jump = while loop
                    # Body: instructions between comparison and jmp
                    syms = {'lt': '<', 'le': '<=', 'eq': '=='}
                    if op == 'test':
                        cond = "%s" % resolve(args[0], constants, locals_map)
                    elif len(args) >= 3:
                        cond = "(%s %s %s)" % (
                            resolve(args[1], constants, locals_map),
                            syms.get(op, op),
                            resolve(args[2], constants, locals_map)
                        )
                    else:
                        cond = "%s" % resolve(args[0], constants, locals_map)

                    output.append("  while %s do" % cond)
                    processed[i] = True
                    processed[jmp_idx] = True

                    # Body
                    for k in range(i + 1, jmp_idx):
                        processed[k] = True
                        for line in decompile_inst(
                                instructions[k]['opcode'],
                                instructions[k]['args'],
                                constants, locals_map):
                            output.append("    %s" % line)

                    output.append("  end")
                    i = jmp_idx + 1
                    continue

        # TESTSET
        if op == 'testset':
            if len(args) >= 3:
                output.append("  if %s then %s = %s end" % (
                    resolve_name(args[1], constants, locals_map),
                    resolve_name(args[0], constants, locals_map),
                    resolve_name(args[1], constants, locals_map)
                ))
            processed[i] = True
            i += 1
            continue

        # RETURN
        if op == 'return':
            for line in decompile_inst(op, args, constants, locals_map):
                output.append("  %s" % line)
            processed[i] = True
            i += 1
            continue

        # JMP (unconditional)
        if op == 'jmp':
            processed[i] = True
            i += 1
            continue

        # Regular instruction
        for line in decompile_inst(op, args, constants, locals_map):
            output.append("  %s" % line)
        processed[i] = True
        i += 1

    output.append("end")
    return output


def decompile_file(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    output = []
    output.append("-- ==============================================================")
    output.append("-- BOT MODULE - Decompiled Lua Source")
    output.append("-- Generated by lua_decompiler.py")
    output.append("-- ==============================================================\n")

    i = 0
    while i < len(lines):
        if lines[i].strip().startswith('.function'):
            func_data, i = parse_function(lines, i)
            func_out = decompile_function_cfg(func_data)
            output.extend(func_out)
            output.append("")
        else:
            i += 1

    result = "\n".join(output)

    # Post-processing: remove bytecode structure comments
    lines = result.split('\n')
    clean = []
    for line in lines:
        stripped = line.strip()
        # Skip bytecode comments
        if stripped.startswith('-- cmp'):
            continue
        if stripped.startswith('-- test '):
            continue
        if stripped.startswith('-- op'):
            continue
        if stripped.startswith('-- jmp '):
            continue
        if stripped.startswith('-- for '):
            continue
        if stripped.startswith('-- extrabyte'):
            continue
        if stripped.startswith('-- settable') or stripped.startswith('-- gettable'):
            continue
        if stripped.startswith('-- t['):
            continue
        if stripped.startswith('-- getglobal') or stripped.startswith('-- setglobal'):
            continue
        if stripped.startswith('-- '):
            if stripped[2:3].isalpha():
                continue  # Skip other op-like comments
        clean.append(line)
    result = '\n'.join(clean)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)
    return len(result)


def main():
    bot_dir = r"d:\FileD\dota\dgame.app\data\bot"
    files = ["bot2", "botpvp", "botPvpBattle", "botpvpserver",
             "down", "ipconfig", "queue", "tools", "up"]

    print("Lua Decompiler (CFG)")
    print("=" * 50)

    for name in files:
        dis_path = os.path.join(bot_dir, "%s.dis.txt" % name)
        lua_path = os.path.join(bot_dir, "%s_decompiled.lua" % name)
        if not os.path.exists(dis_path):
            print("  SKIP: %s.dis.txt not found" % name)
            continue
        n = decompile_file(dis_path, lua_path)
        print("  %s: %d chars" % (name, n))


if __name__ == "__main__":
    main()
