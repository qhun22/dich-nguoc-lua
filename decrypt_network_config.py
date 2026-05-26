"""
Decrypt ipconfig.abc và botpvpserver.abc trong ios/dgame.app/data/bot
"""
import os
import sys
import zipfile
import io

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

BOT_DIR = r"d:\FileD\dota\ios\dgame.app\data\bot"


def descramble_abc(encrypted, name):
    size = len(encrypted)
    buffer = bytearray(size)
    key = f"{name}.abc".encode("utf-8")
    key_len = len(key)
    pos = 0
    for i in range(size):
        dest = pos % size
        buffer[dest] = encrypted[i] ^ key[i % key_len]
        pos += 10007
    return bytes(buffer)


def extract_zip(data, name):
    pwd = f"cocos2d: ERROR: Invalid filename {name}".encode("utf-8")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            return zf.read("data", pwd=pwd)
    except Exception as e:
        print(f"  ZIP error: {e}")
        return None


def bytes_to_readable_strings(data):
    """Extract printable strings from bytecode."""
    strings = []
    current = []
    
    for byte in data:
        if 32 <= byte < 127:
            current.append(chr(byte))
        else:
            if len(current) >= 4:
                strings.append(''.join(current))
            current = []
    
    if len(current) >= 4:
        strings.append(''.join(current))
    
    return strings


def find_network_strings(data):
    """Tìm strings liên quan đến network/server."""
    strings = bytes_to_readable_strings(data)
    keywords = ['server', 'port', 'host', 'ip', 'url', 'connect', 'socket', 
                'http', 'game', 'login', 'account', 'config', 'address']
    
    results = []
    for s in strings:
        s_lower = s.lower()
        if any(k in s_lower for k in keywords):
            results.append(s)
        # Tìm các string có dạng URL hoặc IP
        if ('.' in s and '/' in s) or s.startswith('http'):
            results.append(s)
    
    return results


def decrypt_and_analyze(name):
    abc_path = os.path.join(BOT_DIR, f"{name}.abc")
    luac_path = os.path.join(BOT_DIR, f"{name}.luac")
    
    print(f"\n{'='*60}")
    print(f"DECRYPTING: {name}.abc")
    print('='*60)
    
    # Step 1: Read encrypted
    with open(abc_path, "rb") as f:
        encrypted = f.read()
    print(f"  Encrypted size: {len(encrypted)} bytes")
    
    # Step 2: Descramble
    data = descramble_abc(encrypted, name)
    print(f"  Descrambled: {len(data)} bytes")
    
    # Step 3: ZIP extract
    lua_data = extract_zip(data, name)
    if lua_data is None:
        print(f"  FAIL: ZIP extraction failed!")
        return None
    
    print(f"  ZIP extracted: {len(lua_data)} bytes")
    
    # Save .luac
    with open(luac_path, "wb") as f:
        f.write(lua_data)
    print(f"  Saved: {luac_path}")
    
    # Check Lua bytecode signature
    if lua_data[:3] == b'\x1bLua':
        print(f"  [OK] Valid Lua 5.1 bytecode")
    else:
        print(f"  [WARN] Not standard Lua bytecode")
    
    # Step 4: Find network strings
    print(f"\n  --- NETWORK INFO STRINGS ---")
    network_strings = find_network_strings(lua_data)
    for s in network_strings[:20]:
        if len(s) < 200:
            print(f"    {s}")
    
    # Also print ALL strings for analysis
    print(f"\n  --- ALL READABLE STRINGS ---")
    all_strings = bytes_to_readable_strings(lua_data)
    for s in all_strings[:50]:
        if len(s) > 2:
            print(f"    {s}")
    
    return lua_data


def main():
    files = ["ipconfig", "botpvpserver"]
    
    print("="*60)
    print("ABC DECRYPTION - Network Config Analysis")
    print("="*60)
    
    for name in files:
        decrypt_and_analyze(name)
    
    print(f"\n{'='*60}")
    print("Done! .luac files saved to:")
    print(f"  {BOT_DIR}")


if __name__ == "__main__":
    main()
