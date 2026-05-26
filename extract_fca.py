import argparse
import json
import os
import plistlib
import struct
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class BoneEntry:
    name: str
    sprite: str
    index: int


@dataclass
class AnimEntry:
    name: str
    offset: int
    fps: Optional[float]
    track_count: Optional[int]
    size: Optional[int]


def read_u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def read_f32(data: bytes, offset: int) -> float:
    return struct.unpack_from("<f", data, offset)[0]


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def sanitize_filename(name: str) -> str:
    # Windows-invalid characters: <>:"/\\|?*
    invalid = '<>:"/\\|?*'
    cleaned = "".join((ch if ch not in invalid else "_") for ch in name)
    cleaned = cleaned.strip().strip(".")
    return cleaned or "unnamed"


def parse_rect(val) -> Optional[Tuple[float, float, float, float]]:
    # TexturePacker-style string: "{{x,y},{w,h}}" or "{x,y,w,h}"
    if isinstance(val, str):
        s = val.replace("{", "").replace("}", "")
        parts = [p.strip() for p in s.split(",") if p.strip()]
        if len(parts) == 4:
            try:
                return tuple(float(p) for p in parts)  # type: ignore
            except ValueError:
                return None
    if isinstance(val, dict):
        # Some plists store as dict with keys x,y,width,height
        keys = ["x", "y", "width", "height"]
        if all(k in val for k in keys):
            return (float(val["x"]), float(val["y"]), float(val["width"]), float(val["height"]))
    return None


def convert_pvr_to_png(pvr_path: str, png_path: str) -> bool:
    # Use PVRTexToolCLI if available on PATH.
    candidates = ["PVRTexToolCLI", "PVRTexToolCLI.exe", "PVRTexTool", "PVRTexTool.exe"]
    tool = next((c for c in candidates if shutil_which(c)), None)
    if not tool:
        return False
    cmd = [tool, "-i", pvr_path, "-o", png_path]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False


def shutil_which(cmd: str) -> Optional[str]:
    # Avoid importing shutil to keep dependencies minimal and predictable.
    path = os.environ.get("PATH", "")
    for entry in path.split(os.pathsep):
        candidate = os.path.join(entry, cmd)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


def parse_cha(data: bytes) -> Tuple[str, List[BoneEntry], int]:
    # Format (observed):
    # u32 name_len, bytes name
    # u32 bone_count
    # repeated bone_count:
    #   u32 bone_name_len, bytes bone_name
    #   u32 sprite_name_len, bytes sprite_name
    #   u32 index (1..bone_count)
    o = 0
    name_len = read_u32(data, o)
    o += 4
    name = data[o:o + name_len].decode("ascii", errors="ignore")
    o += name_len
    bone_count = read_u32(data, o)
    o += 4

    bones: List[BoneEntry] = []
    for _ in range(bone_count):
        ln1 = read_u32(data, o)
        o += 4
        bname = data[o:o + ln1].decode("ascii", errors="ignore")
        o += ln1
        ln2 = read_u32(data, o)
        o += 4
        sname = data[o:o + ln2].decode("ascii", errors="ignore")
        o += ln2
        idx = read_u32(data, o)
        o += 4
        bones.append(BoneEntry(bname, sname, idx))

    return name, bones, o


def scan_anim_names(data: bytes, start_offset: int) -> List[Tuple[int, str]]:
    # Scan for length-prefixed ASCII strings after the bone list.
    results: List[Tuple[int, str]] = []
    for off in range(start_offset, len(data) - 8):
        ln = read_u32(data, off)
        if 0 < ln < 64 and off + 4 + ln <= len(data):
            s = data[off + 4:off + 4 + ln]
            if all(32 <= b <= 126 for b in s):
                results.append((off, s.decode("ascii", errors="ignore")))
    # de-dup by offset
    seen = set()
    deduped = []
    for off, s in results:
        if off not in seen:
            seen.add(off)
            deduped.append((off, s))
    return deduped


