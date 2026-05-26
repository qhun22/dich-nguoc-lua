import json

# Manual mappings based on analysis
mappings = {
    # Knowns from bot2.abc / ai.abc pseudo
    54: 'SETTABLE',
    44: 'SETTABLE',
    42: 'GETTABLE',
    56: 'GETTABLE',
    61: 'GETTABLE',
    57: 'CLOSURE',
    63: 'NEWTABLE',
    34: 'JMP',
    28: 'RETURN',
    49: 'RETURN',
    50: 'TEST',
    24: 'GETGLOBAL',
    # Others need guessing.
}

# If I can just write an opmap that forces unluac to output ANYTHING,
# I will see if unluac decompiles without throwing Exception!
# For any unmapped opcode, I will map it to a harmless instruction like MOVE
for i in range(64):
    if i not in mappings:
        mappings[i] = 'MOVE' # dummy

with open('battle.map', 'w') as f:
    for op, name in mappings.items():
        f.write(f".op {op} {name}\n")
