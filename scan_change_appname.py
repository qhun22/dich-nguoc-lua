# -*- coding: utf-8 -*-
"""
Script quet va doi ten app trong APK
Tim kiem trong tat ca cac file de tim ten app cu
"""
import sys
import codecs

# Fix UTF-8 output
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

import os
import re

def search_in_file(filepath, old_name, new_name):
    """Tim va thay the ten app trong file."""
    try:
        with open(filepath, 'rb') as f:
            content = f.read()
        
        # Thu decode voi utf-8
        try:
            text = content.decode('utf-8')
        except:
            try:
                text = content.decode('utf-16')
            except:
                return False
        
        if old_name.lower() in text.lower():
            # Thay the
            new_text = re.sub(re.escape(old_name), new_name, text, flags=re.IGNORECASE)
            
            if new_text != text:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_text)
                return True
    except:
        pass
    return False

def scan_directory(base_dir, old_name, new_name):
    """Quet toan bo thu muc."""
    results = []
    
    for root, dirs, files in os.walk(base_dir):
        for f in files:
            filepath = os.path.join(root, f)
            
            # Chi quet cac file co the doc
            if f.endswith(('.xml', '.txt', '.json', '.lua', '.abc', '.plist', '.cfg', '.conf')):
                try:
                    with open(filepath, 'rb') as file:
                        content = file.read()
                    
                    # Check if old name exists
                    if old_name.lower().encode('utf-8') in content.lower():
                        rel_path = os.path.relpath(filepath, base_dir)
                        results.append(rel_path)
                        
                        # Thu thay the
                        changed = search_in_file(filepath, old_name, new_name)
                        if changed:
                            print(f"  [CHANGED] {rel_path}")
                        else:
                            print(f"  [FOUND] {rel_path}")
                except:
                    pass
    
    return results

def main():
    OLD_NAME = "TMgame99 Dota Truyền Kỳ 7 Sao"
    NEW_NAME = "DotaTruyenKy"
    
    print("=" * 60)
    print("APP NAME SCANNER")
    print("=" * 60)
    print(f"Tên cũ: {OLD_NAME}")
    print(f"Tên mới: {NEW_NAME}")
    print()
    
    # Quet trong apk/base/assets
    print("Dang quet thu muc assets...")
    assets_dir = r"d:\FileD\dota\apk\base\assets"
    
    if os.path.exists(assets_dir):
        results = scan_directory(assets_dir, OLD_NAME, NEW_NAME)
        
        print()
        print("=" * 60)
        print(f"Ket qua: Tim thay {len(results)} files")
        
        if results:
            print("\nFiles chua ten app cu:")
            for r in results:
                print(f"  - {r}")
        else:
            print("\nKhong tim thay ten app trong assets.")
            print("Ten app co the nam trong resources.arsc (binary).")
    else:
        print("Khong tim thay thu muc assets!")

if __name__ == "__main__":
    main()
