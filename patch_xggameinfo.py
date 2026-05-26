# -*- coding: utf-8 -*-
"""Patch xggameinfo.plist - doi IP tu 192.168.2.2 thanh 192.168.2.111"""
import os
import plistlib
import sys

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

OLD_IP = "192.168.2.2"
NEW_IP = "192.168.2.111"
OLD_URL = f"http://{OLD_IP}:9181"
NEW_URL = f"http://{NEW_IP}:9181"

def patch_plist(plist_path):
    """Doc va patch plist, luu lai."""
    print(f"Doc: {plist_path}")

    with open(plist_path, 'rb') as f:
        data = f.read()

    # Thay the string truc tiep trong binary
    if OLD_URL.encode('utf-8') in data:
        data = data.replace(OLD_URL.encode('utf-8'), NEW_URL.encode('utf-8'))
        print(f"  Da thay '{OLD_URL}' -> '{NEW_URL}'")

        with open(plist_path, 'wb') as f:
            f.write(data)
        print(f"  Da luu!")
        return True
    elif NEW_URL.encode('utf-8') in data:
        print(f"  URL da la: '{NEW_URL}'")
        return True
    else:
        print(f"  [LOI] Khong tim thay URL!")
        return False

if __name__ == "__main__":
    plists = [
        r"d:\FileD\dota\ios\dgame.app\xggameinfo.plist",
        r"d:\FileD\dota\ios\Payload\dgame.app\xggameinfo.plist",
    ]

    for plist in plists:
        if os.path.exists(plist):
            patch_plist(plist)
        else:
            print(f"[LOI] Khong tim thay: {plist}")
