# -*- coding: utf-8 -*-
import os

# Search for app name in assets
assets_dir = r'd:\FileD\dota\apk\base\assets'

print('Searching for app name references...')

keywords = ['tmgame', '99 dota', 'truyen ky', 'truyền kỳ', '7 sao', 'game99', 'DotaTruyenKy']

for root, dirs, files in os.walk(assets_dir):
    for f in files:
        path = os.path.join(root, f)
        try:
            with open(path, 'rb') as file:
                content = file.read()
                text = content.decode('utf-8', errors='ignore')
                for kw in keywords:
                    if kw.lower() in text.lower():
                        rel = os.path.relpath(path, assets_dir)
                        print(f'Found "{kw}" in: {rel}')
        except:
            pass

print('\nDone!')
