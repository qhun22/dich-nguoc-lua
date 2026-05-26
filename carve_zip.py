import os


def find_all(data, needle):
    offsets = []
    start = 0
    while True:
        idx = data.find(needle, start)
        if idx == -1:
            break
        offsets.append(idx)
        start = idx + 1
    return offsets


def carve_zip(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"File not found: {input_path}")
        return

    with open(input_path, "rb") as f:
        data = f.read()

    local_sig = b"PK\x03\x04"
    central_sig = b"PK\x01\x02"
    eocd_sig = b"PK\x05\x06"

    local_offsets = find_all(data, local_sig)
    central_offsets = find_all(data, central_sig)
    eocd_offsets = find_all(data, eocd_sig)

    print(f"Local headers: {len(local_offsets)}")
    print(f"Central dir headers: {len(central_offsets)}")
    print(f"EOCD headers: {len(eocd_offsets)}")

    if not local_offsets:
        print("No ZIP local header found.")
        return

    if eocd_offsets:
        zip_start = local_offsets[0]
        zip_end = eocd_offsets[-1] + 22
        zip_blob = data[zip_start:zip_end]
        with open(output_path, "wb") as f:
            f.write(zip_blob)
        print(f"Carved ZIP: {output_path}")
        print(f"Range: {zip_start}-{zip_end} ({len(zip_blob)} bytes)")
        return

    # Fallback: carve from first local header to end of file
    zip_start = local_offsets[0]
    zip_blob = data[zip_start:]
    with open(output_path, "wb") as f:
        f.write(zip_blob)
    print(f"Carved ZIP (no EOCD): {output_path}")
    print(f"Range: {zip_start}-{len(data)} ({len(zip_blob)} bytes)")


if __name__ == "__main__":
    carve_zip("unscrambled_bot2.abc.bin", "carved_bot2.zip")
