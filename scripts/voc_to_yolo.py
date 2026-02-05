import os
import glob
import xml.etree.ElementTree as ET

# USTAW: nazwy klas w XML (dopasuj do siebie)
CLASS_MAP = {
    "plate": 0,
    "license_plate": 0,
    "tablica": 0,
}

def convert_box(size, box):
    w, h = size
    xmin, ymin, xmax, ymax = box
    x_center = ((xmin + xmax) / 2.0) / w
    y_center = ((ymin + ymax) / 2.0) / h
    bw = (xmax - xmin) / w
    bh = (ymax - ymin) / h
    return x_center, y_center, bw, bh

def parse_voc(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    size_node = root.find("size")
    w = int(size_node.find("width").text)
    h = int(size_node.find("height").text)

    labels = []
    for obj in root.findall("object"):
        name = obj.find("name").text.strip()
        if name not in CLASS_MAP:
            continue
        cls_id = CLASS_MAP[name]
        bnd = obj.find("bndbox")
        xmin = int(float(bnd.find("xmin").text))
        ymin = int(float(bnd.find("ymin").text))
        xmax = int(float(bnd.find("xmax").text))
        ymax = int(float(bnd.find("ymax").text))

        x, y, bw, bh = convert_box((w, h), (xmin, ymin, xmax, ymax))
        labels.append((cls_id, x, y, bw, bh))

    return labels

def main(voc_dir: str, out_labels_dir: str):
    os.makedirs(out_labels_dir, exist_ok=True)

    xml_files = glob.glob(os.path.join(voc_dir, "*.xml"))
    for xml_path in xml_files:
        labels = parse_voc(xml_path)
        base = os.path.splitext(os.path.basename(xml_path))[0]
        out_txt = os.path.join(out_labels_dir, base + ".txt")

        with open(out_txt, "w", encoding="utf-8") as f:
            for cls_id, x, y, bw, bh in labels:
                f.write(f"{cls_id} {x:.6f} {y:.6f} {bw:.6f} {bh:.6f}\n")

    print(f"Done. Converted {len(xml_files)} xml files → {out_labels_dir}")

if __name__ == "__main__":
    # przykład:
    # python scripts/voc_to_yolo.py data/voc_xml data/yolo/labels
    import sys
    voc_dir = sys.argv[1]
    out_dir = sys.argv[2]
    main(voc_dir, out_dir)
