# -*- coding: utf-8 -*-
"""
Quet tat ca file .abc trong thu muc data/ de patch IP va version.
"""
import os
import sys
import glob
import zipfile
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# === CAU HINH ===
IP_CU = "192.168.1.179"
IP_MOI = "192.168.2.111"
VERSION_CU = "9.9.0"
VERSION_MOI = "1.0.0103"

DATA_DIR = r"d:\FileD\dota\ios\dgame.app\data"
# =================


def descramble_abc(data, name):
    """
    Giai ma Stride-10007 Permutation + XOR.
    Thu tu:
      pos = 0
      for i in range(size):
        dest = pos % size
        buffer[dest] = encrypted[i] ^ key[i % key_len]
        pos += 10007
    """
    size = len(data)
    key = f"{name}.abc".encode('utf-8')
    key_len = len(key)
    
    buffer = bytearray(size)
    pos = 0
    for i in range(size):
        dest = pos % size
        buffer[dest] = data[i] ^ key[i % key_len]
        pos += 10007
    
    return bytes(buffer)


def scramble_abc(data, name):
    """
    Ma hoa Stride-10007 Permutation + XOR (ham nguoc cua descramble).
    """
    size = len(data)
    key = f"{name}.abc".encode('utf-8')
    key_len = len(key)
    
    stride = 10007
    
    # Tim modular inverse cua stride
    inverse_stride = None
    for x in range(1, size):
        if (stride * x) % size == 1:
            inverse_stride = x
            break
    
    if inverse_stride is None:
        # Khong co inverse, su dung brute force
        encrypted = bytearray(size)
        for i in range(size):
            dest = (i * stride) % size
            encrypted[i] = data[dest] ^ key[i % key_len]
        return bytes(encrypted)
    
    # Su dung inverse de scramble
    result = bytearray(size)
    for dest in range(size):
        i = (dest * inverse_stride) % size
        result[i] = data[dest] ^ key[dest % key_len]
    
    return bytes(result)


def giai_ma_zip(data, name):
    """Giai ma file .abc -> giai nen ZIP -> tra ve noi dung."""
    try:
        # Descramble
        zip_data = descramble_abc(data, name)
        
        # Kiem tra ZIP signature
        if zip_data[:4] != b'PK\x03\x04':
            return None, "Loi: Khong phai ZIP"
        
        # Password cho ZIP
        pwd = f"cocos2d: ERROR: Invalid filename {name}".encode('utf-8')
        
        # Giai nen ZIP voi password
        try:
            zf = zipfile.ZipFile(io.BytesIO(zip_data), 'r')
            zf.setpassword(pwd)
            
            # Doc tat ca entries
            for entry_name in zf.namelist():
                try:
                    lua_data = zf.read(entry_name, pwd=pwd)
                    zf.close()
                    return lua_data, None
                except RuntimeError as e:
                    if "password" in str(e).lower():
                        continue
                    raise
                except:
                    continue
            
            zf.close()
            return None, "Loi: Khong doc duoc entry (sai password?)"
            
        except Exception as e:
            if "password" in str(e).lower():
                return None, f"File bi mat khau: {e}"
            return None, f"Loi giai nen: {e}"
            
    except Exception as e:
        return None, f"Loi giai ma: {e}"


def tao_zip(data, name):
    """Tao ZIP voi password dong."""
    pwd = f"cocos2d: ERROR: Invalid filename {name}".encode('utf-8')
    
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("data", data, compress_type=zipfile.ZIP_STORED)
    
    return zip_buffer.getvalue()


def patch_lua_data(lua_data, ip_cu, ip_moi, version_cu, version_moi):
    """Patch IP va version trong Lua bytecode."""
    data = bytearray(lua_data)
    
    changes = []
    
    # Patch IP
    ip_cu_bytes = ip_cu.encode('utf-8')
    ip_moi_bytes = ip_moi.encode('utf-8')
    
    # Pad IP moi neu can
    if len(ip_cu) > len(ip_moi):
        ip_moi_padded = ip_moi + "\x00" * (len(ip_cu) - len(ip_moi))
        ip_moi_bytes = ip_moi_padded.encode('utf-8')
    else:
        ip_moi_bytes = ip_moi.encode('utf-8')
    
    # Tim va thay the IP
    count_ip = data.count(ip_cu_bytes)
    if count_ip > 0:
        data = data.replace(ip_cu_bytes, ip_moi_bytes)
        changes.append(f"IP: {count_ip} vi tri '{ip_cu}' -> '{ip_moi}'")
    
    # Patch version
    version_cu_bytes = version_cu.encode('utf-8')
    version_moi_bytes = version_moi.encode('utf-8')
    
    # Pad version moi neu can
    if len(version_cu) > len(version_moi):
        version_moi_padded = version_moi + "\x00" * (len(version_cu) - len(version_moi))
        version_moi_bytes = version_moi_padded.encode('utf-8')
    else:
        version_moi_bytes = version_moi.encode('utf-8')
    
    count_ver = data.count(version_cu_bytes)
    if count_ver > 0:
        data = data.replace(version_cu_bytes, version_moi_bytes)
        changes.append(f"Version: {count_ver} vi tri '{version_cu}' -> '{version_moi}'")
    
    return bytes(data), changes


