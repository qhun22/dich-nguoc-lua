# -*- coding: utf-8 -*-
"""
Quet va patch cac file .abc trong 5 thu muc chi dinh.
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

# 5 thu muc chi dinh
TARGET_DIRS = [
    r"d:\FileD\dota\ios\Payload\dgame.app\data\network",
    r"d:\FileD\dota\ios\Payload\dgame.app\data\genericnetwork",
    r"d:\FileD\dota\ios\Payload\dgame.app\data\sdk",
    r"d:\FileD\dota\ios\Payload\dgame.app\data\extversion",
    r"d:\FileD\dota\ios\Payload\dgame.app\data\socket",
]
# =================


def descramble_abc(data, name):
    """Giai ma Stride-10007 Permutation + XOR."""
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
    """Ma hoa Stride-10007 Permutation + XOR (ham nguoc cua descramble)."""
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
        encrypted = bytearray(size)
        for i in range(size):
            dest = (i * stride) % size
            encrypted[i] = data[dest] ^ key[i % key_len]
        return bytes(encrypted)
    
    result = bytearray(size)
    for dest in range(size):
        i = (dest * inverse_stride) % size
        result[i] = data[dest] ^ key[dest % key_len]
    
    return bytes(result)


def giai_ma_zip(data, name):
    """Giai ma file .abc -> giai nen ZIP -> tra ve noi dung."""
    try:
        zip_data = descramble_abc(data, name)
        
        if zip_data[:4] != b'PK\x03\x04':
            return None, "Loi: Khong phai ZIP"
        
        pwd = f"cocos2d: ERROR: Invalid filename {name}".encode('utf-8')
        
        try:
            zf = zipfile.ZipFile(io.BytesIO(zip_data), 'r')
            zf.setpassword(pwd)
            
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
            return None, "Loi: Khong doc duoc entry"
            
        except Exception as e:
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


def dong_goi_abc(lua_data, name, target_size):
    """Dong goi .abc voi kich thuoc chinh xac bang cach noi byte rac vao comment."""
    # Tao ZIP
    zip_data = tao_zip(lua_data, name)
    
    # Scramble
    encrypted = scramble_abc(zip_data, name)
    
    original_len = len(encrypted)
    
    # Pad null bytes neu can
    if len(encrypted) < target_size:
        encrypted = encrypted + b'\x00' * (target_size - len(encrypted))
    elif len(encrypted) > target_size:
        encrypted = encrypted[:target_size]
    
    return encrypted


def xu_ly_file_abc(file_path):
    """Xu ly mot file .abc."""
    name = os.path.splitext(os.path.basename(file_path))[0]
    
    print(f"\nXu ly: {file_path}")
    
    try:
        with open(file_path, 'rb') as f:
            abc_data = f.read()
    except Exception as e:
        print(f"  [LOI] Khong doc duoc: {e}")
        return False, "Loi doc file"
    
    original_size = len(abc_data)
    
    # Giai ma
    lua_data, error = giai_ma_zip(abc_data, name)
    if error:
        print(f"  [BO QUA] {error}")
        return False, error
    
    # Kiem tra noi dung
    content = lua_data.decode('utf-8', errors='replace')
    
    has_old_ip = IP_CU in content
    has_old_version = VERSION_CU in content
    
    if not (has_old_ip or has_old_version):
        print(f"  [BO QUA] Khong co noi dung can patch")
        return False, "Khong co noi dung can patch"
    
    # Patch
    data = bytearray(lua_data)
    changes = []
    
    # Patch IP
    ip_cu_bytes = IP_CU.encode('utf-8')
    if IP_CU in content:
        # Pad neu can
        if len(IP_CU) > len(IP_MOI):
            ip_moi_padded = IP_MOI + "\x00" * (len(IP_CU) - len(IP_MOI))
        else:
            ip_moi_padded = IP_MOI
        data = data.replace(ip_cu_bytes, ip_moi_padded.encode('utf-8'))
        changes.append(f"IP: '{IP_CU}' -> '{IP_MOI}'")
    
    # Patch version
    version_cu_bytes = VERSION_CU.encode('utf-8')
    if VERSION_CU in content:
        if len(VERSION_CU) > len(VERSION_MOI):
            version_moi_padded = VERSION_MOI + "\x00" * (len(VERSION_CU) - len(VERSION_MOI))
        else:
            version_moi_padded = VERSION_MOI
        data = data.replace(version_cu_bytes, version_moi_padded.encode('utf-8'))
        changes.append(f"Version: '{VERSION_CU}' -> '{VERSION_MOI}'")
    
    print(f"  Da patch: {', '.join(changes)}")
    
    # Dong goi
    abc_patched = dong_goi_abc(bytes(data), name, original_size)
    
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
    print("QUET VA PATCH .abc TRONG 5 THU MUC CHI DINH")
    print("=" * 70)
    
    print(f"\n[CAU HINH]")
    print(f"  IP cu: {IP_CU} -> IP moi: {IP_MOI}")
    print(f"  Version cu: {VERSION_CU} -> Version moi: {VERSION_MOI}")
    print(f"\n[5 THU MUC CHI DINH]")
    for d in TARGET_DIRS:
        print(f"  - {d}")
    
    # Tim tat ca file .abc trong 5 thu muc
    abc_files = []
    for dir_path in TARGET_DIRS:
        if os.path.exists(dir_path):
            pattern = os.path.join(dir_path, "**", "*.abc")
            found = glob.glob(pattern, recursive=True)
            abc_files.extend(found)
            print(f"\n[{dir_path}]")
            print(f"  Tim thay {len(found)} file .abc")
        else:
            print(f"\n[{dir_path}]")
            print(f"  [LOI] Thu muc khong ton tai!")
    
    print(f"\n{'='*70}")
    print(f"TONG SO FILE TIM THAY: {len(abc_files)}")
    print(f"{'='*70}")
    
    if not abc_files:
        print("\n[CANH BAO] Khong co file .abc nao de xu ly!")
        return
    
    # Xu ly tung file
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
    print(f"That bai/Bo qua: {len(abc_files) - thanh_cong}")
    
    print(f"\n{'='*70}")
    print("DANH SACH FILE DA PATCH THANH CONG")
    print(f"{'='*70}")
    for file_path, ok, msg in ket_qua:
        if ok:
            print(f"\n[OK] {file_path}")
            for m in msg:
                print(f"    - {m}")


if __name__ == "__main__":
    main()
