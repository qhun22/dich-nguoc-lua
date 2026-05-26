import os

def decrypt_abc_file(input_path, output_path):
    # Chìa khóa vạn năng tìm được từ hàm Xor::getXorStr
    KEY = b"cmto6or!M#@nnsk19"
    key_len = len(KEY)
    
    if not os.path.exists(input_path):
        print(f"❌ Không tìm thấy file: {input_path}")
        return

    print(f"⏳ Đang giải mã file {input_path}...")
    
    with open(input_path, "rb") as f:
        encrypted_data = f.read()
        
    decrypted_bytes = bytearray()
    
    # Chạy vòng lặp XOR từng byte dữ liệu với Key tuần hoàn
    for i, byte in enumerate(encrypted_data):
        # Phép toán XOR cơ bản giống trong mã nguồn game
        decrypted_byte = byte ^ KEY[i % key_len]
        decrypted_bytes.append(decrypted_byte)
        
    # Ghi dữ liệu sạch ra file mới
    with open(output_path, "wb") as f:
        f.write(decrypted_bytes)
        
    print(f"🎉 Giải mã thành công! File sạch lưu tại: {output_path}")

if __name__ == "__main__":
    # Resolve paths relative to the script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, "bot2.abc")
    output_path = os.path.join(script_dir, "bot2_clean.txt")
    decrypt_abc_file(input_path, output_path)