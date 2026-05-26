"""
Unified Pipeline: Decrypt bot .abc files -> .lua source

Steps per file:
  1. Stride-10007 descramble + XOR (key = "name.abc")
  2. ZIP extract (password = "cocos2d: ERROR: Invalid filename <name>")
  3. Disassemble with unluac
  4. Parse disassembly to clean Lua (op54=settable, op56=gettable, op61=gettable, op63=newtable)

Keeps: <name>.abc (original) + <name>.lua (decompiled source)
Intermediate: <name>.luac + <name>.dis.txt (auto-cleaned after success)
"""
import os
import sys
import glob
import zipfile
import io
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
UNLUAC_CP = os.path.join(SCRIPT_DIR, "unluac_src2", "unluac-master", "bin")
UNLUAC_MAIN = "unluac.Main"
BOT_DIR = os.path.join(PROJECT_ROOT, "data", "bot")


def descramble_abc(abc_path, name):
    """Stride-10007 descramble + XOR. Key = 'name.abc', XOR at read-time."""
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
    return bytes(buffer)


def extract_zip(data, name, out_dir):
    """Extract ZIP with dynamic password. Returns extracted bytes or None."""
    pwd = f"cocos2d: ERROR: Invalid filename {name}".encode("utf-8")
    zip_path = os.path.join(out_dir, f"_temp_{name}.zip")
    data_path = os.path.join(out_dir, "data")
    try:
        with open(zip_path, "wb") as f:
            f.write(data)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(path=out_dir, pwd=pwd)
        if os.path.exists(data_path):
            with open(data_path, "rb") as f:
                result = f.read()
            os.remove(data_path)
            return result
    except Exception as e:
        print(f"    ZIP error: {e}")
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)
    return None


def run_unluac_disasm(luac_path, dis_path):
    """Disassemble .luac file with unluac."""
    cmd = ["java", "-cp", UNLUAC_CP, UNLUAC_MAIN, "--disassemble",
           "--output", dis_path, luac_path]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"    unluac disasm error: {e.stderr[:200]}")
        return False


def parse_dis_to_lua(dis_path, lua_path):
    """Parse disassembly to clean Lua using CFG decompiler."""
    try:
        import lua_decompiler
        lua_decompiler.decompile_file(dis_path, lua_path)
        return True
    except Exception as e:
        print(f"    CFG decompile error: {e}")
        return False


def process_file(name):
    """Full pipeline for one .abc file."""
    abc_path = os.path.join(BOT_DIR, f"{name}.abc")
    luac_path = os.path.join(BOT_DIR, f"{name}.luac")
    dis_path = os.path.join(BOT_DIR, f"{name}.dis.txt")
    lua_path = os.path.join(BOT_DIR, f"{name}.lua")

    print(f"\n--- {name}.abc ---")

    # Step 1: Descramble
    data = descramble_abc(abc_path, name)
    print(f"  Descrambled: {len(data)} bytes")

    # Step 2: ZIP extract
    data = extract_zip(data, name, BOT_DIR)
    if data is None:
        print(f"  FAIL: ZIP extraction failed")
        return False
    print(f"  ZIP extracted: {len(data)} bytes")

    # Save .luac (intermediate)
    with open(luac_path, "wb") as f:
        f.write(data)

    # Step 3: Disassemble
    if not run_unluac_disasm(luac_path, dis_path):
        return False
    print(f"  Disassembled: {dis_path}")

    # Step 4: Parse to Lua
    if not parse_dis_to_lua(dis_path, lua_path):
        return False
    print(f"  Lua source: {lua_path}")

    # Clean intermediates
    if os.path.exists(luac_path):
        os.remove(luac_path)
    if os.path.exists(dis_path):
        os.remove(dis_path)

    return True


def main():
    print("=" * 60)
    print("BOT ABC DECRYPTION PIPELINE")
    print("Decryption -> Disassembly -> Lua Source")
    print("=" * 60)

    abc_files = sorted(glob.glob(os.path.join(BOT_DIR, "*.abc")))
    results = {}

    for abc_path in abc_files:
        name = os.path.splitext(os.path.basename(abc_path))[0]
        ok = process_file(name)
        results[name] = ok

    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    for name, ok in results.items():
        lua_path = os.path.join(BOT_DIR, f"{name}.lua")
        size = os.path.getsize(lua_path) if os.path.exists(lua_path) else 0
        status = "OK" if ok and size > 0 else "FAIL"
        print(f"  {name}.abc -> {name}.lua  [{size:,} bytes]  {status}")


if __name__ == "__main__":
    main()
