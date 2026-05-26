import os
import zipfile

zip_bin_file = "unscrambled_bot2.abc.bin"
output_folder = "bot2_extracted_code"

smart_passwords = [
    "data/bot/bot2",
    "d:/FileD/dota/dgame.app/data/bot/bot2",
    "bot2",
    "data/bot/bot2.abc",
]

if not os.path.exists(zip_bin_file):
    print(f"File not found: {zip_bin_file}")
else:
    print("Trying smart ZIP passwords...")
    success = False

    for pwd in smart_passwords:
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
        print("No smart passwords matched.")
