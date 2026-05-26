# -*- coding: utf-8 -*-
"""Tim kiem versionStr trong binary"""
import re

path = r'd:\FileD\dota\ios\dgame.app\dgame'

with open(path, 'rb') as f:
    data = f.read()

print(f'Kich thuoc: {len(data)} bytes')

# Tim tat ca cac chuoi co format nhu version
# Tim chuoi "9.x.x" hoac "X.X.X" gan versionStr
search_terms = [
    b'9.9.0',
    b'9.0.0',
    b'versionStr',
    b'version',
]

for term in search_terms:
    count = data.count(term)
    print(f'\n"{term.decode()}" xuat hien {count} lan')
    if count > 0 and count < 20:
        pos = 0
        for i in range(count):
            pos = data.find(term, pos)
            if pos == -1:
                break
            start = max(0, pos - 30)
            end = min(len(data), pos + len(term) + 30)
            context = data[start:end]
            print(f'  Pos {pos}: {context.hex()[:80]}...')
            pos += 1

# Tim cac chuoi dai hon co the la version
print('\n\nTim cac chuoi nhu "X.X.X":')
pattern = rb'["\x00][0-9]\.[0-9]\.[0-9]+["\x00]'
matches = list(re.finditer(pattern, data))
for m in matches[:10]:
    pos = m.start()
    s = m.group()
    print(f'  Pos {pos}: {s}')
