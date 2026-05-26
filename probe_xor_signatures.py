#!/usr/bin/env python3
"""
probe_xor_signatures.py - XOR Brute-force & Compression Signature Finder
=======================================================================
Tac gia: Reverse Engineering Tool
Ngay: 2026-05-21

Chuc nang: Brute-force giai ma XOR 1-byte tren phan Payload cua file .bin,
           nham tim kiem dau vet cac tep tin bi nen an (zlib, gzip, lz4...)

Cach su dung:
    python probe_xor_signatures.py <duong_dan_file.bin> [offset_payload]

Vi du:
    python probe_xor_signatures.py Idle.bin
    python probe_xor_signatures.py Idle.bin 24
"""

import sys
import zlib
import os
from pathlib import Path

# Compression signatures to detect
COMPRESSION_SIGNATURES = {
    "ZLIB_7801": bytes([0x78, 0x01]),
    "ZLIB_789C": bytes([0x78, 0x9C]),
    "ZLIB_78DA": bytes([0x78, 0xDA]),
    "GZIP": bytes([0x1F, 0x8B]),
    "LZ4": bytes([0x04, 0x22, 0x4D, 0x18]),
    "ZSTD": bytes([0x28, 0xB5, 0x2F, 0xFD]),
}


def check_signatures(data):
    """Kiem tra xem data co chua chu ky nen nao khong"""
    found = []
    for name, sig in COMPRESSION_SIGNATURES.items():
        if data[:len(sig)] == sig:
            found.append(name)
    return found


def try_zlib_decompress(data):
    """Thu giai nen voi cac thuat toan khac nhau"""
    for wbits in [15, -15, 15 + 32, 31, -31, 47]:
        try:
            result = zlib.decompress(data, wbits)
            return True, result, f"zlib (wbits={wbits})"
        except:
            pass
    return False, None, None


def entropy_analysis(data):
    """Tinh entropy de phan biet encrypted vs compressed"""
    from math import log2
    freq = [0] * 256
    for b in data:
        freq[b] += 1
    entropy = 0
    for f in freq:
        if f > 0:
            p = f / len(data)
            entropy -= p * log2(p)
    return entropy


def xor_probe_file(filepath, payload_offset=24):
    """
    Thuc hien XOR brute-force tren file.

    Args:
        filepath: Duong dan den file .bin
        payload_offset: Offset bat dau phan Payload (mac dinh 24)

    Returns:
        dict chua ket qua
    """
    print(f"\n{'='*60}")
    print(f"ANALYZING: {os.path.basename(filepath)}")
    print(f"{'='*60}")

    try:
        with open(filepath, "rb") as f:
            file_data = f.read()
    except Exception as e:
        print(f"[!] Read error: {e}")
        return None

    file_size = len(file_data)
    print(f"[+] File size: {file_size} bytes")
    print(f"[+] Entropy: {entropy_analysis(file_data):.4f}")
    print(f"    (7.0-8.0 = encrypted/random, ~6.0 = compressed/numeric data)")

    # Xu ly payload
    if payload_offset >= file_size:
        print(f"[!] Offset {payload_offset} vuot qua kich thuoc file")
        return None

    payload = file_data[payload_offset:]

    # Brute-force 256 keys
    candidates = []
    for key in range(256):
        decrypted = bytes([b ^ key for b in payload])
        found_sigs = check_signatures(decrypted)

        if found_sigs:
            print(f"[!] KEY = 0x{key:02X} -> {', '.join(found_sigs)}")
            candidates.append({
                "key": key,
                "decrypted": decrypted,
                "signatures": found_sigs,
            })

            # Thu giai nen
            success, decompressed, algo = try_zlib_decompress(decrypted)
            if success:
                output = Path(filepath).stem + "_unlocked.bin"
                with open(output, "wb") as f:
                    f.write(decompressed)
                print(f"[***] SUCCESS! -> {output} ({len(decompressed)} bytes)")
                return key

    if not candidates:
        print(f"[-] No XOR key found with offset {payload_offset}")

    return None


def main():
    anim_dir = Path("d:/FileD/dota/ios/dgame.app/pfca/TitanPA.fca_out/anim_blocks")

    print("*" * 60)
    print("XOR BRUTE-FORCE & COMPRESSION SIGNATURE FINDER")
    print("*" * 60)

    # Su dung Idle.bin lam vi du
    idle_file = anim_dir / "Idle.bin"

    if not idle_file.exists():
        print(f"[!] Idle.bin not found at {idle_file}")
        return

    # Thu cac payload offsets khac nhau
    result = xor_probe_file(str(idle_file), payload_offset=24)

    if result is None:
        # Thu offset khac
        for offset in [16, 20, 28, 32, 36]:
            result = xor_probe_file(str(idle_file), payload_offset=offset)
            if result is not None:
                break

    if result is not None:
        print(f"\n[***] FOUND KEY = 0x{result:02X}! Decrypting all files...")


if __name__ == "__main__":
    main()
