# -*- coding: utf-8 -*-
import zipfile, io

def descramble_abc(data, name):
    size = len(data)
    key = f'{name}.abc'.encode('utf-8')
    key_len = len(key)
    buffer = bytearray(size)
    pos = 0
    for i in range(size):
        dest = pos % size
        buffer[dest] = data[i] ^ key[i % key_len]
        pos += 10007
    return bytes(buffer)

path = r'd:\FileD\dota\ios\dgame.app\data\version.abc'
with open(path, 'rb') as f:
    abc_data = f.read()

zip_data = descramble_abc(abc_data, 'version')

if zip_data[:4] == b'PK\x03\x04':
    zf = zipfile.ZipFile(io.BytesIO(zip_data), 'r')
    pwd = b'cocos2d: ERROR: Invalid filename version'
    for name in zf.namelist():
        content = zf.read(name, pwd=pwd)
        print(f'Lua bytecode ({len(content)} bytes):')

        # Tim cac chuoi trong bytecode
        text = content.decode('latin-1', errors='replace')

        # Hien thi cac constant strings
        print('\nNoi dung text:')
        for i, c in enumerate(text):
            if c.isprintable():
                print(c, end='')
            else:
                print(f'\\x{ord(c):02x}', end='')
        print()

        # Tim cac chuoi nhu version
        print('\n\nTim kiem version:')
        if b'9.9.0' in content:
            print('  Tim thay "9.9.0"!')
        if b'1.0.0103' in content:
            print('  Tim thay "1.0.0103"!')

        # Tim cac chuoi co trong bytecode
        import re
        strings = re.findall(rb'[\x20-\x7e]{3,}', content)
        print('\nCac chuoi tim thay:')
        for s in strings:
            try:
                print(f'  {s.decode("utf-8", errors="replace")}')
            except:
                pass

    zf.close()
