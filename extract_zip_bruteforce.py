import os
import zipfile

zip_bin_file = "unscrambled_bot2.abc.bin"
output_folder = "bot2_extracted_code"

candidate_passwords = [
    "data",
    "cmto6or!M#@nnsk19",
    "bot2",
    "bot2.abc",
    "dgame",
]

if not os.path.exists(zip_bin_file):
    print(f"File not found: {zip_bin_file}")
else:
    print("Trying candidate ZIP passwords...")
    success = False
    for pwd in candidate_passwords:
        try:
            with zipfile.ZipFile(zip_bin_file, "r") as zip_ref:
                zip_ref.extractall(output_folder, pwd=pwd.encode("utf-8"))
            print(f"SUCCESS: password = '{pwd}'")
            print(f"Output: {output_folder}")
            success = True
            break
        except (RuntimeError, zipfile.BadZipFile) as exc:
            print(f"Password '{pwd}' failed: {exc}")

    if not success:
        print("No candidate passwords matched.")
