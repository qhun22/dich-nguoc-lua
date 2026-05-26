# -*- coding: utf-8 -*-
"""
Phan tich chi tiet cau truc ZIP goc
"""
import os
import sys
import zipfile
import io
import struct

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


def phan_tich_zip(data):
    """Phan tich chi tiet cau truc ZIP."""
    print(f"\nZIP size: {len(data)} bytes")
    
    # Doc header
    sig = data[:4]
    print(f"Signature: {sig.hex()}")
    
    if sig == b'PK\x03\x04':
        # Local file header
        print("\n--- Local File Header ---")
        version = struct.unpack('<H', data[4:6])[0]
        flags = struct.unpack('<H', data[6:8])[0]
        compression = struct.unpack('<H', data[8:10])[0]
        crc = struct.unpack('<I', data[14:18])[0]
        compressed_size = struct.unpack('<I', data[18:22])[0]
        uncompressed_size = struct.unpack('<I', data[22:26])[0]
        filename_len = struct.unpack('<H', data[26:28])[0]
        extra_len = struct.unpack('<H', data[28:30])[0]
        
        print(f"  Version needed: {version}")
        print(f"  General purpose bit flag: {flags} ({bin(flags)})")
        print(f"  Compression method: {compression}")
        print(f"  CRC-32: {crc}")
        print(f"  Compressed size: {compressed_size}")
        print(f"  Uncompressed size: {uncompressed_size}")
        print(f"  Filename length: {filename_len}")
        print(f"  Extra field length: {extra_len}")
        
        filename = data[30:30+filename_len].decode('utf-8')
        print(f"  Filename: '{filename}'")
        
        data_start = 30 + filename_len + extra_len
        compressed_data = data[data_start:data_start + compressed_size]
        
        print(f"\n  Data starts at: {data_start}")
        print(f"  Compressed data size: {len(compressed_data)}")
        print(f"  Compressed data header: {compressed_data[:20].hex()}")
        
        # Check trailing data
        trailing = data[data_start + compressed_size:]
        if trailing:
            print(f"\n  Trailing data: {len(trailing)} bytes")
            print(f"  Trailing: {trailing[:50].hex()}")
        
        return {
            'compressed_data': compressed_data,
            'uncompressed_size': uncompressed_size,
            'compression': compression
        }
    
    return None


def main():
    print("PHAN TICH CHI TIET ZIP GOC")
    print("=" * 60)
    
    # Doc file goc
    with open(ABC_FILE, "rb") as f:
        abc_data = f.read()
    
    print(f"ABC file: {len(abc_data)} bytes")
    
    # Giai ma
    zip_data = descramble_abc(abc_data, FILE_NAME)
    print(f"ZIP data: {len(zip_data)} bytes")
    
    # Phan tich
    info = phan_tich_zip(zip_data)
    
    if info:
        # Thu giai nen
        print("\n--- Giai nen thu ---")
        import zlib
        try:
            decompressed = zlib.decompress(info['compressed_data'])
            print(f"  Giai nen thanh cong: {len(decompressed)} bytes")
        except Exception as e:
            print(f"  Loi: {e}")


if __name__ == "__main__":
    main()
