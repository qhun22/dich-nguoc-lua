# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'd:\FileD\dota\ios\dgame.app\Info.plist'
with open(path, 'rb') as f:
    data = f.read()

# Tim cac chuoi trong binary plist
text = data.decode('latin-1', errors='replace')

# Tim version
import re
strings = re.findall(r'[\x20-\x7e]{2,}', text)
for s in strings:
    if 'version' in s.lower() or '9.9' in s:
        print(s)
