import re
import sys

def parse_disassembly(filepath, outpath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    out = open(outpath, 'w', encoding='utf-8')
    
    current_func = None
    constants = {}
    locals_map = {}
    
    out.write("# ==========================================\n")
    out.write("# Bot Algorithm Decompiled (Pseudo-Lua)\n")
    out.write("# ==========================================\n\n")

    def resolve(arg):
        if arg in constants:
            val = constants[arg]
            if isinstance(val, str):
                return f'"{val}"'
            return str(val)
        return arg

    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('.function'):
            current_func = line.split('\t')[1] if '\t' in line else line.split(' ')[1]
            constants = {}
            locals_map = {}
            out.write(f"\nfunction {current_func}()\n")
            continue
            
        if line.startswith('.constant'):
            parts = line.split('\t')
            if len(parts) >= 3:
                k_name = parts[1].strip()
                k_val_str = parts[2].strip()
                
                # Check for string
                if k_val_str.startswith('"') and k_val_str.endswith('"'):
                    constants[k_name] = k_val_str[1:-1]
                elif k_val_str == 'true':
                    constants[k_name] = True
                elif k_val_str == 'false':
                    constants[k_name] = False
                elif k_val_str == 'nil':
                    constants[k_name] = 'nil'
                else:
                    try:
                        if '.' in k_val_str:
                            constants[k_name] = float(k_val_str)
                        else:
                            constants[k_name] = int(k_val_str)
                    except ValueError:
                        constants[k_name] = k_val_str
            continue
            
        if line.startswith('.local'):
            # .local "name" start end
            # We just record it for info
            parts = line.split('\t')
            if len(parts) >= 2:
                name = parts[1].strip().replace('"', '')
                out.write(f"    -- local variable {name} defined\n")
            continue
            
        if line.startswith('.line'):
            # .line <num> <opcode> <args>
            # Examples:
            # .line	1	lt             0    r0    r0
            # .line	1	op54          r0    k1    r1 ; k1 = "path"
            # Remove comments
            line_no_comment = line.split(';')[0].strip()
            # Split by whitespace
            parts = re.split(r'\s+', line_no_comment)
            if len(parts) < 3:
                continue
                
            line_num = parts[1]
            opcode = parts[2]
            args = parts[3:]
            
            res_str = f"    -- [Line {line_num}] "
            pseudo = f"{opcode} " + ", ".join(args)
            
            if opcode == 'op54':  # Settable
                if len(args) >= 3:
                    A, B, C = args[0], args[1], args[2]
                    pseudo = f"{A}[{resolve(B)}] = {resolve(C)}"
            elif opcode in ['op56', 'op61', 'op42']:  # Gettable
                if len(args) >= 3:
                    A, B, C = args[0], args[1], args[2]
                    pseudo = f"{A} = {resolve(B)}[{resolve(C)}]"
            elif opcode == 'setglobal':
                if len(args) >= 2:
                    A, B = args[0], args[1]
                    pseudo = f"_G[{resolve(B)}] = {A}"
            elif opcode == 'getglobal':
                if len(args) >= 2:
                    A, B = args[0], args[1]
                    pseudo = f"{A} = _G[{resolve(B)}]"
            elif opcode == 'loadk':
                if len(args) >= 2:
                    A, B = args[0], args[1]
                    pseudo = f"{A} = {resolve(B)}"
            elif opcode == 'move':
                if len(args) >= 2:
                    A, B = args[0], args[1]
                    pseudo = f"{A} = {B}"
            elif opcode == 'call':
                if len(args) >= 3:
                    A, B, C = args[0], args[1], args[2]
                    num_args = int(B) - 1 if B != '0' else 'var'
                    num_rets = int(C) - 1 if C != '0' else 'var'
                    pseudo = f"CALL {A} (args: {num_args}, returns: {num_rets})"
            elif opcode == 'lt':
                if len(args) >= 3:
                    A, B, C = args[0], args[1], args[2]
                    pseudo = f"if not ({resolve(B)} < {resolve(C)}) then skip next"
            elif opcode == 'le':
                if len(args) >= 3:
                    A, B, C = args[0], args[1], args[2]
                    pseudo = f"if not ({resolve(B)} <= {resolve(C)}) then skip next"
            elif opcode == 'eq':
                if len(args) >= 3:
                    A, B, C = args[0], args[1], args[2]
                    pseudo = f"if not ({resolve(B)} == {resolve(C)}) then skip next"
            elif opcode == 'add':
                if len(args) >= 3:
                    pseudo = f"{args[0]} = {resolve(args[1])} + {resolve(args[2])}"
            elif opcode == 'sub':
                if len(args) >= 3:
                    pseudo = f"{args[0]} = {resolve(args[1])} - {resolve(args[2])}"
            elif opcode == 'mul':
                if len(args) >= 3:
                    pseudo = f"{args[0]} = {resolve(args[1])} * {resolve(args[2])}"
            elif opcode == 'div':
                if len(args) >= 3:
                    pseudo = f"{args[0]} = {resolve(args[1])} / {resolve(args[2])}"
            elif opcode == 'mod':
                if len(args) >= 3:
                    pseudo = f"{args[0]} = {resolve(args[1])} % {resolve(args[2])}"
            elif opcode == 'pow':
                if len(args) >= 3:
                    pseudo = f"{args[0]} = {resolve(args[1])} ^ {resolve(args[2])}"
            elif opcode == 'loadbool':
                if len(args) >= 3:
                    A, B, C = args[0], args[1], args[2]
                    pseudo = f"{A} = {'true' if B != '0' else 'false'}"
                    if C != '0':
                        pseudo += " ; skip next"
            elif opcode == 'loadnil':
                if len(args) >= 2:
                    A = args[0]
                    B = args[1]
                    pseudo = f"Registers {A}..{B} = nil"
            elif opcode == 'getupval':
                if len(args) >= 2:
                    pseudo = f"{args[0]} = UPVAL({args[1]})"
            elif opcode == 'setupval':
                if len(args) >= 2:
                    pseudo = f"UPVAL({args[1]}) = {args[0]}"
            elif opcode in ['jmp', 'setlist']:
                if len(args) >= 2:
                    pseudo = f"goto offset {args[1]}"
            elif opcode == 'forprep':
                if len(args) >= 2:
                    pseudo = f"FOR loop init {args[0]}, goto {args[1]}"
            elif opcode == 'forloop':
                if len(args) >= 2:
                    pseudo = f"FOR loop step {args[0]}, goto {args[1]}"
            elif opcode in ['test', 'op50']:
                if len(args) >= 2:
                    pseudo = f"if not {args[0]} then skip next"
            elif opcode == 'testset':
                if len(args) >= 3:
                    pseudo = f"if {args[1]} then {args[0]} = {args[1]} else skip next"
            elif opcode == 'return':
                if len(args) >= 2:
                    num_rets = int(args[1]) - 1 if args[1] != '0' else 'var'
                    pseudo = f"return {num_rets} values starting from {args[0]}"
            elif opcode == 'tailcall':
                if len(args) >= 3:
                    num_args = int(args[1]) - 1 if args[1] != '0' else 'var'
                    pseudo = f"return {args[0]}({num_args} args)"
            elif opcode == 'len':
                if len(args) >= 2:
                    pseudo = f"{args[0]} = #{resolve(args[1])}"
            elif opcode == 'unm':
                if len(args) >= 2:
                    pseudo = f"{args[0]} = -{resolve(args[1])}"
            elif opcode == 'not':
                if len(args) >= 2:
                    pseudo = f"{args[0]} = not {resolve(args[1])}"
            elif opcode in ['op63', 'op50', 'op57', 'op49']:
                # Custom opcodes fallback
                # Often op63 is a variant of move or setup
                pseudo = f"{opcode} " + ", ".join([str(resolve(a)) for a in args])

            out.write(f"{res_str}{pseudo}\n")

    out.write("\n")
    out.close()
    print(f"Decompilation finished. Saved to {outpath}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python parse_bot2.py <input.txt> <output.lua>")
    else:
        parse_disassembly(sys.argv[1], sys.argv[2])
