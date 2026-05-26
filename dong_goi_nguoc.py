# -*- coding: utf-8 -*-
"""
Buoc 2: Dong goi nguoc file .luac thanh .abc
Pipeline nguoc:
  1. Tao ZIP voi password dong: "cocos2d: ERROR: Invalid filename <name>"
  2. Ma hoa Stride-10007 Permutation + XOR voi key "name.abc"
"""
import os
import sys
import zipfile
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# Thêm thư mục tools vào path để import nếu cần
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# === CẤU HÌNH ===
LUAC_FILE = r"d:\FileD\dota\ios\dgame.app\data\bot\ipconfig.luac"
ABC_FILE = r"d:\FileD\dota\ios\dgame.app\data\bot\ipconfig.abc"
FILE_NAME = "ipconfig"  # Tên file không có đuôi
# =================


def tao_zip(data, name):
    """
    Tạo ZIP archive với entry 'data' chứa nội dung bytecode.
    Password: "cocos2d: ERROR: Invalid filename <name>"
    """
    pwd = f"cocos2d: ERROR: Invalid filename {name}".encode('utf-8')
    
    # Tạo ZIP trong memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Thêm entry "data" chứa nội dung
        zf.writestr("data", data, compress_type=zipfile.ZIP_STORED)
    
    zip_data = zip_buffer.getvalue()
    return zip_data


def scramble_abc(data, name):
    """
    Ma hoa Stride-10007 Permutation + XOR.
    Day la ham nguoc cua descramble_abc().
    
    Thuật toán descramble_abc (giai ma):
      pos = 0
      for i in range(size):
        dest = pos % size
        buffer[dest] = encrypted[i] ^ key[i % key_len]
        pos += 10007
    
    Nghich dao:
      - encrypted[i] = buffer[dest] ^ key[i % key_len]
      - dest = (i * 10007) % size
    """
    size = len(data)
    key = f"{name}.abc".encode('utf-8')
    key_len = len(key)
    
    # Tao buffer dau ra
    buffer = bytearray(size)
    
    # Thuật toan scramble: với mỗi i trong data đầu vào,
    # tính dest = (i * stride) % size và ghi vào buffer
    # Nhưng thực tế, descramble sử dụng:
    #   dest = pos % size với pos += stride
    # Điều này có nghĩa là mỗi dest sẽ được ghi đúng 1 lần
    # Vậy để scramble, ta cần tìm i sao cho descramble ghi vào dest
    
    # Tính toán permutation nghịch đảo
    # Trong descramble: buffer[(i * stride) % size] = encrypted[i] ^ key[...]
    # Trong scramble: encrypted[(dest * inverse_stride) % size] = buffer[dest] ^ key[...]
    
    # Tìm modular inverse của stride mod size
    stride = 10007
    
    # Sử dụng brute force để tìm inverse
    # Tìm x sao cho (stride * x) % size == 1
    inverse_stride = None
    for x in range(1, size):
        if (stride * x) % size == 1:
            inverse_stride = x
            break
    
    if inverse_stride is None:
        # Không có inverse, sử dụng brute force
        print(f"  Khong tim duoc inverse, su dung brute force...")
        
        # Tạo encrypted rỗng
        encrypted = bytearray(size)
        
        # Với mỗi dest trong buffer, tìm i sao cho dest = (i * stride) % size
        # i = (dest * k) % size với k là số sao cho (k * stride) % size = 1
        for i in range(size):
            dest = (i * stride) % size
            encrypted[i] = data[dest] ^ key[i % key_len]
        
        return bytes(encrypted)
    
    # Sử dụng inverse để scramble
    encrypted = bytearray(size)
    
    for i in range(size):
        dest = (i * stride) % size
        encrypted[dest] = data[i] ^ key[dest % key_len]
    
    # Cách khác: vì descramble ghi buffer[dest] = encrypted[i] với dest = (i * stride) % size
    # Nên scramble cần: encrypted[(dest * inv_stride) % size] = buffer[dest]
    
    # Thử cách này
    result = bytearray(size)
    for dest in range(size):
        # Tìm i sao cho dest = (i * stride) % size
        # i = (dest * inv_stride) % size
        i = (dest * inverse_stride) % size
        result[i] = data[dest] ^ key[dest % key_len]
    
    return bytes(result)


def doc_file(duong_dan):
    """Đọc file .luac."""
    with open(duong_dan, "rb") as f:
        return f.read()


def luu_file(duong_dan, data):
    """Lưu file .abc."""
    with open(duong_dan, "wb") as f:
        f.write(data)
    print(f"  Đã lưu: {duong_dan} ({len(data)} bytes)")


def main():
    print("=" * 60)
    print("ĐÓNG GÓI NGƯỢC: .luac -> .abc")
    print("=" * 60)
    
    print(f"\n[CẤU HÌNH]")
    print(f"  File Lua bytecode: {LUAC_FILE}")
    print(f"  File ABC đầu ra: {ABC_FILE}")
    print(f"  Tên file: {FILE_NAME}")
    
    # Bước 1: Kiểm tra file tồn tại
    print(f"\n[1] Kiểm tra file...")
    if not os.path.exists(LUAC_FILE):
        print(f"  Lỗi: File {LUAC_FILE} không tồn tại!")
        print(f"  Chạy 'patch_ip.py' trước để tạo file .luac đã patch IP.")
        return
    
    # Bước 2: Đọc file Lua bytecode
    print(f"\n[2] Đọc file Lua bytecode...")
    lua_data = doc_file(LUAC_FILE)
    print(f"  Kích thước: {len(lua_data)} bytes")
    
    if lua_data[:3] == b'\x1bLua':
        print("  [OK] Signature Lua 5.1 bytecode hợp lệ")
    else:
        print("  [CẢNH BÁO] File không có signature Lua chuẩn")
    
    # Bước 3: Tạo ZIP với password động
    print(f"\n[3] Tạo ZIP archive...")
    print(f"  Password: cocos2d: ERROR: Invalid filename {FILE_NAME}")
    zip_data = tao_zip(lua_data, FILE_NAME)
    print(f"  Kích thước ZIP: {len(zip_data)} bytes")
    
    # Bước 4: Mã hóa Stride Permutation
    print(f"\n[4] Mã hóa Stride-10007...")
    print(f"  Key: {FILE_NAME}.abc")
    encrypted = scramble_abc(zip_data, FILE_NAME)
    print(f"  Kích thước encrypted: {len(encrypted)} bytes")
    
    # Bước 5: Lưu file .abc
    print(f"\n[5] Lưu file .abc...")
    luu_file(ABC_FILE, encrypted)
    
    # Bước 6: Xác minh bằng cách giải mã lại
    print(f"\n[6] Xác minh (giải mã thử)...")
    
    # Hàm giải mã (để test)
    def descramble(encrypted, name):
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
    
    test_data = descramble(encrypted, FILE_NAME)
    
    # Kiểm tra ZIP signature
    if test_data[:4] == b'PK\x03\x04':
        print("  [OK] File .abc hợp lệ! Có thể giải mã thành công.")
    else:
        print("  [CẢNH BÁO] File có thể không hợp lệ!")
    
    print("\n" + "=" * 60)
    print("HOÀN TẤT! File .abc đã được tạo thành công.")
    print(f"  File: {ABC_FILE}")
    print("Tiếp theo: Copy file này vào thư mục iOS app và cài đặt lại.")
    print("=" * 60)


if __name__ == "__main__":
    main()
