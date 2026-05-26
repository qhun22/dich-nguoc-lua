"""
Decrypt ipconfig.abc và botpvpserver.abc trong ios/dgame.app/data/bot
In ra network config sau khi giải mã
"""
import os
import sys
import zipfile
import io

BOT_DIR = r"d:\FileD\dota\ios\dgame.app\data\bot"


def descramble_abc(abc_path, name):
    """Stride-10007 descramble + XOR."""
    with open(abc_path, "rb") as f:
        encrypted = f.read()
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
    """Extract ZIP với dynamic password."""
    pwd = f"cocos2d: ERROR: Invalid filename {name}".encode("utf-8")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            return zf.read("data", pwd=pwd)
    except Exception as e:
        print(f"  ZIP error: {e}")
        return None


def extract_strings(data):
    """Extract readable strings from bytecode."""
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


def decrypt_file(name):
    abc_path = os.path.join(BOT_DIR, f"{name}.abc")
    luac_path = os.path.join(BOT_DIR, f"{name}.luac")
    
    print(f"\n{'='*60}")
    print(f"DECRYPTING: {name}.abc")
    print('='*60)
    
    # Step 1: Descramble
    data = descramble_abc(abc_path, name)
    print(f"  Descrambled: {len(data)} bytes")
    
    # Step 2: ZIP extract
    lua_data = extract_zip(data, name)
    if lua_data is None:
        print(f"  FAIL: ZIP extraction failed!")
        return None
    
    print(f"  ZIP extracted: {len(lua_data)} bytes")
    
    # Save .luac
    with open(luac_path, "wb") as f:
        f.write(lua_data)
    
    # Check Lua signature
    if lua_data[:3] == b'\x1bLua':
        print(f"  [OK] Valid Lua 5.1 bytecode")
    
    return lua_data


def find_network_config(lua_data):
    """Tìm thông tin network từ bytecode data."""
    strings = extract_strings(lua_data)
    
    ports = []
    urls = []
    relevant = []
    
    for s in strings:
        # Tìm port numbers
        import re
        port_matches = re.findall(r'\b(\d{4,5})\b', s)
        for p in port_matches:
            port = int(p)
            if 1000 <= port <= 65535 and port not in ports:
                ports.append(port)
        
        # Tìm URLs/hosts
        if 'http' in s.lower() or ('.' in s and '/' in s):
            urls.append(s)
        
        # Tìm strings liên quan network
        keywords = ['server', 'port', 'host', 'ip', 'url', 'connect', 'socket', 
                    'http', 'game', 'login', 'account', 'config', 'address',
                    'data', 'version', 'channel', 'sdk', 'key']
        if any(k in s.lower() for k in keywords):
            relevant.append(s)
    
    return ports, urls, relevant


def main():
    files = ["ipconfig", "botpvpserver"]
    
    print("="*60)
    print("ABC DECRYPTION - Network Config Extraction")
    print("="*60)
    
    all_ports = []
    all_urls = []
    all_relevant = []
    
    for name in files:
        lua_data = decrypt_file(name)
        if lua_data:
            ports, urls, relevant = find_network_config(lua_data)
            all_ports.extend(ports)
            all_urls.extend(urls)
            all_relevant.extend(relevant)
            
            print(f"\n  --- {name.upper()} STRINGS ---")
            for s in relevant[:15]:
                if len(s) < 200:
                    print(f"    {s}")
    
    # Summary
    print(f"\n{'='*60}")
    print("NETWORK CONFIG SUMMARY")
    print('='*60)
    
    if all_ports:
        print(f"\n  PORTS FOUND: {sorted(set(all_ports))}")
    
    if all_urls:
        print(f"\n  URLS/HOSTS:")
        for u in sorted(set(all_urls))[:10]:
            print(f"    {u}")
    
    if all_relevant:
        print(f"\n  ALL RELEVANT STRINGS:")
        for s in sorted(set(all_relevant)):
            if len(s) < 150:
                print(f"    {s}")
    
    print(f"\n  .luac files saved to: {BOT_DIR}")


if __name__ == "__main__":
    main()