def dong_goi_abc(lua_data, name, target_size):
    """Dong goi .abc voi dung luong chinh xac."""
    # Tao ZIP
    zip_data = tao_zip(lua_data, name)
    
    # Scramble
    encrypted = scramble_abc(zip_data, name)
    
    # Neu nho hon target, pad voi null
    if len(encrypted) < target_size:
        encrypted = encrypted + b'\x00' * (target_size - len(encrypted))
    # Neu lon hon, cat bo
    elif len(encrypted) > target_size:
        encrypted = encrypted[:target_size]
    
    return encrypted


def xu_ly_file_abc(file_path):
    """Xu ly mot file .abc."""
    name = os.path.splitext(os.path.basename(file_path))[0]
    
    print(f"\n{'='*60}")
    print(f"Xu ly: {file_path}")
    print(f"{'='*60}")
    
    # Doc file
    try:
        with open(file_path, 'rb') as f:
            abc_data = f.read()
    except Exception as e:
        print(f"  [LOI] Khong doc duoc file: {e}")
        return False, "Khong doc duoc file"
    
    original_size = len(abc_data)
    print(f"  Kich thuoc goc: {original_size} bytes")
    
    # Giai ma
    lua_data, error = giai_ma_zip(abc_data, name)
    if error:
        print(f"  [BO QUA] {error}")
        return False, error
    
    print(f"  [OK] Giai ma thanh cong")
    
    # Kiem tra noi dung
    content = lua_data.decode('utf-8', errors='replace')
    
    has_old_ip = IP_CU in content
    has_old_version = VERSION_CU in content
    
    print(f"  Chuoi cu: IP={has_old_ip}, Version={has_old_version}")
    
    if not (has_old_ip or has_old_version):
        print(f"  [BO QUA] Khong co noi dung can patch")
        return False, "Khong co noi dung can patch"
    
    # Patch
    lua_patched, changes = patch_lua_data(lua_data, IP_CU, IP_MOI, VERSION_CU, VERSION_MOI)
    
    print(f"  Da patch: {', '.join(changes)}")
    
    # Dong goi
    abc_patched = dong_goi_abc(lua_patched, name, original_size)
    
    # Luu
    try:
        with open(file_path, 'wb') as f:
            f.write(abc_patched)
        print(f"  [OK] Da luu ({len(abc_patched)} bytes)")
        return True, changes
    except Exception as e:
        print(f"  [LOI] Khong luu duoc: {e}")
        return False, str(e)


def main():
    print("=" * 70)
    print("QUET VA PATCH TOAN BO FILE .abc TRONG THU MUC DATA")
    print("=" * 70)
    
    print(f"\n[CAU HINH]")
    print(f"  Thu muc: {DATA_DIR}")
    print(f"  IP cu: {IP_CU} -> IP moi: {IP_MOI}")
    print(f"  Version cu: {VERSION_CU} -> Version moi: {VERSION_MOI}")
    
    # Tim tat ca file .abc
    pattern = os.path.join(DATA_DIR, "**", "*.abc")
    abc_files = glob.glob(pattern, recursive=True)
    
    print(f"\nTim thay {len(abc_files)} file .abc:")
    for f in abc_files:
        print(f"  - {f}")
    
    # Xu ly tung file
    print(f"\n{'='*70}")
    print("BAT DAU XU LY...")
    print(f"{'='*70}")
    
    ket_qua = []
    thanh_cong = 0
    
    for file_path in abc_files:
        ok, msg = xu_ly_file_abc(file_path)
        ket_qua.append((file_path, ok, msg))
        if ok:
            thanh_cong += 1
    
    # Tom tat
    print(f"\n{'='*70}")
    print("TOM TAT KET QUA")
    print(f"{'='*70}")
    print(f"Tong so file: {len(abc_files)}")
    print(f"Thanh cong: {thanh_cong}")
    print(f"That bai: {len(abc_files) - thanh_cong}")
    
    print(f"\n[DANH SACH FILE DA PATCH]")
    for file_path, ok, msg in ket_qua:
        if ok:
            print(f"  [OK] {file_path}")
            for m in msg:
                print(f"       - {m}")
        else:
            print(f"  [--] {file_path} ({msg})")


if __name__ == "__main__":
    main()
