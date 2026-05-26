import os
import quicklz


def decrypt_with_exact_stride(file_path):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))

    if not os.path.isabs(file_path):
        file_path = os.path.normpath(os.path.join(project_root, file_path))

    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    stride = 10007

    potential_keys = [
        "data/bot/",
        "d:/FileD/dota/dgame.app/data/bot/",
        "/bot2.abc",
        "bot2.abc",
    ]

    with open(file_path, "rb") as f:
        encrypted_data = f.read()

    file_size = len(encrypted_data)

    for key_str in potential_keys:
        key_bytes = key_str.encode("utf-8")
        key_len = len(key_bytes)

        unscrambled_buffer = bytearray(file_size)
        u_var9 = 0
        i_var8 = 0

        for byte in encrypted_data:
            dest_idx = u_var9 % file_size
            unscrambled_buffer[dest_idx] = byte ^ key_bytes[i_var8 % key_len]
            i_var8 += 1
            u_var9 += stride

        header_sample = unscrambled_buffer[:4]
        header_text = "".join(chr(b) if 32 <= b < 127 else "." for b in header_sample)
        print(f"--- Key: '{key_str}' ---")
        print(f"Header hex: {header_sample.hex(' ')}")
        print(f"Header text: {header_text}")

        try:
            final_source = quicklz.decompress(bytes(unscrambled_buffer))
        except Exception:
            raw_name = f"unscrambled_{key_str.replace('/', '_').replace(':', '')}.bin"
            with open(raw_name, "wb") as raw_f:
                raw_f.write(unscrambled_buffer)
            print("Not QuickLZ, saved raw buffer for inspection.\n")
            continue

        output_path = "bot2_SUCCESS_CODE.txt"
        with open(output_path, "wb") as out_f:
            out_f.write(final_source)
        print(f"SUCCESS: {output_path}")
        return

    print("No matching key produced valid QuickLZ data.")


if __name__ == "__main__":
    decrypt_with_exact_stride("data/bot/bot2.abc")
