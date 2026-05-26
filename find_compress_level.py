# -*- coding: utf-8 -*-
"""
Tim muc nen chinh xac de tao ZIP cung kich thuoc
"""
import os
import sys
import zipfile
import io
import zlib

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

FILE_NAME = "ipconfig"
ABC_FILE = r"d:\FileD\dota\ios\dgame.app\data\bot\ipconfig.abc"

def descramble_abc(encrypted, name):
    size = len(encrypted)
    buffer = bytearray(size)
    key = f"{name}.abc".encode('utf-8')
    key_len = len(key)
    pos = 0
    for i in range(size):
        dest = pos % size
        buffer[dest] = encrypted[i] ^ key[i % key_len]
        pos += 10007
    return bytes(buffer)


def main():
    print("TIM MUC NEN CHINH XAC")
    print("=" * 60)
    
    # Doc file goc va giai ma
    with open(ABC_FILE, "rb") as f:
        abc_data = f.read()
    
    zip_data = descramble_abc(abc_data, FILE_NAME)
    target_size = len(zip_data)
    print(f"Kich thuoc muc tieu: {target_size} bytes")
    
    # Doc Lua bytecode
    pwd = f"cocos2d: ERROR: Invalid filename {FILE_NAME}".encode('utf-8')
    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        luac_data = zf.read("data", pwd=pwd)
    
    print(f"Lua bytecode: {len(luac_data)} bytes")
    
    # Thu cac muc nen
    print("\nThu cac muc nen:")
    for level in range(0, 10):
        if level == 0:
            # No compression (STORE)
            compressed = luac_data
        else:
            compressed = zlib.compress(luac_data, level)
        
        print(f"  Level {level}: {len(compressed)} bytes (chenh lech: {len(compressed) - target_size:+d})")
    
    # Thu tao ZIP voi zlib directly
    print("\nThu voi zlib.deflate:")
    for wbits in range(15):
        try:
            compressed = zlib.compress(luac_data, 6)
            # wbits: -15 to -8 = raw deflate, 8-15 = zlib wrapper
            if wbits < 8:
                # Raw deflate
                compressed_raw = zlib.compress(luac_data, 6)
                # Them zlib header/footer
                header = b'\x78\x9c'  # zlib header thong thuong
                result = header + compressed_raw + zlib.crc32(compressed_raw).to_bytes(4, 'little') + len(compressed_raw).to_bytes(4, 'little')
            else:
                result = zlib.compress(luac_data, 6)
            
            print(f"  wbits={wbits}: {len(result)} bytes (chenh lech: {len(result) - target_size:+d})")
        except Exception as e:
            print(f"  wbits={wbits}: loi - {e}")


if __name__ == "__main__":
    main()
