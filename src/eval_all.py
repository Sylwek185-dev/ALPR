# src/eval_10.py
import os
import glob
import csv
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import cv2

from src.vision.detector import PlateDetector
from src.vision.preprocess import crop_with_padding, basic_preprocess
from src.vision.ocr import PlateOCR
from src.vision.validate import validate_and_fix


def norm_plate(s: str | None) -> str:
    s = (s or "").upper()
    s = re.sub(r"[^A-Z0-9]", "", s)
    return s


def load_cvat_gt(xml_path: str) -> dict[str, str]:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    gt: dict[str, str] = {}

    for img in root.findall(".//image"):
        name = img.attrib.get("name")
        if not name:
            continue

        plate_number = None
        for box in img.findall("./box"):
            for attr in box.findall("./attribute"):
                if (attr.attrib.get("name") or "").strip().lower() == "plate number":
                    txt = (attr.text or "").strip()
                    if txt:
                        plate_number = txt
                        break
            if plate_number:
                break

        if plate_number:
            gt[name] = norm_plate(plate_number)

    return gt


def predict_plate(img_bgr, detector: PlateDetector, ocr: PlateOCR,
                  yolo_conf_min: float = 0.35, ocr_min_conf: float = 0.40):
    det = detector.detect_best(img_bgr)
    if det is None:
        return None, 0.0, "", 0.0

    x1, y1, x2, y2, yconf = det
    if yconf < yolo_conf_min:
        return None, yconf, "", 0.0

    plate_bgr = crop_with_padding(img_bgr, x1, y1, x2, y2, pad=30)
    if plate_bgr is None or plate_bgr.size == 0:
        return None, yconf, "", 0.0

    # try 1: preprocess
    plate_rgb = basic_preprocess(plate_bgr)
    raw, rconf = ocr.read_best(plate_rgb)

    # fallback: no preprocess
    if (len(raw) < 6) or (rconf < ocr_min_conf):
        plate_rgb2 = cv2.cvtColor(plate_bgr, cv2.COLOR_BGR2RGB)
        raw2, conf2 = ocr.read_best(plate_rgb2)
        if conf2 > rconf:
            raw, rconf = raw2, conf2

    fixed = validate_and_fix(raw)
    return (fixed if fixed else None), yconf, raw, rconf


def main():
    os.environ["DISABLE_MODEL_SOURCE_CHECK"] = "True"

    images_dir = Path("data/images")
    xml_path = Path("data/annotations.xml")
    model_path = Path("models/plate_detector.pt")

    out_csv = Path("data/results/results_10.csv")
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    if not images_dir.exists():
        raise FileNotFoundError(f"Missing folder: {images_dir}")
    if not model_path.exists():
        raise FileNotFoundError(f"Missing model: {model_path}")

    gt_map = load_cvat_gt(str(xml_path)) if xml_path.exists() else {}

    detector = PlateDetector(str(model_path), conf=0.35)
    ocr = PlateOCR()

    img_paths = sorted(glob.glob(str(images_dir / "*.jpg")))[:10]
    if not img_paths:
        raise FileNotFoundError("No .jpg found in data/images")

    results = []
    with_gt = 0
    correct = 0
    unknown = 0

    for p in img_paths:
        name = Path(p).name
        img = cv2.imread(p)
        if img is None:
            continue

        pred, yconf, raw, rconf = predict_plate(img, detector, ocr)

        gt = gt_map.get(name, "")
        match = ""
        if gt:
            with_gt += 1
            match = "1" if norm_plate(pred) == gt else "0"
            if match == "1":
                correct += 1

        if pred is None:
            unknown += 1

        results.append({
            "image": name,
            "gt": gt,
            "pred": pred or "",
            "match": match,
            "yolo_conf": f"{yconf:.3f}",
            "ocr_raw": raw,
            "ocr_conf": f"{rconf:.3f}",
        })

    # write CSV
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)

    print("\n===== EVAL (10 IMAGES) =====")
    print(f"Saved CSV: {out_csv.resolve()}")
    print(f"Images:    {len(results)}")
    print(f"UNKNOWN:   {unknown}")
    if with_gt:
        print(f"GT count:  {with_gt}")
        print(f"Correct:   {correct}")
        print(f"Accuracy:  {correct/with_gt:.3%}")
    else:
        print("No GT found in XML for these files (check XML / attribute name).")

    wrong = [r for r in results if r["match"] == "0"]
    if wrong:
        print("\nWrong examples:")
        for r in wrong:
            print(f"- {r['image']}: GT={r['gt']}  PRED={r['pred']}  raw={r['ocr_raw']!r} "
                  f"(yolo={r['yolo_conf']}, ocr={r['ocr_conf']})")
    print("")


if __name__ == "__main__":
    main()
