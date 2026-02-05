import os
import random
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

CLASS_MAP = {"plate": 0}  # u Ciebie label="plate"

def yolo_line_from_box(img_w, img_h, xtl, ytl, xbr, ybr, cls_id):
    # YOLO: class x_center y_center width height (0..1)
    x_center = ((xtl + xbr) / 2.0) / img_w
    y_center = ((ytl + ybr) / 2.0) / img_h
    bw = (xbr - xtl) / img_w
    bh = (ybr - ytl) / img_h

    # clamp (czasem CVAT ma minimalnie poza obraz)
    def clamp(v): 
        return max(0.0, min(1.0, v))

    x_center = clamp(x_center)
    y_center = clamp(y_center)
    bw = clamp(bw)
    bh = clamp(bh)

    return f"{cls_id} {x_center:.6f} {y_center:.6f} {bw:.6f} {bh:.6f}"

def parse_cvat(xml_path: str):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    data = []  # (image_name, width, height, [yolo_lines])
    for img in root.findall(".//image"):
        name = img.attrib["name"]
        w = int(float(img.attrib["width"]))
        h = int(float(img.attrib["height"]))

        lines = []
        for box in img.findall("./box"):
            label = box.attrib.get("label", "").strip()
            if label not in CLASS_MAP:
                continue
            cls_id = CLASS_MAP[label]
            xtl = float(box.attrib["xtl"])
            ytl = float(box.attrib["ytl"])
            xbr = float(box.attrib["xbr"])
            ybr = float(box.attrib["ybr"])
            lines.append(yolo_line_from_box(w, h, xtl, ytl, xbr, ybr, cls_id))

        data.append((name, w, h, lines))

    return data

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--xml", default="data/annotations.xml")
    ap.add_argument("--images", default="data/images")
    ap.add_argument("--out", default="data/yolo")
    ap.add_argument("--val", type=float, default=0.2)  # 20% walidacja
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    random.seed(args.seed)

    out = Path(args.out)
    for p in [
        out / "images/train", out / "images/val",
        out / "labels/train", out / "labels/val"
    ]:
        p.mkdir(parents=True, exist_ok=True)

    items = parse_cvat(args.xml)
    # bierzemy tylko te, które mają przynajmniej jedną tablicę
    items = [it for it in items if len(it[3]) > 0]

    random.shuffle(items)
    val_count = int(len(items) * args.val)
    val_set = set([x[0] for x in items[:val_count]])

    images_dir = Path(args.images)

    copied = 0
    for name, w, h, lines in items:
        src_img = images_dir / name
        if not src_img.exists():
            # jeśli masz jpg w innym miejscu/inną nazwę, tu zobaczysz co nie pasuje
            print(f"[WARN] Brak pliku obrazu: {src_img}")
            continue

        split = "val" if name in val_set else "train"
        dst_img = out / f"images/{split}/{name}"
        dst_lbl = out / f"labels/{split}/{Path(name).stem}.txt"

        shutil.copy2(src_img, dst_img)
        dst_lbl.write_text("\n".join(lines) + "\n", encoding="utf-8")
        copied += 1

    print(f"OK. Skopiowano {copied} obrazów do {out}")

if __name__ == "__main__":
    main()