def collect_anim_entries(data: bytes, start_offset: int, bone_names: set) -> List[AnimEntry]:
    # Filter strings into animation names (exclude bones and .mp3 sound names).
    strings = scan_anim_names(data, start_offset)
    anims = []
    for off, s in strings:
        if s.endswith(".mp3"):
            continue
        if s in bone_names:
            continue
        # common animation labels are short; keep all strings after start
        anims.append((off, s))

    # keep only sorted unique names by first occurrence
    anims_sorted = []
    seen_names = set()
    for off, s in sorted(anims, key=lambda x: x[0]):
        if s not in seen_names:
            anims_sorted.append((off, s))
            seen_names.add(s)

    entries: List[AnimEntry] = []
    for i, (off, name) in enumerate(anims_sorted):
        # try to read fps and track count
        fps = None
        track_count = None
        try:
            ln = read_u32(data, off)
            if ln == len(name):
                pos = off + 4 + ln
                fps = read_f32(data, pos)
                track_count = read_u32(data, pos + 4)
        except Exception:
            pass

        next_off = anims_sorted[i + 1][0] if i + 1 < len(anims_sorted) else None
        size = (next_off - off) if next_off is not None else None
        entries.append(AnimEntry(name, off, fps, track_count, size))

    return entries


def extract_fca(fca_path: str, out_dir: str) -> None:
    ensure_dir(out_dir)
    with zipfile.ZipFile(fca_path, "r") as z:
        names = z.namelist()
        for n in names:
            out_path = os.path.join(out_dir, n)
            ensure_dir(os.path.dirname(out_path))
            with z.open(n) as src, open(out_path, "wb") as dst:
                dst.write(src.read())

    # Parse plist frames
    plist_path = os.path.join(out_dir, "plist")
    atlas_json = os.path.join(out_dir, "atlas.json")
    if os.path.exists(plist_path):
        with open(plist_path, "rb") as f:
            pl = plistlib.load(f)
        frames = pl.get("frames", {}) if isinstance(pl, dict) else {}
        atlas = {}
        for frame_name, info in frames.items():
            rect = None
            if isinstance(info, dict):
                rect = parse_rect(info.get("frame") or info.get("textureRect"))
            atlas[frame_name] = {"rect": rect, "raw": info}
        with open(atlas_json, "w", encoding="utf-8") as f:
            json.dump(atlas, f, ensure_ascii=True, indent=2)

    # Convert sheet.pvr to PNG if PVRTexToolCLI is available
    pvr_path = os.path.join(out_dir, "sheet.pvr")
    if os.path.exists(pvr_path):
        png_path = os.path.join(out_dir, "sheet.png")
        if convert_pvr_to_png(pvr_path, png_path):
            print("Converted sheet.pvr -> sheet.png")
        else:
            print("PVRTexToolCLI not found; kept sheet.pvr")

    # Parse cha (bones + animations)
    cha_path = os.path.join(out_dir, "cha")
    if os.path.exists(cha_path):
        data = open(cha_path, "rb").read()
        char_name, bones, anim_start = parse_cha(data)
        bone_json = os.path.join(out_dir, "bones.json")
        with open(bone_json, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "character": char_name,
                    "bone_count": len(bones),
                    "bones": [b.__dict__ for b in bones],
                },
                f,
                ensure_ascii=True,
                indent=2,
            )

        bone_names = {b.name for b in bones}
        anim_entries = collect_anim_entries(data, anim_start, bone_names)
        anim_json = os.path.join(out_dir, "animations.json")
        with open(anim_json, "w", encoding="utf-8") as f:
            json.dump(
                [
                    {
                        "name": a.name,
                        "offset": a.offset,
                        "fps": a.fps,
                        "track_count": a.track_count,
                        "size": a.size,
                    }
                    for a in anim_entries
                ],
                f,
                ensure_ascii=True,
                indent=2,
            )

        # Dump raw animation blocks for further reverse engineering
        anim_dir = os.path.join(out_dir, "anim_blocks")
        ensure_dir(anim_dir)
        for i, a in enumerate(anim_entries):
            next_off = anim_entries[i + 1].offset if i + 1 < len(anim_entries) else len(data)
            block = data[a.offset:next_off]
            safe_name = sanitize_filename(a.name)
            with open(os.path.join(anim_dir, f"{safe_name}.bin"), "wb") as f:
                f.write(block)


def main() -> int:
    ap = argparse.ArgumentParser(description="Extract .fca (zip) contents and dump atlas/bone info.")
    ap.add_argument("fca", help="Path to .fca file")
    ap.add_argument("-o", "--out", help="Output directory", default=None)
    args = ap.parse_args()

    fca_path = os.path.abspath(args.fca)
    if not os.path.isfile(fca_path):
        print("Input file not found:", fca_path)
        return 2

    out_dir = args.out or (fca_path + "_out")
    extract_fca(fca_path, out_dir)
    print("Done. Output:", out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
