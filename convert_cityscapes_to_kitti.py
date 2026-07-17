#!/usr/bin/env python3
"""Convert Cityscapes leftImg8bit/gtBbox3d to a KITTI-style dataset.

The generated labels use KITTI camera coordinates (X right, Y down, Z forward).
Cityscapes ISO8855 coordinates are converted as X=-y, Y=-z, Z=x.
"""
import argparse
import json
import math
import os
from pathlib import Path
import shutil


CLASS_MAP = {
    "car": "Car", "truck": "Truck", "bus": "Bus", "train": "Train",
    "motorcycle": "Motorcycle", "bicycle": "Cyclist", "person": "Pedestrian",
    "rider": "Cyclist",
}


def yaw_from_xyzw(q):
    x, y, z, w = [float(v) for v in q]
    r00 = 1.0 - 2.0 * (y * y + z * z)
    r10 = 2.0 * (x * y + z * w)
    return math.atan2(r10, r00)


def link_or_copy(src, dst, copy_images):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        return
    if copy_images:
        shutil.copy2(src, dst)
    else:
        dst.symlink_to(os.path.relpath(src, dst.parent))


def kitti_label(obj):
    label = CLASS_MAP.get(obj.get("label", ""))
    if not label or "3d" not in obj or "2d" not in obj:
        return None
    box = obj["2d"].get("amodal") or obj["2d"].get("modal")
    if not box or len(box) != 4:
        return None
    left, top, width, height = map(float, box)
    x1, y1, x2, y2 = left, top, left + width, top + height
    d = obj["3d"]
    center = list(map(float, d.get("center", [0, 0, 0])))
    dims = list(map(float, d.get("dimensions", [0, 0, 0])))
    if len(center) != 3 or len(dims) != 3:
        return None
    # ISO8855: (forward, left, up), KITTI: (right, down, forward).
    tx, ty, tz = -center[1], -center[2], center[0]
    h, w, l = dims[2], dims[1], dims[0]
    ry = yaw_from_xyzw(d.get("rotation", [0, 0, 0, 1]))
    trunc = min(1.0, max(0.0, float(obj.get("truncation", 0.0))))
    occ = int(min(3, max(0, round(float(obj.get("occlusion", 0.0)) * 3))))
    height_px = y2 - y1
    if height_px >= 40 and occ <= 0 and trunc <= 0.15:
        diff = 0
    elif height_px >= 25 and occ <= 1 and trunc <= 0.3:
        diff = 1
    elif height_px >= 25:
        diff = 2
    else:
        diff = 3
    return f"{label} {trunc:.2f} {occ} {ry:.6f} {x1:.2f} {y1:.2f} {x2:.2f} {y2:.2f} {h:.3f} {w:.3f} {l:.3f} {tx:.3f} {ty:.3f} {tz:.3f} {ry:.6f}"


def convert(src, dst, copy_images=False):
    src = Path(src).resolve()
    dst = Path(dst)
    for split in ("train", "val", "test"):
        for kind in ("image_2", "label_2", "calib"):
            directory = dst / split / kind
            directory.mkdir(parents=True, exist_ok=True)
            for old_file in directory.iterdir():
                if old_file.is_file() or old_file.is_symlink():
                    old_file.unlink()
        (dst / "ImageSets").mkdir(parents=True, exist_ok=True)
        ids = []
        for image in sorted((src / "leftImg8bit" / split).glob("*/*_leftImg8bit.png")):
            stem = image.name[:-len("_leftImg8bit.png")]
            sample_id = f"{len(ids):06d}"
            ids.append(sample_id)
            link_or_copy(image, dst / split / "image_2" / f"{sample_id}.png", copy_images)
            ann = src / "gtBbox3d" / split / image.parent.name / f"{stem}_gtBbox3d.json"
            objects = []
            sensor = {}
            if ann.exists():
                with ann.open() as f:
                    data = json.load(f)
                sensor = data.get("sensor", {})
                objects = [line for obj in data.get("objects", []) if (line := kitti_label(obj))]
            (dst / split / "label_2" / f"{sample_id}.txt").write_text("\n".join(objects) + ("\n" if objects else ""))
            fx, fy = float(sensor.get("fx", 2268.36)), float(sensor.get("fy", 2225.54))
            u0, v0 = float(sensor.get("u0", 1048.64)), float(sensor.get("v0", 519.277))
            p2 = f"{fx:.12g} 0 {u0:.12g} 0 0 {fy:.12g} {v0:.12g} 0 0 0 1 0"
            calib = f"P0: {p2}\nP1: {p2}\nP2: {p2}\nP3: {p2}\nR0_rect: 1 0 0 0 1 0 0 0 1\nTr_velo_to_cam: 1 0 0 0 0 1 0 0 0 0 1 0\nTr_imu_to_velo: 1 0 0 0 0 1 0 0 0 0 1 0\n"
            (dst / split / "calib" / f"{sample_id}.txt").write_text(calib)
        (dst / "ImageSets" / f"{split}.txt").write_text("\n".join(ids) + ("\n" if ids else ""))
    for split in ("training", "testing"):
        (dst / split / "velodyne").mkdir(parents=True, exist_ok=True)
        (dst / split / "planes").mkdir(parents=True, exist_ok=True)
    print(f"Converted dataset to {dst} (images are {'copied' if copy_images else 'symlinked'})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="cityscapes")
    ap.add_argument("--dst", default="cityscapes_kitti_format")
    ap.add_argument("--copy-images", action="store_true")
    args = ap.parse_args()
    convert(args.src, args.dst, args.copy_images)
