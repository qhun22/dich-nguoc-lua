# -*- coding: utf-8 -*-
"""
Step 1: Patch IP in ipconfig.luac file
Replace old IP '192.168.1.179' with new IP '192.168.2.2'
"""
import os
import sys

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# === CONFIG ===
IP_CU = "192.168.1.179"
IP_MOI = "192.168.2.2"  # IP moi co 11 ky tu, cu co 13 ky tu
                          # Se tu dong pad voi null byte de cung do dai
IPCONFIG_LUAC = r"d:\FileD\dota\ios\dgame.app\data\bot\ipconfig.luac"
# =================

def doc_file_luac(duong_dan):
    """Doc noi dung file .luac duoi dang bytes."""
    with open(duong_dan, "rb") as f:
        return f.read()


def tim_va_thay_the_ip(data, ip_cu, ip_moi):
    """
    Tim va thay the chuoi IP trong binary data.
    Neu do dai khac nhau, se pad voi null byte de giu nguyen do dai.
    """
    # Chuan bi bytes
    ip_cu_bytes = ip_cu.encode('utf-8')
    
    # Neu do dai khac nhau, pad IP moi voi null byte
    if len(ip_cu) != len(ip_moi):
        print(f"Chu y: IP cu co {len(ip_cu)} ky tu, IP moi co {len(ip_moi)} ky tu.")
        print(f"Se pad IP moi voi null byte de giu nguyen cau truc.")
        # Pad voi null byte cho den khi cung do dai
        ip_moi_padded = ip_moi + "\x00" * (len(ip_cu) - len(ip_moi))
        ip_moi_bytes = ip_moi_padded.encode('utf-8')
        print(f"IP moi sau khi pad: '{ip_moi_padded}' ({len(ip_moi_padded)} ky tu)")
    else:
        ip_moi_bytes = ip_moi.encode('utf-8')
    
    # Tim vi tri
    vi_tri = data.find(ip_cu_bytes)
    if vi_tri == -1:
        print(f"Khong tim thay IP '{ip_cu}' trong file!")
        return None
    
    print(f"Tim thay IP '{ip_cu}' tai vi tri: {vi_tri}")
    
    # Thay the
    data_moi = data.replace(ip_cu_bytes, ip_moi_bytes)
    
    # Dem so lan thay the
    so_lan = data.count(ip_cu_bytes)
    print(f"Da thay the {so_lan} vi tri")
    
    return data_moi


def luu_file(duong_dan, data):
    """Luu du lieu vao file."""
    with open(duong_dan, "wb") as f:
        f.write(data)
    print(f"Da luu file: {duong_dan}")


def hien_thi_context(data, vi_tri, do_dai=20):
    """Hien thi cac ky tu xung quanh vi tri de xac nhan."""
    bat_dau = max(0, vi_tri - do_dai)
    ket_thuc = min(len(data), vi_tri + do_dai)
    
    print(f"\nNgữ cảnh xung quanh vi tri {vi_tri}:")
    # Hien thi hex
    print(f"  Hex: {data[bat_dau:ket_thuc].hex()}")


def main():
    print("=" * 60)
    print("PATCH IP TRONG FILE LUA BYTECODE")
    print("=" * 60)
    
    print("\n[CAU HINH]")
    print(f"  IP cu: {IP_CU}")
    print(f"  IP moi: {IP_MOI}")
    print(f"  File: {IPCONFIG_LUAC}")
    
    # Buoc 1: Doc file
    print(f"\n[1] Doc file: {IPCONFIG_LUAC}")
    if not os.path.exists(IPCONFIG_LUAC):
        print(f"Loi: File khong ton tai!")
        return
    
    data = doc_file_luac(IPCONFIG_LUAC)
    print(f"  Kich thuoc: {len(data)} bytes")
    
    # Kiem tra signature Lua
    if data[:3] == b'\x1bLua':
        print("  [OK] Day la file Lua bytecode hop le")
    else:
        print("  [CANH BAO] File khong co signature Lua chuan")
    
    # Buoc 2: Tim vi tri IP cu
    print(f"\n[2] Tim IP cu '{IP_CU}'...")
    vi_tri = data.find(IP_CU.encode('utf-8'))
    if vi_tri != -1:
        hien_thi_context(data, vi_tri)
    
    # Buoc 3: Thay the IP
    print(f"\n[3] Thay the IP...")
    data_moi = tim_va_thay_the_ip(data, IP_CU, IP_MOI)
    if data_moi is None:
        print("Thay the that bai!")
        return
    
    # Xac nhan da thay doi
    vi_tri_moi = data_moi.find(IP_MOI.encode('utf-8'))
    if vi_tri_moi != -1:
        print(f"\n[OK] Xac nhan IP moi '{IP_MOI}' da duoc ghi tai vi tri {vi_tri_moi}")
        hien_thi_context(data_moi, vi_tri_moi)
    
    # Buoc 4: Luu file da patch
    print(f"\n[4] Luu file da patch...")
    luu_file(IPCONFIG_LUAC, data_moi)
    
    print("\n" + "=" * 60)
    print("HOAN TAT! IP da duoc thay doi.")
    print("Tiep theo: Chay script 'dong_goi_nguoc.py' de dong goi thanh .abc")
    print("=" * 60)


if __name__ == "__main__":
    main()
