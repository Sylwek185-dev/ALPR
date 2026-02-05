# src/vision/ocr.py
import os
os.environ["DISABLE_MODEL_SOURCE_CHECK"] = "True"

import re
from paddleocr import PaddleOCR


# Preferujemy ciąg jak tablica: litery/cyfry, 5-9 znaków
PLATE_LIKE_RE = re.compile(r"^[A-Z0-9]{5,9}$")


def _normalize(text: str) -> str:
    """
    Normalizacja OCR:
    - uppercase
    - usuń wszystko poza A-Z0-9
    """
    t = (text or "").upper()
    t = re.sub(r"[^A-Z0-9]", "", t)
    return t


def _score_plate_like(text: str, conf: float) -> float:
    """
    Scoring: wybieraj wynik, który wygląda jak tablica.
    """
    t = text
    s = float(conf)

    # bonus za zgodność z regex
    if PLATE_LIKE_RE.match(t):
        s += 0.60

    # preferuj długość 6-8
    if 6 <= len(t) <= 8:
        s += 0.30

    # kara za długość odbiegającą od 7
    s -= abs(len(t) - 7) * 0.05

    # kara za "podejrzane" bardzo krótkie
    if len(t) < 5:
        s -= 0.50

    return s


class PlateOCR:
    def __init__(self):
        # PaddleOCR 3.x / PaddleX pipeline
        self.ocr = PaddleOCR(lang="en")

    def read_best(self, plate_rgb):
        """
        Zwraca (text, confidence).
        Jeśli nie znajdzie sensownego wyniku: ("", 0.0)
        """
        if plate_rgb is None:
            return "", 0.0

        res = self.ocr.ocr(plate_rgb)
        if not res:
            return "", 0.0

        # W Twojej wersji: res = [ { ... 'rec_texts': [...], 'rec_scores': [...] ... } ]
        if isinstance(res, list) and len(res) > 0 and isinstance(res[0], dict):
            d = res[0]
            texts = d.get("rec_texts", []) or []
            scores = d.get("rec_scores", []) or []

            candidates = []
            for t, sc in zip(texts, scores):
                t2 = _normalize(t)
                if not t2:
                    continue

                # filtruj typowe śmieci z paska UE
                if t2 in {"PL", "POL", "EU"}:
                    continue

                candidates.append((t2, float(sc)))

            if not candidates:
                return "", 0.0

            # wybierz najbardziej "tablicowy" wynik
            best_text, best_conf = max(
                candidates,
                key=lambda x: _score_plate_like(x[0], x[1])
            )
            return best_text, float(best_conf)

        # Fallback (gdyby kiedyś format był inny)
        return "", 0.0
