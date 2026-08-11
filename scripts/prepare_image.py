#!/usr/bin/env python3
"""
Ritu photo-integration pipeline.

Usage: python3 prepare_image.py <name> --anchor-x <0..1> --anchor-y <0..1> [--pad 180]

For each source image:
  1. Sample the background color from the image corners.
  2. Pixel-density scan to find the real content bounding box against that background.
  3. Crop tight to the content, centered on a caller-supplied anchor (fraction of the
     content bbox width/height) rather than the bbox's naive geometric center.
  4. Scan the cropped region for stray artifacts (isolated high-variance blobs near
     the edges that don't belong to the main content mass) and report them.
  5. Pad with ImageOps.expand, filled with the sampled background color, so the
     radial mask has room to feather into.
  6. Save to processed-images/<name>.png and print the sampled background color.
"""
import argparse
import sys
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source-images"
OUT = ROOT / "processed-images"


def sample_background(im, corner_px=6):
    """Majority-vote the background color from the four corners."""
    w, h = im.size
    px = im.convert("RGB").load()
    samples = []
    for cx, cy in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        for dx in range(corner_px):
            for dy in range(corner_px):
                x = min(w - 1, max(0, cx + (dx if cx == 0 else -dx)))
                y = min(h - 1, max(0, cy + (dy if cy == 0 else -dy)))
                samples.append(px[x, y])
    r = sorted(s[0] for s in samples)[len(samples) // 2]
    g = sorted(s[1] for s in samples)[len(samples) // 2]
    b = sorted(s[2] for s in samples)[len(samples) // 2]
    return (r, g, b)


def content_bbox(im, bg, tol=14, step=4):
    """Pixel-density scan: find rows/cols that contain non-background pixels."""
    w, h = im.size
    px = im.convert("RGB").load()

    def is_bg(p):
        return abs(p[0] - bg[0]) <= tol and abs(p[1] - bg[1]) <= tol and abs(p[2] - bg[2]) <= tol

    def row_has_content(y):
        for x in range(0, w, step):
            if not is_bg(px[x, y]):
                return True
        return False

    def col_has_content(x):
        for y in range(0, h, step):
            if not is_bg(px[x, y]):
                return True
        return False

    top = 0
    while top < h and not row_has_content(top):
        top += step
    bottom = h - 1
    while bottom > top and not row_has_content(bottom):
        bottom -= step
    left = 0
    while left < w and not col_has_content(left):
        left += step
    right = w - 1
    while right > left and not col_has_content(right):
        right -= step

    return (max(0, left - step), max(0, top - step), min(w, right + step), min(h, bottom + step))


def scan_artifacts(im, bg, bbox, tol=14, block=48, edge_margin=0.12):
    """
    Look for small isolated high-variance blocks near the crop edges (icons/badges/
    text a generator may have added) that sit apart from the main content mass.
    Returns a list of (x, y, w, h, variance) flags for manual review.
    """
    left, top, right, bottom = bbox
    w, h = right - left, bottom - top
    px = im.convert("RGB").load()
    flags = []
    ex, ey = int(w * edge_margin), int(h * edge_margin)
    edge_zones = [
        (left, top, left + ex, top + ey),           # top-left
        (right - ex, top, right, top + ey),         # top-right
        (left, bottom - ey, left + ex, bottom),      # bottom-left
        (right - ex, bottom - ey, right, bottom),    # bottom-right
    ]
    for zx0, zy0, zx1, zy1 in edge_zones:
        for by in range(zy0, zy1, block):
            for bx in range(zx0, zx1, block):
                pixels = []
                for y in range(by, min(by + block, zy1)):
                    for x in range(bx, min(bx + block, zx1)):
                        pixels.append(px[x, y])
                if not pixels:
                    continue
                mean = tuple(sum(p[i] for p in pixels) / len(pixels) for i in range(3))
                var = sum(sum((p[i] - mean[i]) ** 2 for i in range(3)) for p in pixels) / len(pixels)
                is_bg_block = abs(mean[0] - bg[0]) <= tol and abs(mean[1] - bg[1]) <= tol and abs(mean[2] - bg[2]) <= tol
                if not is_bg_block and var > 4500:
                    flags.append((bx, by, block, block, round(var, 1)))
    return flags


def process(name, anchor_x, anchor_y, pad, tol, block_check=True):
    src_path = SRC / f"{name}.png"
    im = Image.open(src_path).convert("RGB")
    w, h = im.size

    bg = sample_background(im)
    print(f"[{name}] sampled background: rgb{bg}  (source {w}x{h})")

    bbox = content_bbox(im, bg, tol=tol)
    bl, bt, br, bb = bbox
    cw, ch = br - bl, bb - bt
    print(f"[{name}] content bbox: {bbox}  ({cw}x{ch})")

    flags = scan_artifacts(im, bg, bbox) if block_check else []
    if flags:
        print(f"[{name}] WARNING: {len(flags)} possible artifact block(s) near edges:")
        for f in flags:
            print(f"    x={f[0]} y={f[1]} w={f[2]} h={f[3]} variance={f[4]}")
    else:
        print(f"[{name}] artifact scan: clean, no stray blocks detected")

    # anchor point in absolute pixel coords, within the content bbox
    ax = bl + cw * anchor_x
    ay = bt + ch * anchor_y

    # Crop tight to the actual content bbox -- no background padding added here to
    # force the anchor to dead center, since that would drag in acres of dead space
    # on whichever side the content happens to be thin. The anchor instead drives
    # the mask/vignette center downstream in CSS, the same way Doorsong's roof mask
    # sat at "50% 47%" rather than exact center to match its off-center subject.
    left, top, right, bottom = bl, bt, br, bb
    cropped = im.crop((left, top, right, bottom))
    print(f"[{name}] cropped tight to content bbox {cropped.size}, anchor at frac ({anchor_x:.2f}, {anchor_y:.2f}) -> abs ({ax:.0f}, {ay:.0f})")

    padded = ImageOps.expand(cropped, border=pad, fill=bg)
    print(f"[{name}] padded {pad}px with sampled background -> {padded.size}")

    # anchor's position within the final padded frame, for the CSS mask/vignette center
    final_ax = (ax - left + pad) / padded.size[0]
    final_ay = (ay - top + pad) / padded.size[1]
    print(f"[{name}] anchor within final frame: {final_ax*100:.1f}% {final_ay*100:.1f}%  (use as mask-image center)")

    OUT.mkdir(exist_ok=True)
    out_path = OUT / f"{name}.png"
    padded.save(out_path)
    print(f"[{name}] saved -> {out_path}")
    print(f"[{name}] BACKGROUND_HEX=#{bg[0]:02x}{bg[1]:02x}{bg[2]:02x}")
    return bg, out_path, (final_ax, final_ay)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--anchor-x", type=float, required=True, help="0..1 fraction across the content bbox width")
    ap.add_argument("--anchor-y", type=float, required=True, help="0..1 fraction down the content bbox height")
    ap.add_argument("--pad", type=int, default=180)
    ap.add_argument("--tol", type=int, default=14)
    args = ap.parse_args()
    process(args.name, args.anchor_x, args.anchor_y, args.pad, args.tol)
