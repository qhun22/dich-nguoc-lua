# -*- coding: utf-8 -*-
import re

# Read AndroidManifest
with open(r'd:\FileD\dota\apk\base\AndroidManifest.xml', 'rb') as f:
    data = f.read()

# Try UTF-16 decode
try:
    text = data.decode('utf-16')
except:
    text = data.decode('utf-8', errors='ignore')

# Find icon references
pattern = r'@mipmap/([^\s"]+)|@drawable/([^\s"]+)'
icons = re.findall(pattern, text)

print('Icon references in AndroidManifest:')
for match in icons:
    for g in match:
        if g:
            print(f'  @mipmap/{g}' if '@mipmap' not in g else f'  @{g}')

print()
print('Checking if mipmap directories exist...')

import os
for root, dirs, files in os.walk(r'd:\FileD\dota\apk\base\res'):
    if 'mipmap' in root.lower():
        print(f'Found: {root}')
        for f in files[:5]:
            print(f'  {f}')
