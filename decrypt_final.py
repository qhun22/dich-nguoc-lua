import os


def decrypt_cocos_custom(file_path, output_path):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))

    if not os.path.isabs(file_path):
        file_path = os.path.normpath(os.path.join(project_root, file_path))
    if not os.path.isabs(output_path):
        output_path = os.path.normpath(os.path.join(project_root, output_path))

    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    normalized_path = file_path.replace("\\", "/")
    dir_path = os.path.dirname(normalized_path) + "/"
    key = dir_path.encode("utf-8")
    key_len = len(key)

    print(f"Key from directory: '{dir_path}'")

    with open(file_path, "rb") as f:
        encrypted_data = f.read()

    file_size = len(encrypted_data)
    decrypted_buffer = bytearray(file_size)

    u_var9 = 0
    i_var8 = 0
    u_var11 = 1

    for byte in encrypted_data:
        dest_idx = u_var9 % file_size
        decrypted_buffer[dest_idx] = byte ^ key[i_var8 % key_len]
        i_var8 += 1
        u_var9 += u_var11

    with open(output_path, "wb") as f:
        f.write(decrypted_buffer)

    print(f"Decrypted output: {output_path}")


if __name__ == "__main__":
    decrypt_cocos_custom("data/bot/bot2.abc", "data/bot/bot2_clear_lua.txt")
