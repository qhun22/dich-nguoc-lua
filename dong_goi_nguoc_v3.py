# -*- coding: utf-8 -*-
"""
Dong goi .luac -> .abc
Thu cac phuong phap nen khac nhau de tao ZIP cung kich thuoc voi file goc
"""
import os
import sys
import zipfile
import io
import struct

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# === CONFIG ===
FILE_NAME = "ipconfig"
LUAC_FILE = r"d:\FileD\dota\ios\dgame.app\data\bot\ipconfig.luac"
ABC_FILE = r"d:\FileD\dota\ios\dgame.app\data\bot\ipconfig.abc"
ORIGINAL_ABC = r"d:\FileD\dota\apk\base\assets\data\bot\ipconfig.abc"  # File goc de lay kich thuoc
# =================

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


def scramble_abc(data, name):
    """Ma hoa scramble."""
    size = len(data)
    key = f"{name}.abc".encode('utf-8')
    key_len = len(key)
    stride = 10007
    
    encrypted = bytearray(size)
    for i in range(size):
        dest = (i * stride) % size
        encrypted[i] = data[dest] ^ key[i % key_len]
    
    return bytes(encrypted)


def tao_zip_stored(data, name):
    """Tao ZIP khong nen (STORE)."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_STORED) as zf:
        zf.writestr("data", data)
    return zip_buffer.getvalue()


def tao_zip_deflate(data, name, compresslevel=6):
    """Tao ZIP voi DEFLATE."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', compresslevel=compresslevel) as zf:
        zf.writestr("data", data)
    return zip_buffer.getvalue()


def doc_ip_tu_luac(lua_data, ip_cu, ip_moi):
    """Doc IP tu Lua bytecode, tra ve data da thay doi."""
    ip_cu_bytes = ip_cu.encode('utf-8')
    ip_moi_bytes = ip_moi.encode('utf-8')
    
    if len(ip_cu) != len(ip_moi):
        ip_moi_padded = ip_moi + "\x00" * (len(ip_cu) - len(ip_moi))
        ip_moi_bytes = ip_moi_padded.encode('utf-8')
    
    if ip_cu_bytes not in lua_data:
        print(f"  Loi: Khong tim thay IP '{ip_cu}'!")
        return None
    
    return lua_data.replace(ip_cu_bytes, ip_moi_bytes)


def tao_zip_custom(data, name, target_size):
    """
    Thu tao ZIP voi kich thuoc chinh xac.
    """
    import zlib
    import struct
    
    pwd = f"cocos2d: ERROR: Invalid filename {name}".encode('utf-8')
    
    # Nen DEFLATE
    compressed = zlib.compress(data, 6)[2:-4]  # Bo header va trailer cua zlib
    
    # Tao ZIP local file header
    filename = b"data"
    crc = zlib.crc32(data) & 0xffffffff
    
    header = struct.pack('<4sHHHHHIIIHH',
        b'PK\x03\x04',  # signature
        20,             # version needed
        0,              # general purpose bit flag
        8,              # compression method (DEFLATE)
        0,              # last mod file time
        0,              # last mod file date
        crc,
        len(compressed), # compressed size
        len(data),       # uncompressed size
        len(filename),   # filename length
        0               # extra field length
    )
    
    result = header + filename + compressed
    
    if len(result) == target_size:
        return result
    
    # Thu cac phuong phap khac
    print(f"\n  ZIP chua khop ({len(result)} vs {target_size}), thu phuong phap khac...")
    
    # Phuong phap 1: Them bytes vao extra field
    if len(result) < target_size:
        extra_size = target_size - len(result)
        header_modified = struct.pack('<4sHHHHHIIIHH',
            b'PK\x03\x04', 20, 0, 8, 0, 0, crc,
            len(compressed), len(data), len(filename), extra_size
        )
        extra = b'\x00' * extra_size  # Null padding
        result = header_modified + filename + compressed + extra
        print(f"  Phuong phap 1 (padding): {len(result)} bytes")
    
    return result


def main():
    print("DONG GOI .LUA -> .ABC")
    print("=" * 60)
    
    # Doc file goc de lay kich thuoc
    with open(ORIGINAL_ABC, "rb") as f:
        original_abc = f.read()
    target_size = len(original_abc)
    print(f"Kich thuoc muc tieu: {target_size} bytes")
    
    # Doc Lua bytecode
    print(f"\n[1] Doc Lua bytecode...")
    with open(LUAC_FILE, "rb") as f:
        lua_data = f.read()
    print(f"  Kich thuoc: {len(lua_data)} bytes")
    
    # Thay doi IP
    IP_CU = "192.168.1.179"
    IP_MOI = "192.168.2.2"
    print(f"\n[2] Thay doi IP: {IP_CU} -> {IP_MOI}")
    
    lua_moi = doc_ip_tu_luac(lua_data, IP_CU, IP_MOI)
    if lua_moi is None:
        return
    print(f"  Da thay doi thanh cong!")
    
    # Tao ZIP
    print(f"\n[3] Tao ZIP...")
    
    # Thu tao ZIP chinh xac
    zip_exact = tao_zip_custom(lua_moi, FILE_NAME, target_size)
    print(f"  ZIP chinh xac: {len(zip_exact)} bytes")
    
    # Scramble
    print(f"\n[4] Scramble...")
    abc_data = scramble_abc(zip_exact, FILE_NAME)
    print(f"  Scrambled: {len(abc_data)} bytes")
    
    # Luu
    print(f"\n[5] Luu...")
    with open(ABC_FILE, "wb") as f:
        f.write(abc_data)
    print(f"  Da luu: {ABC_FILE}")
    
    # Xac minh
    print(f"\n[6] Xac minh...")
    test_abc = descramble_abc(abc_data, FILE_NAME)
    
    if test_abc[:4] == b'PK\x03\x04':
        print("  [OK] ZIP hop le!")
        
        # Kiem tra IP
        if IP_MOI.encode('utf-8')[:len(IP_MOI)] in test_abc:
            print(f"  [OK] IP moi '{IP_MOI}' co mat trong file!")
        else:
            print("  [CANH BAO] Khong tim thay IP moi!")
    else:
        print("  [LOI] ZIP khong hop le!")
        print(f"  Header: {test_abc[:20].hex()}")
    
    print("\n" + "=" * 60)
    print("HOAN TAT!")


if __name__ == "__main__":
    main()
