# Cityscapes to KITTI Format

This project converts Cityscapes `leftImg8bit` images and `gtBbox3d` annotations into a KITTI-style dataset for KITTI-based 3D object detection projects.

## Requirements

- Python 3.8 or newer
- An extracted Cityscapes dataset with this directory structure:

```text
/path/to/cityscapes/
├── leftImg8bit/
│   ├── train/
│   │   ├── aachen/
│   │   │   └── aachen_000000_000019_leftImg8bit.png
│   │   ├── val/
│   │   │   └── frankfurt/
│   │   │       └── frankfurt_000000_000294_leftImg8bit.png
│   │   └── test/
│   │       └── munich/
│   │           └── munich_000000_000019_leftImg8bit.png
└── gtBbox3d/
    ├── train/
    │   ├── aachen/
    │   │   └── aachen_000000_000019_gtBbox3d.json
    │   ├── val/
    │   │   └── frankfurt/
    │   │       └── frankfurt_000000_000294_gtBbox3d.json
    │   └── test/
    │       └── munich/
    │           └── munich_000000_000019_gtBbox3d.json
```

`train`, `val`, and `test` contain city subdirectories. Each image has a matching JSON file with the same Cityscapes frame stem; only the suffix differs (`_leftImg8bit.png` versus `_gtBbox3d.json`). The names above are examples; the converter processes all cities and frames found under these directories.

The converter uses only Python standard-library modules.

## Usage

```bash
python3 convert_cityscapes_to_kitti.py \\
  --src /path/to/cityscapes \\
  --dst /path/to/cityscapes_kitti_format
```

Images use relative symbolic links by default. To copy files instead, add `--copy-images`.

The script rebuilds generated `image_2`, `label_2`, and `calib` directories on each run.

## Output Layout

```text
cityscapes_kitti_format/
├── train/image_2/000000.png
├── train/label_2/000000.txt
├── train/calib/000000.txt
├── val/
├── test/
├── ImageSets/{train,val,test}.txt
├── training/velodyne/
└── testing/velodyne/
```

Frame IDs are assigned independently per split, starting at `000000`. Image, label, calibration, and `ImageSets` entries use the same ID. Empty `velodyne` directories are included for loader compatibility; Cityscapes does not provide KITTI-format point clouds.

## Label Conversion

Labels use the 15-field KITTI format:

```text
type truncation occlusion alpha left top right bottom height width length x y z rotation_y
```

| Cityscapes | KITTI |
| --- | --- |
| `car` | `Car` |
| `truck` | `Truck` |
| `bus` | `Bus` |
| `train` | `Train` |
| `motorcycle` | `Motorcycle` |
| `bicycle`, `rider` | `Cyclist` |
| `person` | `Pedestrian` |

3D centers and dimensions are converted to KITTI camera coordinates. Dimensions are written as `(height, width, length)` and the amodal 2D box is preferred when available.

## Calibration

Each `calib/*.txt` contains `P0` through `P3`, `R0_rect`, `Tr_velo_to_cam`, and `Tr_imu_to_velo`. Projection matrices use per-image Cityscapes camera intrinsics; unavailable velodyne and IMU transforms are identity matrices.

## Verification

```bash
for split in train val test; do
  find "cityscapes_kitti_format/$split/image_2" -type f -o -type l | wc -l
  find "cityscapes_kitti_format/$split/label_2" -type f | wc -l
  find "cityscapes_kitti_format/$split/calib" -type f | wc -l
done
```
