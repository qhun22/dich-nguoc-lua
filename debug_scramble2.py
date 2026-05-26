# -*- coding: utf-8 -*-
"""
Debug chi tiet: So sanh encrypted goc voi cac phuong phap scramble
"""
import os
import sys
import zipfile
import io

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

FILE_NAME = "ipconfig"
ABC_FILE = r"d:\FileD\dota\ios\dgame.app\data\bot\ipconfig.abc"


def descramble_abc(encrypted, name):
    """Giai ma (da biet dung)."""
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


def tao_zip(data, name):
    pwd = f"cocos2d: ERROR: Invalid filename {name}".encode('utf-8')
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("data", data, compress_type=zipfile.ZIP_STORED)
    return zip_buffer.getvalue()


def main():
    print("DEBUG: So sanh chi tiet")
    print("=" * 60)
    
    # Doc file goc
    with open(ABC_FILE, "rb") as f:
        original_encrypted = f.read()
    print(f"Original encrypted: {len(original_encrypted)} bytes")
    print(f"First 32 bytes: {original_encrypted[:32].hex()}")
    
    # Giai ma de lay ZIP
    zip_data = descramble_abc(original_encrypted, FILE_NAME)
    print(f"\nZIP data: {len(zip_data)} bytes")
    print(f"First 32 bytes: {zip_data[:32].hex()}")
    
    # Doc Lua
    pwd = f"cocos2d: ERROR: Invalid filename {FILE_NAME}".encode('utf-8')
    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        luac_data = zf.read("data", pwd=pwd)
    print(f"\nLua bytecode: {len(luac_data)} bytes")
    
    # Tao ZIP moi
    new_zip = tao_zip(luac_data, FILE_NAME)
    print(f"\nNew ZIP: {len(new_zip)} bytes")
    print(f"First 32 bytes: {new_zip[:32].hex()}")
    print(f"Are they equal? {zip_data == new_zip}")
    
    # Thu scramble chi tiet
    print("\n" + "=" * 60)
    print("THU SCRAMBLE CHI TIET")
    print("=" * 60)
    
    size = len(new_zip)
    key = f"{FILE_NAME}.abc".encode('utf-8')
    key_len = len(key)
    stride = 10007
    
    print(f"\nSize: {size}, Key: {key}")
    
    # Tinh toan permutation
    print("\nTinh permutation (dest = (i * stride) % size):")
    perm = {}
    for i in range(size):
        dest = (i * stride) % size
        perm[i] = dest
    
    # Dem so lan moi dest duoc gap
    from collections import Counter
    counter = Counter(perm.values())
    print(f"Cac dest duoc gap: {len(counter)} / {size} unique")
    print(f"Cac dest khong duoc gap: {[d for d in range(size) if d not in counter]}")
    
    # Phuong phap 5: Su dung XOR truoc khi tinh dest
    print("\n[Thu 5] Scramble nhu nhung XOR voi key cua dest:")
    encrypted = bytearray(size)
    for i in range(size):
        dest = (i * stride) % size
        encrypted[dest] = new_zip[i] ^ key[dest % key_len]
    
    print(f"Encrypted: {encrypted[:32].hex()}")
    print(f"Original: {original_encrypted[:32].hex()}")
    print(f"Match: {bytes(encrypted) == original_encrypted}")
    
    # Thu 6: XOR voi key cua i, nhung ghi vao dest
    print("\n[Thu 6] XOR voi key cua i, ghi vao dest:")
    encrypted = bytearray(size)
    for i in range(size):
        dest = (i * stride) % size
        encrypted[dest] = new_zip[i] ^ key[i % key_len]
    
    print(f"Encrypted: {encrypted[:32].hex()}")
    print(f"Original: {original_encrypted[:32].hex()}")
    print(f"Match: {bytes(encrypted) == original_encrypted}")
    
    # Thu 7: Nhu 6 nhung nguoc thu tu
    print("\n[Thu 7] Doc tu new_zip[i], ghi vao encrypted[dest], dest = (i * stride) % size:")
    encrypted = bytearray(size)
    for dest in range(size):
        # Tim i sao cho dest = (i * stride) % size
        # i = dest * inv % size
        inv = 35  # Da tim thay 35
        i = (dest * inv) % size
        encrypted[dest] = new_zip[i] ^ key[dest % key_len]
    
    print(f"Encrypted: {encrypted[:32].hex()}")
    print(f"Original: {original_encrypted[:32].hex()}")
    print(f"Match: {bytes(encrypted) == original_encrypted}")
    
    # Thu 8: Nhu 7 nhung XOR voi key cua i
    print("\n[Thu 8] Nhu 7 nhung XOR voi key cua i:")
    encrypted = bytearray(size)
    for dest in range(size):
        inv = 35
        i = (dest * inv) % size
        encrypted[dest] = new_zip[i] ^ key[i % key_len]
    
    print(f"Encrypted: {encrypted[:32].hex()}")
    print(f"Original: {original_encrypted[:32].hex()}")
    print(f"Match: {bytes(encrypted) == original_encrypted}")
    
    # Thu 9: Thu voi byte order khac
    print("\n[Thu 9] Thu voi key nguoc:")
    encrypted = bytearray(size)
    for dest in range(size):
        inv = 35
        i = (dest * inv) % size
        # Key theo thu tu nguoc
        encrypted[dest] = new_zip[i] ^ key[(key_len - 1 - (dest % key_len)) % key_len]
    
    print(f"Encrypted: {encrypted[:32].hex()}")
    print(f"Original: {original_encrypted[:32].hex()}")
    print(f"Match: {bytes(encrypted) == original_encrypted}")
    
    # Thu 10: So sanh byte by byte
    print("\n[So sanh chi tiet byte 0-31]:")
    for i in range(32):
        if encrypted[i] != original_encrypted[i]:
            print(f"  Byte {i}: encrypted={encrypted[i]:02x}, original={original_encrypted[i]:02x}, diff={encrypted[i]^original_encrypted[i]:02x}")


if __name__ == "__main__":
    main()
