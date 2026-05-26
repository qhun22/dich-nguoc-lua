"""
Batch pipeline: decrypt all data/**/*.abc to adjacent .lua

Steps per file:
  1) Stride-10007 descramble + XOR (key = "name.abc")
  2) ZIP extract (password = "cocos2d: ERROR: Invalid filename <name>")
  3) Disassemble with unluac
  4) Parse disassembly to Lua via lua_decompiler

Skips files when .lua already exists (default behavior).
"""
import os
import sys
import zipfile
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DEFAULT_DATA_DIR = os.path.join(PROJECT_ROOT, "data")
UNLUAC_CP = os.path.join(SCRIPT_DIR, "unluac_src2", "unluac-master", "bin")
UNLUAC_MAIN = "unluac.Main"

sys.path.insert(0, SCRIPT_DIR)


def descramble_abc(abc_path, name):
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
    except Exception:
        return None
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)
    return None


def run_unluac_disasm(luac_path, dis_path):
    cmd = [
        "java",
        "-cp",
        UNLUAC_CP,
        UNLUAC_MAIN,
        "--disassemble",
        "--output",
        dis_path,
        luac_path,
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True, None
    except subprocess.CalledProcessError as exc:
        return False, (exc.stderr or exc.stdout or "")[:200]


def parse_dis_to_lua(dis_path, lua_path):
    try:
        import lua_decompiler

        lua_decompiler.decompile_file(dis_path, lua_path)
        return True, None
    except Exception as exc:
        return False, str(exc)[:200]


def iter_abc_files(root_dir):
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.lower().endswith(".abc"):
                yield os.path.join(root, file)


def process_file(abc_path, overwrite=False):
    name = os.path.splitext(os.path.basename(abc_path))[0]
    out_dir = os.path.dirname(abc_path)
    lua_path = os.path.join(out_dir, f"{name}.lua")
    luac_path = os.path.join(out_dir, f"{name}.luac")
    dis_path = os.path.join(out_dir, f"{name}.dis.txt")

    if (not overwrite) and os.path.exists(lua_path):
        return "SKIP", "exists"

    data = descramble_abc(abc_path, name)
    data = extract_zip(data, name, out_dir)
    if data is None:
        return "FAIL", "zip"

    with open(luac_path, "wb") as f:
        f.write(data)

    ok, err = run_unluac_disasm(luac_path, dis_path)
    if not ok:
        return "FAIL", f"unluac: {err}"

    ok, err = parse_dis_to_lua(dis_path, lua_path)
    if not ok:
        return "FAIL", f"decompile: {err}"

    if os.path.exists(luac_path):
        os.remove(luac_path)
    if os.path.exists(dis_path):
        os.remove(dis_path)

    return "OK", ""


def main():
    overwrite = False
    data_dir = DEFAULT_DATA_DIR

    # Optional CLI: python batch_decrypt_data.py <data_dir> [--overwrite]
    for arg in sys.argv[1:]:
        if arg == "--overwrite":
            overwrite = True
        else:
            data_dir = arg
    total = 0
    ok_count = 0
    skip_count = 0
    fail_count = 0
    fail_samples = []

    for abc_path in iter_abc_files(data_dir):
        total += 1
        status, detail = process_file(abc_path, overwrite=overwrite)
        if status == "OK":
            ok_count += 1
        elif status == "SKIP":
            skip_count += 1
        else:
            fail_count += 1
            if len(fail_samples) < 20:
                fail_samples.append((abc_path, detail))

    print("=" * 60)
    print("BATCH DECRYPT ALL DATA ABC")
    print(f"Root:  {data_dir}")
    print("=" * 60)
    print(f"Total: {total}")
    print(f"OK:    {ok_count}")
    print(f"Skip:  {skip_count}")
    print(f"Fail:  {fail_count}")
    if fail_samples:
        print("\nSample failures:")
        for path, detail in fail_samples:
            print(f"  {path} -> {detail}")


if __name__ == "__main__":
    main()
