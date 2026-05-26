import os
import quicklz


def brute_force_cocos_crypto(file_path):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))

    if not os.path.isabs(file_path):
        file_path = os.path.normpath(os.path.join(project_root, file_path))

    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, "rb") as f:
        encrypted_data = f.read()

    file_size = len(encrypted_data)

    potential_keys = [
        "d:/FileD/dota/dgame.app/data/bot/",
        "data/bot/",
        "/bot2.abc",
        "bot2.abc",
    ]

    print("Brute-forcing stride 1-256 and key variants...")

    for key_str in potential_keys:
        key_bytes = key_str.encode("utf-8")
        key_len = len(key_bytes)

        for stride in range(1, 257):
            decrypted_buffer = bytearray(file_size)
            u_var9 = 0
            i_var8 = 0

            for byte in encrypted_data:
                dest_idx = u_var9 % file_size
                decrypted_buffer[dest_idx] = byte ^ key_bytes[i_var8 % key_len]
                i_var8 += 1
                u_var9 += stride

            try:
                final_code = quicklz.decompress(bytes(decrypted_buffer))
            except Exception:
                continue

            output_file = os.path.join(script_dir, "bot2_FINAL_SOURCE.txt")
            with open(output_file, "wb") as out_f:
                out_f.write(final_code)

            print("SUCCESS")
            print(f"Key: {key_str}")
            print(f"Stride: {stride}")
            print(f"Output: {output_file}")
            return

    print("No matching stride/key found for QuickLZ decompression.")


if __name__ == "__main__":
    brute_force_cocos_crypto("data/bot/bot2.abc")
