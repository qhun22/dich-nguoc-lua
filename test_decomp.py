"""Test patched unluac decompiler on bot2."""
import os, sys, zipfile, io, subprocess

BOT_DIR = r"d:\FileD\dota\dgame.app\data\bot"
UNLUAC_CP = r"d:\FileD\dota\dgame.app\python_scripts\unluac_src2\unluac-master\bin"
OPMAP = r"d:\FileD\dota\dgame.app\python_scripts\bot_opmap_full.map"

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

# Save luac
luac_path = os.path.join(BOT_DIR, f"{name}.luac")
with open(luac_path, "wb") as f:
    f.write(luac_data)

# Decompile with patched unluac + full opmap
out_path = os.path.join(BOT_DIR, f"{name}_decomp.lua")
cmd = [
    "java", "-cp", UNLUAC_CP, "unluac.Main",
    "--opmap", OPMAP,
    "--output", out_path,
    luac_path
]
result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
print(f"RC: {result.returncode}")
if result.stderr:
    # Filter out common warnings
    lines = result.stderr.split('\n')
    for line in lines[:20]:
        if line.strip():
            print(f"  STDERR: {line}")
if result.stdout:
    print(f"  STDOUT: {result.stdout[:200]}")

if os.path.exists(out_path):
    with open(out_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    print(f"\nDecompiled ({len(content)} chars, {content.count(chr(10))+1} lines):")
    print("=" * 60)
    print(content[:5000])
    print("=" * 60)
else:
    print("\nNo output file produced.")
