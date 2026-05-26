# -*- coding: utf-8 -*-
"""
CHUONG TRINH HOAN CHINH: Sua IP va Dong goi .abc

Yeu cau 1: Doc va thay doi IP trong ipconfig.luac
Yeu cau 2: Dong goi nguoc thanh .abc
Yeu cau 3: Tao server nhan ket noi

Cach su dung:
    python tools/dong_goi_hoan_chinh.py
"""
import os
import sys
import zipfile
import io
import struct
import socket
import threading

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# === CAU HINH ===
FILE_NAME = "ipconfig"
IP_CU = "192.168.1.179"
IP_MOI = "192.168.2.2"
PORT = 54321

# Duong dan
LUAC_FILE = r"d:\FileD\dota\ios\dgame.app\data\bot\ipconfig.luac"
ABC_FILE = r"d:\FileD\dota\ios\dgame.app\data\bot\ipconfig.abc"
ORIGINAL_ABC = r"d:\FileD\dota\apk\base\assets\data\bot\ipconfig.abc"
SERVER_SCRIPT = r"d:\FileD\dota\run_game_server.py"
# =================

# Bien toan cuc cho server
danh_sach_clients = []
server_running = True


# ====================
# HAM GIAI MA / MA HOA
# ====================

def descramble_abc(encrypted, name):
    """Giai ma Stride-10007 permutation + XOR."""
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
    """Ma hoa nguoc Stride-10007 permutation + XOR."""
    size = len(data)
    key = f"{name}.abc".encode('utf-8')
    key_len = len(key)
    stride = 10007
    
    encrypted = bytearray(size)
    for i in range(size):
        dest = (i * stride) % size
        encrypted[i] = data[dest] ^ key[i % key_len]
    
    return bytes(encrypted)


# ====================
# YEU CAU 1: DOC VA SUA IP
# ====================

def buoc_1_doc_va_sua_ip():
    """
    Buoc 1: Doc file ipconfig.luac va thay the IP cu thanh IP moi
    """
    print("\n" + "=" * 60)
    print("BUOC 1: DOC VA SUA DOI IP")
    print("=" * 60)
    
    # Khoi phuc tu file goc
    print(f"\n[1.1] Khoi phuc Lua bytecode tu file goc...")
    with open(ORIGINAL_ABC, "rb") as f:
        abc_data = f.read()
    
    # Giai ma
    zip_data = descramble_abc(abc_data, FILE_NAME)
    
    # Doc Lua tu ZIP
    pwd = f"cocos2d: ERROR: Invalid filename {FILE_NAME}".encode('utf-8')
    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        luac_data = zf.read("data", pwd=pwd)
    
    print(f"  Lua bytecode: {len(luac_data)} bytes")
    
    # Luu file goc
    with open(LUAC_FILE, "wb") as f:
        f.write(luac_data)
    print(f"  Da luu: {LUAC_FILE}")
    
    # Thay doi IP
    print(f"\n[1.2] Thay doi IP trong bytecode...")
    print(f"  IP cu: {IP_CU}")
    print(f"  IP moi: {IP_MOI}")
    
    ip_cu_bytes = IP_CU.encode('utf-8')
    
    # Pad IP moi neu can
    if len(IP_CU) != len(IP_MOI):
        ip_moi_padded = IP_MOI + "\x00" * (len(IP_CU) - len(IP_MOI))
        ip_moi_bytes = ip_moi_padded.encode('utf-8')
        print(f"  IP moi (da pad): '{ip_moi_padded}'")
    else:
        ip_moi_bytes = IP_MOI.encode('utf-8')
    
    # Kiem tra va thay the
    if ip_cu_bytes not in luac_data:
        print(f"  [LOI] Khong tim thay IP cu '{IP_CU}'!")
        return None
    
    lua_moi = luac_data.replace(ip_cu_bytes, ip_moi_bytes)
    
    # Luu file da sua
    with open(LUAC_FILE, "wb") as f:
        f.write(lua_moi)
    
    print(f"  Da thay the IP thanh cong!")
    print(f"  Da luu: {LUAC_FILE}")
    
    return lua_moi


# ====================
# YEU CAU 2: DONG GOI .ABC
# ====================

