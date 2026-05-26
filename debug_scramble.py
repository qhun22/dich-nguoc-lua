# -*- coding: utf-8 -*-
"""
Debug: Tim thuat toan scramble dung bang cach doc file goc
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
BACKUP_FILE = r"d:\FileD\dota\ios\dgame.app\data\bot\ipconfig.abc.backup"
# =================

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
    """Tao ZIP archive."""
    pwd = f"cocos2d: ERROR: Invalid filename {name}".encode('utf-8')
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("data", data, compress_type=zipfile.ZIP_STORED)
    return zip_buffer.getvalue()


def test_scramble(luac_data):
    """Thu tất ca cach scramble có the."""
    size = len(luac_data)
    key = f"{FILE_NAME}.abc".encode('utf-8')
    key_len = len(key)
    stride = 10007
    
    print(f"\nLua bytecode size: {size} bytes")
    print(f"Key: {key}")
    
    # Tao ZIP
    zip_data = tao_zip(luac_data, FILE_NAME)
    print(f"ZIP size: {len(zip_data)} bytes")
    
    results = []
    
    # Thu 1: Scramble thuan (vong lap i tinh dest)
    print("\n[Thu 1] encrypted[i] = data[(i * stride) % size] XOR key[i]")
    try:
        encrypted = bytearray(size)
        for i in range(size):
            src = (i * stride) % size
            encrypted[i] = zip_data[src] ^ key[i % key_len]
        
        decrypted = descramble_abc(bytes(encrypted), FILE_NAME)
        match = decrypted == zip_data
        print(f"  Result: {'DUNG' if match else 'SAI'}")
        if not match:
            print(f"    Decrypted: {decrypted[:20].hex()}")
            print(f"    Expected:  {zip_data[:20].hex()}")
        results.append(("Thu 1", match))
    except Exception as e:
        print(f"  Loi: {e}")
        results.append(("Thu 1", False))
    
    # Thu 2: Scramble nguoc
    print("\n[Thu 2] encrypted[(i * stride) % size] = data[i] XOR key[i]")
    try:
        encrypted = bytearray(size)
        for i in range(size):
            dest = (i * stride) % size
            encrypted[dest] = zip_data[i] ^ key[i % key_len]
        
        decrypted = descramble_abc(bytes(encrypted), FILE_NAME)
        match = decrypted == zip_data
        print(f"  Result: {'DUNG' if match else 'SAI'}")
        if not match:
            print(f"    Decrypted: {decrypted[:20].hex()}")
            print(f"    Expected:  {zip_data[:20].hex()}")
        results.append(("Thu 2", match))
    except Exception as e:
        print(f"  Loi: {e}")
        results.append(("Thu 2", False))
    
    # Thu 3: Nhu thuan nhung dau vao lai thu tu
    print("\n[Thu 3] encrypted[i] = data[i] XOR key[i], dest = pos % size")
    try:
        encrypted = bytearray(size)
        pos = 0
        for i in range(size):
            dest = pos % size
            encrypted[dest] = zip_data[i] ^ key[i % key_len]
            pos += stride
        
        decrypted = descramble_abc(bytes(encrypted), FILE_NAME)
        match = decrypted == zip_data
        print(f"  Result: {'DUNG' if match else 'SAI'}")
        if not match:
            print(f"    Decrypted: {decrypted[:20].hex()}")
            print(f"    Expected:  {zip_data[:20].hex()}")
        results.append(("Thu 3", match))
    except Exception as e:
        print(f"  Loi: {e}")
        results.append(("Thu 3", False))
    
    # Thu 4: Nhu giai ma nhung nguoc lai
    print("\n[Thu 4] encrypted[dest] = data[i] XOR key[src], dest=pos%size, i tim src")
    try:
        # Tim permutation nguoc
        # dest = (i * stride) % size
        # i = (dest * inv) % size
        
        # Tim modular inverse
        inv = None
        for x in range(1, size):
            if (stride * x) % size == 1:
                inv = x
                break
        
        if inv is None:
            print("  Khong tim duoc modular inverse")
            results.append(("Thu 4", False))
        else:
            print(f"  Modular inverse cua {stride} mod {size} la {inv}")
            
            encrypted = bytearray(size)
            pos = 0
            for i in range(size):
                dest = pos % size
                src = (dest * inv) % size
                encrypted[dest] = zip_data[src] ^ key[dest % key_len]
                pos += stride
            
            decrypted = descramble_abc(bytes(encrypted), FILE_NAME)
            match = decrypted == zip_data
            print(f"  Result: {'DUNG' if match else 'SAI'}")
            if not match:
                print(f"    Decrypted: {decrypted[:20].hex()}")
                print(f"    Expected:  {zip_data[:20].hex()}")
            results.append(("Thu 4", match))
    except Exception as e:
        print(f"  Loi: {e}")
        results.append(("Thu 4", False))
    
    return results


def main():
    print("DEBUG: Tim thuat toan scramble")
    print("=" * 60)
    
    # Khoi phuc file goc
    print("\n[1] Khoi phuc file goc...")
    if os.path.exists(BACKUP_FILE):
        with open(ABC_FILE, "rb") as f:
            current = f.read()
        with open(BACKUP_FILE, "rb") as f:
            backup = f.read()
        
        if current != backup:
            print("  Phat hien file da biet thay doi!")
            print(f"  Hien tai: {len(current)} bytes")
            print(f"  Backup: {len(backup)} bytes")
            
            with open(ABC_FILE, "wb") as f:
                f.write(backup)
            print("  Da khoi phuc tu backup!")
    else:
        print("  Khong co backup. Thu giai ma file hien tai...")
    
    # Doc file
    print("\n[2] Doc file .abc...")
    if not os.path.exists(ABC_FILE):
        print(f"  Loi: File khong ton tai!")
        return
    
    with open(ABC_FILE, "rb") as f:
        abc_data = f.read()
    print(f"  Kich thuoc: {len(abc_data)} bytes")
    
    # Giai ma
    print("\n[3] Giai ma...")
    zip_data = descramble_abc(abc_data, FILE_NAME)
    
    if zip_data[:4] == b'PK\x03\x04':
        print("  [OK] Day la ZIP!")
    else:
        print(f"  [LOI] Khong phai ZIP!")
        print(f"  Header: {zip_data[:20].hex()}")
        return
    
    # Doc Lua
    pwd = f"cocos2d: ERROR: Invalid filename {FILE_NAME}".encode('utf-8')
    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        luac_data = zf.read("data", pwd=pwd)
    print(f"  Lua bytecode: {len(luac_data)} bytes")
    
    # Thu scramble
    print("\n[4] Thu cac phuong phap scramble...")
    results = test_scramble(luac_data)
    
    # Ket luan
    print("\n" + "=" * 60)
    print("KET LUAN:")
    for name, match in results:
        print(f"  {name}: {'DUNG' if match else 'SAI'}")


if __name__ == "__main__":
    main()
