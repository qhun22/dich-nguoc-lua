# -*- coding: utf-8 -*-
"""Tim kiem rong rai trong tat ca cac file"""
import os
import glob

SEARCH_TERMS = [
    b"192.168.1.179",
    b"9.9.0",
    b"versionStr",
]

# Thu muc goc
ROOT = r"d:\FileD\dota\ios\dgame.app"

# Cac duoi file can bo qua
SKIP_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.mp3', '.wav', '.ttf', '.otf',
    '.atlas', '.fnt', '.pvr', '.pvr.ccz', '.luac', '.abc'
}

def search_file(filepath):
    """Tim kiem trong mot file."""
    results = []
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
        
        for term in SEARCH_TERMS:
            if term in data:
                idx = data.find(term)
                context = data[max(0,idx-50):idx+len(term)+50]
                results.append({
                    'term': term.decode('utf-8', errors='replace'),
                    'pos': idx,
                    'context': context.hex()[:200]
                })
    except:
        pass
    return results

def main():
    print("=" * 70)
    print("TIM KIEM RONG RAI TRONG TAT CA FILE")
    print("=" * 70)
    
    # Tim tat ca file
    all_files = []
    for root, dirs, files in os.walk(ROOT):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext not in SKIP_EXTENSIONS:
                all_files.append(os.path.join(root, f))
    
    print(f"\nTong so file can kiem tra: {len(all_files)}")
    
    # Kiem tra tung file
    found_files = []
    for i, filepath in enumerate(all_files):
        if i % 500 == 0:
            print(f"  Da kiem tra {i}/{len(all_files)} files...")
        
        results = search_file(filepath)
        if results:
            found_files.append((filepath, results))
    
    # Hien thi ket qua
    print(f"\n{'='*70}")
    print(f"KET QUA TIM KIEM ({len(found_files)} file)")
    print("=" * 70)
    
    for filepath, results in found_files:
        print(f"\n[OK] {filepath}")
        for r in results:
            print(f"     Term: '{r['term']}' tai vi tri {r['pos']}")
            print(f"     Hex: {r['context'][:100]}...")

if __name__ == "__main__":
    main()
