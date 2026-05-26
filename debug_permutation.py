# -*- coding: utf-8 -*-
"""
Debug chi tiet: Tinh toan permutation va kiem tra XOR
"""
import os
import sys

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


def main():
    print("DEBUG SCRAMBLE: TIM PERMUTATION")
    print("=" * 60)
    
    # Doc file goc
    with open(ABC_FILE, "rb") as f:
        encrypted = f.read()
    
    # Giai ma
    decrypted = descramble_abc(encrypted, FILE_NAME)
    
    size = len(encrypted)
    key = f"{FILE_NAME}.abc".encode('utf-8')
    key_len = len(key)
    
    print(f"\nSize: {size}")
    print(f"Key: {key}")
    
    # Tinh permutation
    print("\nTinh permutation cua descramble:")
    print("  descramble: decrypted[dest] = encrypted[i] XOR key[i % key_len]")
    print("  dest = pos % size, pos += 10007")
    
    perm = {}
    pos = 0
    for i in range(size):
        dest = pos % size
        perm[dest] = i  # reversed: i = perm[dest]
        pos += 10007
    
    # Hien thi permutation cua 10 byte dau tien
    print("\nPermutation (dest -> i):")
    for dest in range(min(10, size)):
        i = perm.get(dest, -1)
        enc_byte = encrypted[i] if i >= 0 else -1
        dec_byte = decrypted[dest]
        key_byte = key[i % key_len] if i >= 0 else -1
        enc_str = f"{enc_byte:02x}" if i >= 0 else "?"
        key_str = f"{key_byte:02x}" if i >= 0 else "?"
        print(f"  dest={dest}: i={i}, encrypted={enc_str}, key={key_str}")
        if i >= 0:
            calc = enc_byte ^ key_byte
            print(f"         {enc_str} XOR {key_str} = {calc:02x}, decrypted={dec_byte:02x}, match={calc == dec_byte}")
    
    # Thu scramble chinh xac
    print("\n" + "=" * 60)
    print("THU SCRAMBLE VOI PERMUTATION")
    print("=" * 60)
    
    print("\nScramble: encrypted[i] = decrypted[dest] XOR key[i % key_len]")
    print("          dest = perm[i] (tuong ung voi thu tu ghi trong descramble)")
    
    # Tim permutation thuan (i -> dest)
    perm_forward = {}
    pos = 0
    for i in range(size):
        dest = pos % size
        perm_forward[i] = dest
        pos += 10007
    
    # Tao encrypted
    result = bytearray(size)
    for i in range(size):
        dest = perm_forward[i]
        result[i] = decrypted[dest] ^ key[i % key_len]
    
    print(f"\nScrambled: {result[:10].hex()}")
    print(f"Original:  {encrypted[:10].hex()}")
    print(f"Match: {bytes(result) == encrypted}")
    
    if bytes(result) != encrypted:
        print("\nByte khac nhau dau tien:")
        for i in range(min(20, size)):
            if result[i] != encrypted[i]:
                print(f"  Byte {i}: result={result[i]:02x}, original={encrypted[i]:02x}")
                break


if __name__ == "__main__":
    main()
