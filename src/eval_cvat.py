import argparse
import os
import cv2

from src.config import Paths, Thresholds
from src.cvat.parser import get_ground_truth_plate
from src.vision.detector import PlateDetector
from src.vision.preprocess import crop_with_padding, basic_preprocess
from src.vision.ocr import PlateOCR
from src.vision.validate import validate_and_fix

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True, help="np. 10")
    ap.add_argument("--model", default=Paths().model_path)
    ap.add_argument("--xml", default=Paths().cvat_xml)
    ap.add_argument("--yolo-conf", type=float, default=Thresholds().yolo_conf)
    ap.add_argument("--ocr-conf", type=float, default=Thresholds().ocr_conf)
    args = ap.parse_args()

    img_name = args.id if args.id.lower().endswith(".jpg") else f"{args.id}.jpg"
    img_path = os.path.join(Paths().images_dir, img_name)

    img = cv2.imread(img_path)
    if img is None:
        raise FileNotFoundError(f"Nie mogę wczytać: {img_path}")

    gt = get_ground_truth_plate(args.xml, img_name)

    detector = PlateDetector(args.model, conf=args.yolo_conf)
    ocr = PlateOCR()

    det = detector.detect_best(img)
    if det is None:
        print(f"IMAGE: {img_name}")
        print("YOLO:  no detection")
        print(f"GT:    {gt}")
        return

    x1, y1, x2, y2, dconf = det
    plate_bgr = crop_with_padding(img, x1, y1, x2, y2, pad=12)
    plate_rgb = basic_preprocess(plate_bgr)

    raw, conf = ocr.read_best(plate_rgb)
    pred = validate_and_fix(raw)
    pred_final = pred if (pred and conf >= args.ocr_conf) else None

    print(f"IMAGE: {img_name}")
    print(f"GT:    {gt}")
    print(f"PRED:  {pred_final} (yolo {dconf:.3f}, ocr {conf:.3f}, raw={raw!r})")

    if gt and pred_final:
        print("MATCH:", "YES" if gt.upper() == pred_final.upper() else "NO")
    else:
        print("MATCH: N/A")

if __name__ == "__main__":
    main()
