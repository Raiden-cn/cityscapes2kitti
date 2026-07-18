# Cityscapes to KITTI Format

Convert Cityscapes 3D annotations to a KITTI-compatible dataset and visualize either dataset from the same CLI.

## Requirements

- Python 3.8+
- Cityscapes arranged as:

```text
/path/to/cityscapes/
├── leftImg8bit/{train,val,test}/<city>/*_leftImg8bit.png
└── gtBbox3d/{train,val,test}/<city>/*_gtBbox3d.json
```

The image and JSON files must share the same frame name before their suffix.

## Convert

```bash
python3 convert_cityscapes_to_kitti.py \\
  --src /path/to/cityscapes \\
  --dst /path/to/cityscapes_kitti_format
```

Images are symlinked by default. Copy them instead with `--copy-images`:

```bash
python3 convert_cityscapes_to_kitti.py \\
  --src /path/to/cityscapes \\
  --dst /path/to/cityscapes_kitti_format \\
  --copy-images
```

The output uses six-digit IDs independently within each split:

```text
cityscapes_kitti_format/
├── train/{image_2,label_2,calib}/000000.*
├── val/{image_2,label_2,calib}/000000.*
├── test/{image_2,label_2,calib}/000000.*
├── ImageSets/{train,val,test}.txt
├── training/velodyne/
└── testing/velodyne/
```

## Visualize

The visualization script writes two PNG files per frame and does not open a GUI window.

Converted Cityscapes:

```bash
python3 visualize_dataset.py \\
  --dataset cityscapes \\
  --root /path/to/cityscapes_kitti_format \\
  --split train \\
  --id 000000 \\
  --output-dir visualization
```

Standard KITTI:

```bash
python3 visualize_dataset.py \\
  --dataset kitti \\
  --root /path/to/kitti \\
  --split train \\
  --id 000000 \\
  --output-dir visualization
```

Outputs:

```text
visualization/<dataset>_<split>_<id>_2d.png
visualization/<dataset>_<split>_<id>_3d.png
```

The `_2d.png` file shows 2D boxes and labels. The `_3d.png` file shows projected 3D boxes, labels, and the red front-face marker.