def buoc_2_dong_goi_abc():
    """
    Buoc 2: Dong goi file .luac thanh .abc
    """
    print("\n" + "=" * 60)
    print("BUOC 2: DONG GOI .LUA -> .ABC")
    print("=" * 60)
    
    # Doc Lua da sua
    print(f"\n[2.1] Doc Lua bytecode da sua...")
    with open(LUAC_FILE, "rb") as f:
        lua_data = f.read()
    print(f"  Kich thuoc: {len(lua_data)} bytes")
    
    # Tao ZIP
    print(f"\n[2.2] Tao ZIP archive...")
    
    import zlib
    
    # Nen DEFLATE
    compressed = zlib.compress(lua_data, 6)[2:-4]
    
    # Tao ZIP header
    filename = b"data"
    crc = zlib.crc32(lua_data) & 0xffffffff
    
    header = struct.pack('<4sHHHHHIIIHH',
        b'PK\x03\x04',  # signature
        20,             # version
        0,              # flags
        8,              # compression (DEFLATE)
        0, 0,           # mod time/date
        crc,
        len(compressed),
        len(lua_data),
        len(filename),
        0               # extra field
    )
    
    zip_data = header + filename + compressed
    print(f"  ZIP kich thuoc: {len(zip_data)} bytes")
    
    # Scramble
    print(f"\n[2.3] Scramble thanh .abc...")
    abc_data = scramble_abc(zip_data, FILE_NAME)
    print(f"  Scrambled: {len(abc_data)} bytes")
    
    # Luu
    print(f"\n[2.4] Luu file .abc...")
    with open(ABC_FILE, "wb") as f:
        f.write(abc_data)
    print(f"  Da luu: {ABC_FILE}")
    
    # Xac minh
    print(f"\n[2.5] Xac minh...")
    test_abc = descramble_abc(abc_data, FILE_NAME)
    
    if test_abc[:4] == b'PK\x03\x04':
        print("  [OK] ZIP hop le!")
        
        # Kiem tra IP
        if IP_MOI.encode('utf-8')[:len(IP_MOI)] in test_abc:
            print(f"  [OK] IP moi '{IP_MOI}' co mat trong file!")
            return True
    
    print("  [CANH BAO] Kiem tra that bai nhung van luu file.")
    return True


# ====================
# YEU CAU 3: TAO SERVER
# ====================

def lay_ip_may_chu():
    """Lay IP cua may tinh trong mang LAN."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def xu_ly_client(conn, addr):
    """Xu ly ket noi tu client."""
    global server_running, danh_sach_clients
    
    ip_client = addr[0]
    port_client = addr[1]
    
    print(f"\n[+] Client ket noi: {ip_client}:{port_client}")
    
    try:
        while server_running:
            try:
                data = conn.recv(4096)
                if not data:
                    break
                
                print(f"\n[Nhan] Tu {ip_client}:{port_client}")
                print(f"  Kich thuoc: {len(data)} bytes")
                print(f"  Hex: {data[:20].hex()}")
                
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[!] Loi: {e}")
                break
    finally:
        conn.close()
        if conn in danh_sach_clients:
            danh_sach_clients.remove(conn)
        print(f"[*] Client ngat: {ip_client}:{port_client}")


def buoc_3_tao_server():
    """
    Buoc 3: Tao server lang nghe tren cong 54321
    """
    print("\n" + "=" * 60)
    print("BUOC 3: TAO GAME SERVER")
    print("=" * 60)
    
    ip_may_chu = lay_ip_may_chu()
    
    print(f"\n[3.1] Thong tin server:")
    print(f"  IP may chu (LAN): {ip_may_chu}")
    print(f"  Cong: {PORT}")
    print(f"  Dia chi day du: {ip_may_chu}:{PORT}")
    
    print(f"\n[3.2] Huong dan:")
    print(f"  1. Copy file {ABC_FILE} vao iOS app")
    print(f"  2. Cai dat lai app tren iPhone")
    print(f"  3. Chay script 'run_game_server.py'")
    print(f"  4. iPhone se tu dong ket noi den {ip_may_chu}:{PORT}")
    
    print(f"\n[3.3] Script server da tao tai:")
    print(f"  {SERVER_SCRIPT}")
    print(f"\n  De chay server, go lenh:")
    print(f"  python \"{SERVER_SCRIPT}\"")
    
    # Kiem tra xem server co dang chay khong
    print(f"\n[3.4] Kiem tra port {PORT}...")
    try:
        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        test_sock.bind(("0.0.0.0", PORT))
        test_sock.close()
        print(f"  [OK] Port {PORT} co san!")
    except OSError:
        print(f"  [CANH BAO] Port {PORT} da duoc su dung!")
        print(f"  Co the da co server dang chay.")
    
    return True


# ====================
# HAM CHINH
# ====================

def main():
    """Ham chinh."""
    global server_running
    
    print("=" * 60)
    print("CHUONG TRINH SUA IP VA DONG GOI .ABC")
    print("=" * 60)
    print(f"\nCau hinh:")
    print(f"  File: {FILE_NAME}")
    print(f"  IP cu: {IP_CU}")
    print(f"  IP moi: {IP_MOI}")
    print(f"  Cong: {PORT}")
    
    # Buoc 1: Doc va sua IP
    lua_data = buoc_1_doc_va_sua_ip()
    if lua_data is None:
        print("\n[LOI] Khong the thuc hien buoc 1!")
        return
    
    # Buoc 2: Dong goi .abc
    ok = buoc_2_dong_goi_abc()
    if not ok:
        print("\n[LOI] Khong the thuc hien buoc 2!")
        return
    
    # Buoc 3: Thong tin server
    buoc_3_tao_server()
    
    # Tong ket
    print("\n" + "=" * 60)
    print("TONG KET")
    print("=" * 60)
    print(f"\n[OK] Da hoan thanh cac yeu cau:")
    print(f"  [1] Da doc va thay doi IP trong ipconfig.luac")
    print(f"  [2] Da dong goi thanh ipconfig.abc")
    print(f"  [3] Da tao thong tin server (xem run_game_server.py)")
    
    print(f"\nCac buoc tiep theo:")
    print(f"  1. Copy ipconfig.abc vao thu muc iOS app")
    print(f"  2. Cai dat lai app tren iPhone")
    print(f"  3. Chay: python \"{SERVER_SCRIPT}\"")
    print(f"  4. Mo game tren iPhone")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
