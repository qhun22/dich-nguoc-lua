import os
import sys
import quicklz


def decompress_abc_file(input_path, output_path, max_prefix=256):
    if not os.path.exists(input_path):
        print(f"File not found: {input_path}")
        return

    print(f"Decompressing QuickLZ file {input_path}...")

    with open(input_path, "rb") as f:
        compressed_data = f.read()

    last_error = None
    for prefix in range(0, max_prefix + 1):
        try:
            decompressed_data = quicklz.decompress(compressed_data[prefix:])

            with open(output_path, "wb") as f:
                f.write(decompressed_data)

            print(f"Decompressed output: {output_path}")
            print(f"Used prefix offset: {prefix} bytes")
            return
        except Exception as exc:
            last_error = exc

    print(f"Decompression error: {last_error}")
    print(f"Tip: No valid QuickLZ stream found in first {max_prefix} bytes.")


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, "bot2.abc")
    output_path = os.path.join(script_dir, "bot2_source_code.txt")

    if len(sys.argv) >= 2:
        input_path = sys.argv[1]
        if len(sys.argv) >= 3:
            output_path = sys.argv[2]
        else:
            base = os.path.splitext(os.path.basename(input_path))[0]
            output_path = os.path.join(script_dir, f"{base}_source_code.txt")

    decompress_abc_file(input_path, output_path)
