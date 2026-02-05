# src/app_service.py
from datetime import datetime
from pathlib import Path

import cv2

from src.storage.db import init_db
from src.storage.repo import register_entry, register_exit, list_open, list_last, list_all
from src.vision.detector import PlateDetector
from src.vision.preprocess import crop_with_padding, basic_preprocess
from src.vision.ocr import PlateOCR
from src.vision.validate import validate_and_fix


class ParkingService:
    def __init__(self, model_path: str = "models/plate_detector.pt", yolo_conf: float = 0.35):
        init_db()
        self.detector = PlateDetector(model_path, conf=yolo_conf)
        self.ocr = PlateOCR()

    def read_plate(self, img_path: str) -> dict:
        p = Path(img_path)
        if not p.exists():
            return {"ok": False, "error": f"Brak pliku: {img_path}"}

        img = cv2.imread(str(p))
        if img is None:
            return {"ok": False, "error": f"Nie mogę wczytać: {img_path}"}

        det = self.detector.detect_best(img)
        if det is None:
            return {"ok": False, "error": "Brak detekcji tablicy (YOLO)"}

        x1, y1, x2, y2, yconf = det
        plate_bgr = crop_with_padding(img, x1, y1, x2, y2, pad=30)
        if plate_bgr is None or plate_bgr.size == 0:
            return {"ok": False, "error": "Pusty crop tablicy"}

        plate_rgb = basic_preprocess(plate_bgr)
        raw, rconf = self.ocr.read_best(plate_rgb)
        fixed = validate_and_fix(raw)

        return {
            "ok": True,
            "plate": fixed or None,
            "raw": raw,
            "ocr_conf": float(rconf),
            "yolo_conf": float(yconf),
        }

    def entry_from_image(self, img_path: str) -> dict:
        res = self.read_plate(img_path)
        if not res["ok"] or not res.get("plate"):
            return {"ok": False, "error": res.get("error", "UNKNOWN"), "read": res}

        plate = res["plate"]
        
        try:
            event_id = register_entry(plate)
            return {"ok": True, "event_id": event_id, "plate": plate, "read": res}
        except ValueError as e:
            return {"ok": False, "error": str(e), "plate": plate, "read": res}



        

    def exit_from_image(self, img_path: str) -> dict:
        res = self.read_plate(img_path)
        if not res["ok"] or not res.get("plate"):
            return {"ok": False, "error": res.get("error", "UNKNOWN"), "read": res}

        plate = res["plate"]
        out = register_exit(plate, datetime.now())
        if out is None:
            return {"ok": False, "error": f"BLOCKED: brak aktywnego wjazdu dla {plate}", "read": res}

        return {"ok": True, "exit": out, "plate": plate, "read": res}

    def open_cars(self):
        return list_open()

    def history(self, limit: int = 50):
        return list_last(limit)

    def export_all(self, out_csv: str):
        rows = list_all()
        return rows
