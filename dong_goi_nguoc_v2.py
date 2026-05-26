# -*- coding: utf-8 -*-
"""
Dong goi nguoc voi thuat toan dung
Y tuong: Doc ZIP tu file goc, sua IP, tao ZIP moi, scramble
"""
import os
import sys
import zipfile
import io

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# === CONFIG ===
FILE_NAME = "ipconfig"
ABC_FILE = r"d:\FileD\dota\ios\dgame.app\data\bot\ipconfig.abc"
IP_CU = "192.168.1.179"
IP_MOI = "192.168.2.2"
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
    """Ma hoa nguoc - thu tu giong nhu descramble nhung nguoc lai."""
    size = len(data)
    key = f"{name}.abc".encode('utf-8')
    key_len = len(key)
    
    # Scramble nhu da xac dinh: encrypted[dest] = data[i] XOR key[i]
    encrypted = bytearray(size)
    for i in range(size):
        dest = (i * 10007) % size
        encrypted[dest] = data[i] ^ key[i % key_len]
    
    return bytes(encrypted)


def tao_zip_deflate(data, name):
    """Tao ZIP voi DEFLATE."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("data", data)
    return zip_buffer.getvalue()


def thay_doi_ip_trong_zip(zip_data, ip_cu, ip_moi):
    """
    Thay doi IP trong ZIP da nen.
    Tra ve ZIP moi neu thanh cong, None neu that bai.
    """
    pwd = f"cocos2d: ERROR: Invalid filename {FILE_NAME}".encode('utf-8')
    
    try:
        # Doc Lua bytecode tu ZIP
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            luac_data = zf.read("data", pwd=pwd)
        
        print(f"  Doc Lua bytecode: {len(luac_data)} bytes")
        
        # Thay doi IP trong bytecode
        ip_cu_bytes = ip_cu.encode('utf-8')
        ip_moi_bytes = ip_moi.encode('utf-8')
        
        if len(ip_cu) != len(ip_moi):
            # Pad IP moi voi null byte
            ip_moi_padded = ip_moi + "\x00" * (len(ip_cu) - len(ip_moi))
            ip_moi_bytes = ip_moi_padded.encode('utf-8')
            print(f"  IP moi da pad: '{ip_moi_padded}'")
        
        # Kiem tra IP cu co ton tai
        if ip_cu_bytes not in luac_data:
            print(f"  Loi: Khong tim thay IP cu '{ip_cu}' trong bytecode!")
            return None
        
        # Thay the
        luac_moi = luac_data.replace(ip_cu_bytes, ip_moi_bytes)
        print(f"  Da thay doi IP thanh cong!")
        
        # Tao ZIP moi
        zip_moi = tao_zip_deflate(luac_moi, FILE_NAME)
        print(f"  Tao ZIP moi: {len(zip_moi)} bytes")
        
        return zip_moi
        
    except Exception as e:
        print(f"  Loi: {e}")
        return None


def main():
    print("DONG GOI NGUOC .LUA -> .ABC")
    print("=" * 60)
    
    print(f"\n[Cau hinh]")
    print(f"  File: {ABC_FILE}")
    print(f"  IP cu: {IP_CU}")
    print(f"  IP moi: {IP_MOI}")
    
    # Buoc 1: Doc file goc
    print(f"\n[1] Doc file .abc goc...")
    with open(ABC_FILE, "rb") as f:
        abc_data = f.read()
    print(f"  Kich thuoc: {len(abc_data)} bytes")
    
    # Buoc 2: Giai ma
    print(f"\n[2] Giai ma scramble...")
    zip_data = descramble_abc(abc_data, FILE_NAME)
    print(f"  ZIP data: {len(zip_data)} bytes")
    
    if zip_data[:4] != b'PK\x03\x04':
        print(f"  Loi: Khong phai ZIP!")
        return
    
    # Phan tich ZIP
    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        info = zf.infolist()[0]
        print(f"  Compress type: {info.compress_type}")
        print(f"  File size: {info.file_size}")
    
    # Buoc 3: Thay doi IP
    print(f"\n[3] Thay doi IP trong ZIP...")
    zip_moi = thay_doi_ip_trong_zip(zip_data, IP_CU, IP_MOI)
    if zip_moi is None:
        print("That bai!")
        return
    
    # Buoc 4: Scramble
    print(f"\n[4] Scramble thanh .abc...")
    abc_moi = scramble_abc(zip_moi, FILE_NAME)
    print(f"  Scrambled: {len(abc_moi)} bytes")
    
    # Buoc 5: Luu
    print(f"\n[5] Luu file moi...")
    with open(ABC_FILE, "wb") as f:
        f.write(abc_moi)
    print(f"  Da luu: {ABC_FILE}")
    
    # Buoc 6: Xac minh
    print(f"\n[6] Xac minh (giai ma lai)...")
    test_zip = descramble_abc(abc_moi, FILE_NAME)
    if test_zip[:4] == b'PK\x03\x04':
        print("  [OK] File hop le!")
        
        # Kiem tra IP
        pwd = f"cocos2d: ERROR: Invalid filename {FILE_NAME}".encode('utf-8')
        with zipfile.ZipFile(io.BytesIO(test_zip)) as zf:
            test_lua = zf.read("data", pwd=pwd)
        
        if IP_MOI.encode('utf-8')[:len(IP_MOI)] in test_lua:
            print(f"  [OK] IP moi '{IP_MOI}' da co mat trong file!")
        else:
            print(f"  [CANH BAO] IP moi khong tim thay!")
    else:
        print("  [LOI] File khong hop le!")
    
    print("\n" + "=" * 60)
    print("HOAN TAT!")


if __name__ == "__main__":
    main()
