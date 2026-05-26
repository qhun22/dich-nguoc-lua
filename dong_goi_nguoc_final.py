# -*- coding: utf-8 -*-
"""
Dong goi nguoc .luac -> .abc
Su dung thuat toan scramble da duoc xac dinh:
  encrypted[i] = decrypted[dest] XOR key[i % key_len]
  dest = (i * 10007) % size
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
LUAC_FILE = r"d:\FileD\dota\ios\dgame.app\data\bot\ipconfig.luac"
ABC_FILE = r"d:\FileD\dota\ios\dgame.app\data\bot\ipconfig.abc"
# =================


def scramble_abc(data, name):
    """
    Ma hoa scramble.
    Thuật toan:
      encrypted[i] = data[dest] XOR key[i % key_len]
      dest = (i * 10007) % size
    """
    size = len(data)
    key = f"{name}.abc".encode('utf-8')
    key_len = len(key)
    stride = 10007
    
    encrypted = bytearray(size)
    for i in range(size):
        dest = (i * stride) % size
        encrypted[i] = data[dest] ^ key[i % key_len]
    
    return bytes(encrypted)


def tao_zip_deflate(data, name):
    """Tao ZIP voi DEFLATE compression."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("data", data)
    return zip_buffer.getvalue()


def main():
    print("DONG GOI .LUA -> .ABC")
    print("=" * 60)
    
    print(f"\n[Cau hinh]")
    print(f"  File Lua: {LUAC_FILE}")
    print(f"  File ABC: {ABC_FILE}")
    
    # Buoc 1: Doc Lua bytecode
    print(f"\n[1] Doc file Lua bytecode...")
    if not os.path.exists(LUAC_FILE):
        print(f"  Loi: File khong ton tai!")
        return
    
    with open(LUAC_FILE, "rb") as f:
        lua_data = f.read()
    print(f"  Kich thuoc: {len(lua_data)} bytes")
    
    # Buoc 2: Tao ZIP
    print(f"\n[2] Tao ZIP voi DEFLATE...")
    zip_data = tao_zip_deflate(lua_data, FILE_NAME)
    print(f"  ZIP kich thuoc: {len(zip_data)} bytes")
    
    # Buoc 3: Scramble
    print(f"\n[3] Scramble thanh .abc...")
    abc_data = scramble_abc(zip_data, FILE_NAME)
    print(f"  Scrambled: {len(abc_data)} bytes")
    
    # Buoc 4: Luu
    print(f"\n[4] Luu file...")
    with open(ABC_FILE, "wb") as f:
        f.write(abc_data)
    print(f"  Da luu: {ABC_FILE}")
    
    # Buoc 5: Xac minh
    print(f"\n[5] Xac minh...")
    # Doc lai va kiem tra
    with open(ABC_FILE, "rb") as f:
        test_data = f.read()
    
    # Scramble lai de kiem tra
    test_zip = scramble_abc(test_data, FILE_NAME)
    test_zip_zip = io.BytesIO(test_zip)
    
    try:
        with zipfile.ZipFile(test_zip_zip) as zf:
            info = zf.infolist()[0]
            print(f"  [OK] ZIP hop le!")
            print(f"      Filename: {info.filename}")
            print(f"      Compressed: {info.compress_size} bytes")
            print(f"      Uncompressed: {info.file_size} bytes")
    except Exception as e:
        print(f"  [LOI] ZIP khong hop le: {e}")
    
    print("\n" + "=" * 60)
    print("HOAN TAT!")
    print(f"File da duoc dong goi: {ABC_FILE}")


if __name__ == "__main__":
    main()
