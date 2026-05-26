# -*- coding: utf-8 -*-
"""
Phan tich ZIP goc
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


def tao_zip_deflate(data, name):
    """Tao ZIP voi DEFLATE compression (nhu ZIP goc)."""
    pwd = f"cocos2d: ERROR: Invalid filename {name}".encode('utf-8')
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("data", data)
    return zip_buffer.getvalue()


def tao_zip_exact(data, name, target_size):
    """Tao ZIP voi kich thuoc chinh xac bang cach thu cac muc compression."""
    pwd = f"cocos2d: ERROR: Invalid filename {name}".encode('utf-8')
    
    # Thu voi cac muc compression khac nhau
    for compress_level in range(9):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', compresslevel=compress_level) as zf:
            zf.writestr("data", data)
        result = zip_buffer.getvalue()
        if len(result) == target_size:
            print(f"  Tim thay khop voi compress_level={compress_level}")
            return result
    
    # Neu khong khop, tra ve ZIP_STORED
    return tao_zip_stored(data, name)


def main():
    print("PHAN TICH ZIP GOC")
    print("=" * 60)
    
    # Doc file goc
    with open(ABC_FILE, "rb") as f:
        original_encrypted = f.read()
    print(f"Original encrypted: {len(original_encrypted)} bytes")
    
    # Giai ma
    zip_data = descramble_abc(original_encrypted, FILE_NAME)
    print(f"ZIP data: {len(zip_data)} bytes")
    
    # Phan tich ZIP
    print("\nPhan tich ZIP header:")
    sig = zip_data[:4]
    is_valid = sig == b'PK\x03\x04'
    print(f"  Signature: {sig.hex()} (valid={is_valid})")
    
    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        info = zf.infolist()[0]
        print(f"  Filename: {info.filename}")
        print(f"  Compress type: {info.compress_type}")
        print(f"  Compress size: {info.compress_size}")
        print(f"  File size: {info.file_size}")
        print(f"  CRC32: {info.CRC}")
    
    # Doc Lua
    pwd = f"cocos2d: ERROR: Invalid filename {FILE_NAME}".encode('utf-8')
    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        luac_data = zf.read("data", pwd=pwd)
    print(f"\nLua bytecode: {len(luac_data)} bytes")
    
    # Tao ZIP giong nhu ZIP goc
    print("\nTao ZIP moi voi DEFLATE:")
    new_zip_deflate = tao_zip_deflate(luac_data, FILE_NAME)
    print(f"  ZIP_DEFLATE: {len(new_zip_deflate)} bytes")
    
    # So sanh
    print(f"\nSo sanh:")
    print(f"  ZIP goc: {len(zip_data)} bytes")
    print(f"  ZIP moi (DEFLATE): {len(new_zip_deflate)} bytes")
    print(f"  Giong nhau: {zip_data == new_zip_deflate}")
    
    if zip_data != new_zip_deflate:
        print(f"\n  Can tao ZIP chinh xac {len(zip_data)} bytes")
        exact_zip = tao_zip_exact(luac_data, FILE_NAME, len(zip_data))
        print(f"  ZIP exact: {len(exact_zip)} bytes")
        print(f"  Giong nhau: {zip_data == exact_zip}")


if __name__ == "__main__":
    main()
