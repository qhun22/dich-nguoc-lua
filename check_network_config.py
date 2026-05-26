# -*- coding: utf-8 -*-
import zipfile
import io
import os
import re

def descramble_abc(encrypted, name):
    size = len(encrypted)
    buffer = bytearray(size)
    key = f'{name}.abc'.encode('utf-8')
    key_len = len(key)
    pos = 0
    for i in range(size):
        dest = pos % size
        buffer[dest] = encrypted[i] ^ key[i % key_len]
        pos += 10007
    return bytes(buffer)

def check_file(filepath):
    name = os.path.basename(filepath).replace('.abc', '')
    print(f"\n=== {name}.abc ===")
    try:
        with open(filepath, 'rb') as f:
            abc_data = f.read()
        
        zip_data = descramble_abc(abc_data, name)
        pwd = f'cocos2d: ERROR: Invalid filename {name}'.encode('utf-8')
        
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            lua_data = zf.read('data', pwd=pwd)
            
        # Extract strings
        strings = re.findall(b'[\x20-\x7e]{8,}', lua_data)
        
        # Search for IP/URL patterns
        ip_pattern = re.compile(b'(?:\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3})')
        url_pattern = re.compile(b'https?://[^\s<>\"]+')
        
        found = []
        for s in strings:
            s_str = s.decode('utf-8', errors='replace')
            if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', s_str) or 'http' in s_str.lower():
                found.append(s_str)
        
        if found:
            print(f"  FOUND: {found}")
        else:
            print(f"  No IP/URL found")
            # Show first 500 chars as preview
            text = lua_data[:500].decode('utf-8', errors='replace')
            print(f"  Preview: {text[:300]}")
            
        return len(lua_data)
    except Exception as e:
        print(f"  Error: {e}")
        return 0

# Check all network-related files
files = [
    r'd:\FileD\dota\apk\base\assets\data\network\network.abc',
    r'd:\FileD\dota\apk\base\assets\data\network\network_l.abc',
    r'd:\FileD\dota\apk\base\assets\data\socket\url.abc',
    r'd:\FileD\dota\apk\base\assets\data\socket\http.abc',
    r'd:\FileD\dota\apk\base\assets\data\helloserver\helloserver.abc',
]

for f in files:
    if os.path.exists(f):
        check_file(f)
    else:
        print(f"\n{f} - NOT FOUND")
