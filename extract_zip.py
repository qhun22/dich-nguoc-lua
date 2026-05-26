import os
import zipfile

zip_bin_file = "unscrambled_bot2.abc.bin"
output_folder = "bot2_extracted_code"

if not os.path.exists(zip_bin_file):
    print(f"File not found: {zip_bin_file}")
else:
    print(f"Extracting ZIP from '{zip_bin_file}'...")
    try:
        with zipfile.ZipFile(zip_bin_file, "r") as zip_ref:
            zip_ref.extractall(output_folder)
        print(f"Extracted to: {output_folder}")
    except Exception as exc:
        print(f"Extraction error: {exc}")
        print("Tip: If this fails, we may need to trim junk bytes.")
