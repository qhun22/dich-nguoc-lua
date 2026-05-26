import os
import glob
import subprocess
import zipfile
import shutil

def process_all_abc():
    bot_dir = r"data\bot"
    unluac_jar = r"data\bot\tools\unluac.jar"
    parser_script = "parse_bot2.py"
    
    # Get all .abc files in data/bot
    abc_files = glob.glob(os.path.join(bot_dir, "*.abc"))
    
    for file_path in abc_files:
        basename = os.path.basename(file_path)
        name_no_ext = os.path.splitext(basename)[0]
        
        # Skip bot2.abc since it's already done
        if basename == "bot2.abc":
            print(f"Skipping {basename}...")
            continue
            
        print(f"\n--- Processing {basename} ---")
        
        # 1. Unscramble Stride 10007 and XOR
        with open(file_path, "rb") as f:
            encrypted_data = f.read()
            
        file_size = len(encrypted_data)
        out_buffer = bytearray(file_size)
        key_bytes = basename.encode('utf-8')
        key_len = len(key_bytes)
        
        u_var9 = 0
        for i, byte in enumerate(encrypted_data):
            dest_idx = u_var9 % file_size
            out_buffer[dest_idx] = byte ^ key_bytes[i % key_len]
            u_var9 += 10007
            
        # Write zip file to temp
        zip_temp_path = os.path.join(bot_dir, f"temp_{name_no_ext}.zip")
        with open(zip_temp_path, "wb") as f:
            f.write(out_buffer)
            
        # 2. Unzip with dynamic password
        pwd = f"cocos2d: ERROR: Invalid filename {name_no_ext}"
        extracted_data_path = os.path.join(bot_dir, "data")
        
        try:
            with zipfile.ZipFile(zip_temp_path, 'r') as zip_ref:
                # The file inside the zip is often named "data"
                zip_ref.extractall(path=bot_dir, pwd=pwd.encode('utf-8'))
        except Exception as e:
            print(f"Failed to unzip {basename}: {e}")
            if os.path.exists(zip_temp_path):
                os.remove(zip_temp_path)
            continue
            
        # Clean up temp zip
        if os.path.exists(zip_temp_path):
            os.remove(zip_temp_path)
            
        # 3. Rename extracted 'data' file to .luac
        luac_path = os.path.join(bot_dir, f"{name_no_ext}.luac")
        if os.path.exists(extracted_data_path):
            if os.path.exists(luac_path):
                os.remove(luac_path)
            os.rename(extracted_data_path, luac_path)
        else:
            print(f"Extracted 'data' file not found for {basename}")
            continue
            
        # 4. Disassemble using unluac
        dis_path = os.path.join(bot_dir, f"{name_no_ext}.dis.txt")
        try:
            with open(dis_path, "w", encoding="utf-8") as dis_f:
                subprocess.run(
                    ["java", "-cp", unluac_jar, "unluac.Main", "--disassemble", luac_path],
                    stdout=dis_f,
                    stderr=subprocess.PIPE,
                    check=True
                )
            print(f"Disassembled to {dis_path}")
        except subprocess.CalledProcessError as e:
            print(f"unluac failed for {basename}: {e.stderr.decode('utf-8', errors='ignore')}")
            continue
            
        # 5. Parse to pseudo-lua using parse_bot2.py
        lua_path = os.path.join(bot_dir, f"{name_no_ext}.lua")
        try:
            subprocess.run(
                ["python", parser_script, dis_path, lua_path],
                check=True
            )
            print(f"Successfully generated {lua_path}")
        except subprocess.CalledProcessError as e:
            print(f"parse_bot2.py failed for {basename}")
            continue

if __name__ == '__main__':
    process_all_abc()
