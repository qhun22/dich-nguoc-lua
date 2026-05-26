# -*- coding: utf-8 -*-
"""
Debug chi tiet thuat toan scramble bang cach so sanh byte-by-byte
"""
import os
import sys
import zipfile
import io

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

FILE_NAME = "ipconfig"
ABC_FILE = r"d:\FileD\dota\apk\base\assets\data\bot\ipconfig.abc"


def descramble_abc(encrypted, name):
    size = len(encrypted)
    buffer = bytearray(size)
    key = f"{name}.abc".encode('utf-8')
    key_len = len(key)
    pos = 0
    for i in range(size):
        dest = pos % size
        buffer[dest] = encrypted[i] ^ key[i % key_len]
        pos += 10007
    return bytes(buffer)


def scramble_thu1(data, name):
    """Cach 1: dest = (i * stride) % size, ghi data[i]."""
    size = len(data)
    key = f"{name}.abc".encode('utf-8')
    key_len = len(key)
    stride = 10007
    
    encrypted = bytearray(size)
    for i in range(size):
        dest = (i * stride) % size
        encrypted[i] = data[i] ^ key[i % key_len]
    
    return bytes(encrypted)


def scramble_thu2(data, name):
    """Cach 2: dest = (i * stride) % size, ghi data[i] vao dest."""
    size = len(data)
    key = f"{name}.abc".encode('utf-8')
    key_len = len(key)
    stride = 10007
    
    encrypted = bytearray(size)
    for i in range(size):
        dest = (i * stride) % size
        encrypted[dest] = data[i] ^ key[i % key_len]
    
    return bytes(encrypted)


def scramble_thu3(data, name):
    """Cach 3: nhu descramble nhung dao nguoc vong lap."""
    size = len(data)
    key = f"{name}.abc".encode('utf-8')
    key_len = len(key)
    stride = 10007
    
    encrypted = bytearray(size)
    pos = 0
    for i in range(size):
        dest = pos % size
        encrypted[i] = data[dest] ^ key[dest % key_len]
        pos += stride
    
    return bytes(encrypted)


def main():
    print("DEBUG SCRAMBLE CHI TIET")
    print("=" * 60)
    
    # Doc file goc
    with open(ABC_FILE, "rb") as f:
        original = f.read()
    
    print(f"Original .abc: {len(original)} bytes")
    print(f"First 32 bytes: {original[:32].hex()}")
    
    # Giai ma
    decrypted = descramble_abc(original, FILE_NAME)
    print(f"\nDescrambled: {len(decrypted)} bytes")
    print(f"First 32 bytes: {decrypted[:32].hex()}")
    
    # Thu cac cach scramble
    for name, func in [("Cach 1", scramble_thu1), ("Cach 2", scramble_thu2), ("Cach 3", scramble_thu3)]:
        result = func(decrypted, FILE_NAME)
        match = result == original
        
        print(f"\n{name}:")
        print(f"  Result: {len(result)} bytes")
        print(f"  First 32 bytes: {result[:32].hex()}")
        print(f"  Match original: {match}")
        
        if not match:
            # Tim byte dau tien khac nhau
            for i in range(min(50, len(result))):
                if i < len(original) and result[i] != original[i]:
                    print(f"  Byte {i}: result={result[i]:02x}, original={original[i]:02x}")
                    break


if __name__ == "__main__":
    main()
