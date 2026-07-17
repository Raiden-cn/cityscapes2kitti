#!/usr/bin/env python3
"""Visualize KITTI-style 2D/3D annotations without opening a GUI window."""
import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


COLORS = {
    "Car": (0, 220, 0), "Truck": (255, 165, 0), "Bus": (255, 80, 0),
    "Pedestrian": (0, 180, 255), "Cyclist": (255, 0, 220),
}


def parse_calib(path):
    values = {}
    for line in path.read_text().splitlines():
        if ":" not in line:
            continue
        key, raw = line.split(":", 1)
        values[key] = [float(v) for v in raw.split()]
    p2 = values.get("P2") or values.get("P0")
    if not p2 or len(p2) != 12:
        raise ValueError(f"Missing 3x4 projection matrix in {path}")
    return [p2[0:4], p2[4:8], p2[8:12]]


def parse_labels(path):
    labels = []
    if not path.exists():
        return labels
    for line in path.read_text().splitlines():
        fields = line.split()
        if len(fields) < 15 or fields[0] in {"DontCare", "Misc"}:
            continue
        labels.append({
            "type": fields[0], "truncation": float(fields[1]), "occlusion": int(float(fields[2])),
            "bbox": tuple(float(v) for v in fields[4:8]),
            "h": float(fields[8]), "w": float(fields[9]), "l": float(fields[10]),
            "x": float(fields[11]), "y": float(fields[12]), "z": float(fields[13]),
            "ry": float(fields[14]),
        })
    return labels


def project_box(obj, projection):
    h, w, length = obj["h"], obj["w"], obj["l"]
    x, y, z, ry = obj["x"], obj["y"], obj["z"], obj["ry"]
    # KITTI locations are bottom centers; corners are ordered for visible edges.
    local = [(length / 2, 0, w / 2), (length / 2, 0, -w / 2),
             (-length / 2, 0, -w / 2), (-length / 2, 0, w / 2),
             (length / 2, -h, w / 2), (length / 2, -h, -w / 2),
             (-length / 2, -h, -w / 2), (-length / 2, -h, w / 2)]
    c, s = math.cos(ry), math.sin(ry)
    points = []
    for lx, ly, lz in local:
        px = c * lx + s * lz + x
        py = ly + y
        pz = -s * lx + c * lz + z
        if pz <= 0.1:
            return []
        u = (projection[0][0] * px + projection[0][1] * py + projection[0][2] * pz + projection[0][3]) / pz
        v = (projection[1][0] * px + projection[1][1] * py + projection[1][2] * pz + projection[1][3]) / pz
        points.append((u, v))
    return points


def draw_object(draw, obj, projection, font):
    color = COLORS.get(obj["type"], (255, 255, 0))
    x1, y1, x2, y2 = obj["bbox"]
    draw.rectangle((x1, y1, x2, y2), outline=color, width=3)
    corners = project_box(obj, projection)
    if corners:
        edges = ((0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7))
        for a, b in edges:
            draw.line((corners[a], corners[b]), fill=color, width=3)
    text = f"{obj['type']} xyz=({obj['x']:.1f},{obj['y']:.1f},{obj['z']:.1f}) dims=({obj['h']:.1f},{obj['w']:.1f},{obj['l']:.1f})"
    left, top, right, bottom = draw.textbbox((x1, max(0, y1 - 20)), text, font=font)
    draw.rectangle((left, top, right + 2, bottom + 2), fill=(0, 0, 0))
    draw.text((x1, max(0, y1 - 20)), text, fill=color, font=font)


def resolve_root(dataset, root):
    root = Path(root)
    if dataset == "kitti":
        return root / "training"
    return root / "train" if root.name != "train" else root


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=("kitti", "cityscapes"), required=True)
    parser.add_argument("--root", required=True, help="KITTI root or converted Cityscapes root")
    parser.add_argument("--split", default="train", choices=("train", "val", "test"))
    parser.add_argument("--id", required=True, help="Frame ID, e.g. 000000")
    parser.add_argument("--output-dir", default="visualization")
    args = parser.parse_args()
    root = resolve_root(args.dataset, args.root)
    if args.dataset == "cityscapes":
        root = Path(args.root) / args.split
    sample_id = f"{int(args.id):06d}"
    image_path = root / "image_2" / f"{sample_id}.png"
    label_path = root / "label_2" / f"{sample_id}.txt"
    calib_path = root / "calib" / f"{sample_id}.txt"
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    projection = parse_calib(calib_path)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 16)
    except OSError:
        font = ImageFont.load_default()
    labels = parse_labels(label_path)
    for obj in labels:
        draw_object(draw, obj, projection, font)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{args.dataset}_{args.split}_{sample_id}.png"
    image.save(output_path)
    print(f"Saved {len(labels)} objects to {output_path}")


if __name__ == "__main__":
    main()
