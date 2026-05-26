"""Generate disassembly files for all bot .abc files."""
import os, sys, zipfile, io, subprocess

BOT_DIR = r"d:\FileD\dota\dgame.app\data\bot"
UNLUAC_CP = r"d:\FileD\dota\dgame.app\python_scripts\unluac_src2\unluac-master\bin"

files = ["bot2", "botpvp", "botPvpBattle", "botpvpserver",
         "down", "ipconfig", "queue", "tools", "up"]

for name in files:
    abc_path = os.path.join(BOT_DIR, f"{name}.abc")
    if not os.path.exists(abc_path):
        print(f"  SKIP: {name}.abc not found")
        continue

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

    # Save luac
    luac_path = os.path.join(BOT_DIR, f"{name}.luac")
    with open(luac_path, "wb") as f:
        f.write(luac_data)

    # Disassemble
    dis_path = os.path.join(BOT_DIR, f"{name}.dis.txt")
    cmd = ["java", "-cp", UNLUAC_CP, "unluac.Main", "--disassemble",
           "--output", dis_path, luac_path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        print(f"  {name}: {os.path.getsize(dis_path):,} bytes")
    else:
        print(f"  {name}: FAILED - {r.stderr[:100]}")
