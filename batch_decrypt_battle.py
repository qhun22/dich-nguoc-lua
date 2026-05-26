import os
import glob
import subprocess
import zipfile

def process_all_abc():
    base_dir = r"d:\FileD\dota\dgame.app"
    battle_dir = os.path.join(base_dir, "data", "battle")
    parser_script = os.path.join(base_dir, "python_scripts", "parse_bot2.py")
    unluac_cp = os.path.join(base_dir, "python_scripts", "unluac_src2", "unluac-master", "bin")
    
    # Get all .abc files recursively
    abc_files = glob.glob(os.path.join(battle_dir, "**", "*.abc"), recursive=True)
    
    for file_path in abc_files:
        dir_name = os.path.dirname(file_path)
        basename = os.path.basename(file_path)
        name_no_ext = os.path.splitext(basename)[0]
        
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
        zip_temp_path = os.path.join(dir_name, f"temp_{name_no_ext}.zip")
        with open(zip_temp_path, "wb") as f:
            f.write(out_buffer)
            
        # 2. Unzip with dynamic password
        pwd = f"cocos2d: ERROR: Invalid filename {name_no_ext}"
        extracted_data_path = os.path.join(dir_name, "data")
        
        try:
            with zipfile.ZipFile(zip_temp_path, 'r') as zip_ref:
                zip_ref.extractall(path=dir_name, pwd=pwd.encode('utf-8'))
        except Exception as e:
            print(f"Failed to unzip {basename}: {e}")
            if os.path.exists(zip_temp_path): os.remove(zip_temp_path)
            continue
            
        if os.path.exists(zip_temp_path):
            os.remove(zip_temp_path)
            
        # 3. Rename extracted 'data' file to .luac
        luac_path = os.path.join(dir_name, f"{name_no_ext}.luac")
        if os.path.exists(extracted_data_path):
            if os.path.exists(luac_path):
                os.remove(luac_path)
            os.rename(extracted_data_path, luac_path)
        else:
            print(f"Extracted 'data' file not found for {basename}")
            continue
            
        # 4. Disassemble using unluac (via classpath)
        dis_path = os.path.join(dir_name, f"{name_no_ext}.dis.txt")
        try:
            with open(dis_path, "w", encoding="utf-8") as dis_f:
                subprocess.run(
                    ["java", "-cp", unluac_cp, "unluac.Main", "--disassemble", luac_path],
                    stdout=dis_f,
                    stderr=subprocess.PIPE,
                    check=True
                )
        except subprocess.CalledProcessError as e:
            print(f"unluac failed for {basename}: {e.stderr.decode('utf-8', errors='ignore')}")
            continue
            
        # 5. Parse to pseudo-lua using parse_bot2.py
        lua_path = os.path.join(dir_name, f"{name_no_ext}.lua")
        try:
            subprocess.run(
                ["python", parser_script, dis_path, lua_path],
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"parse_bot2.py failed for {basename}")
            continue

        # 6. Run auto-cleaner logic
        clean_path = os.path.join(dir_name, f"{name_no_ext}_clean.lua")
        try:
            with open(lua_path, "r", encoding="utf-8") as f_in:
                lines = f_in.readlines()
            
            with open(clean_path, "w", encoding="utf-8") as f_out:
                f_out.write(f"-- =========================================================================\n")
                f_out.write(f"-- BÁO CÁO ĐỒ ÁN TỐT NGHIỆP - TỐI ƯU HÓA MÃ NGUỒN BOT LUA VM\n")
                f_out.write(f"-- File: {name_no_ext}_clean.lua\n")
                f_out.write(f"-- Mục đích: Module {name_no_ext} của Battle Engine (Đã Auto-Refactored)\n")
                f_out.write(f"-- =========================================================================\n\n")
                
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith("-- [Line"):
                        # Extract the actual pseudo code part after the comment
                        # Format: "    -- [Line 123] r0 = r2[r1]"
                        # We can just split by "] " and take the rest
                        parts = line.split("] ", 1)
                        if len(parts) > 1:
                            pseudo_code = parts[1]
                            if "op49" in pseudo_code:
                                continue
                            # add a standard indent
                            f_out.write("    " + pseudo_code)
                    else:
                        f_out.write(line)

            print(f"Successfully generated {clean_path}")
        except Exception as e:
            print(f"Cleaner failed for {basename}: {e}")

        # 7. Cleanup temp files
        for temp_file in [luac_path, dis_path, lua_path]:
            if os.path.exists(temp_file):
                os.remove(temp_file)

if __name__ == '__main__':
    process_all_abc()
