# src/read_one.py
import argparse
import cv2
from pathlib import Path

from src.vision.detector import PlateDetector
from src.vision.preprocess import crop_with_padding, basic_preprocess
from src.vision.ocr import PlateOCR
from src.vision.validate import validate_and_fix


def resolve_image_path(img_arg: str | None, img_id: int | None) -> Path:
    if img_arg:
        return Path(img_arg)

    if img_id is None:
        raise ValueError("Podaj --img albo --id.")

    return Path("data/images") / f"{img_id}.jpg"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", type=int, help="np. 5 (wczyta data/images/5.jpg)")
    ap.add_argument("--img", type=str, help="np. data/images/5.jpg")
    ap.add_argument("--model", type=str, default="models/plate_detector.pt")
    ap.add_argument("--yolo-conf", type=float, default=0.35)
    ap.add_argument("--ocr-min-conf", type=float, default=0.40)
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args()

    if args.img is None and args.id is None:
        ap.error("Podaj --id albo --img.")

    img_path = resolve_image_path(args.img, args.id)
    if not img_path.exists():
        raise FileNotFoundError(f"Nie ma pliku: {img_path}")

    img = cv2.imread(str(img_path))
    if img is None:
        raise RuntimeError(f"Nie mogę wczytać obrazu: {img_path}")

    detector = PlateDetector(args.model, conf=args.yolo_conf)
    ocr = PlateOCR()

    det = detector.detect_best(img)
    if det is None:
        print(f"IMAGE:     {img_path.name}")
        print("Brak detekcji tablicy (YOLO nic nie znalazł).")
        return

    x1, y1, x2, y2, yconf = det
    plate_bgr = crop_with_padding(img, x1, y1, x2, y2, pad=30)
    if plate_bgr is None or plate_bgr.size == 0:
        print("Nie udało się wyciąć tablicy (crop pusty).")
        return

    # preprocess (Twoja wersja usuwa pasek UE ostrożnie itp.)
    plate_rgb = basic_preprocess(plate_bgr)

    # OCR próba 1
    raw_text, ocr_conf = ocr.read_best(plate_rgb)

    # fallback: jeśli wynik podejrzanie krótki albo bardzo słaby, spróbuj bez preprocessu
    if (len(raw_text) < 6) or (ocr_conf < args.ocr_min_conf):
        plate_rgb2 = cv2.cvtColor(plate_bgr, cv2.COLOR_BGR2RGB)
        raw2, conf2 = ocr.read_best(plate_rgb2)
        if conf2 > ocr_conf:
            raw_text, ocr_conf = raw2, conf2

    fixed = validate_and_fix(raw_text)
    final_plate = fixed if fixed else "UNKNOWN"

    print(f"IMAGE:     {img_path.name}")
    print(f"YOLO conf: {yconf:.3f}")
    print(f"OCR raw:   '{raw_text}' (conf {ocr_conf:.3f})")
    print(f"PL final:  {final_plate}")

    if args.show:
        cv2.imshow("Plate crop", plate_bgr)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
