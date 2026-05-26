# -*- coding: utf-8 -*-
"""Thay the print thanh _log_request trong views.py"""
import re

path = r"d:\FileD\dota\auth_system\views.py"

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Lưu lại nội dung cũ để thay thế từng phần
# Thay pattern: print("\n=== /xxx ===") va print(json.dumps(...))

# Tìm và thay thế tất cả các khối log
# Pattern 1: print("\n=== ... ===\n") followed by print(json.dumps(...))

pattern = r'print\("\\n=== (\[^"\]+) ===\\n"\)\s*\n\s*print\(json\.dumps\(payload, ensure_ascii=False, indent=2\)\)'

def replacer1(m):
    endpoint = m.group(1)
    return f'_log_request("/{endpoint}", payload)'

content = re.sub(pattern, replacer1, content)

# Pattern 2: print("\n=== /xxx ===\n") -> _log_request("/xxx", ...)
content = re.sub(
    r'print\("\\\\n=== (\[^"\]+) ===\\\\n"\)(?!\s*_log_request)',
    lambda m: f'_log_request("/{m.group(1)}", payload)',
    content
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Da thay the xong!")
