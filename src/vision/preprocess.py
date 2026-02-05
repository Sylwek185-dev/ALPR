# src/vision/preprocess.py
import cv2


def crop_with_padding(img, x1, y1, x2, y2, pad=30):
    """
    Crop bbox + padding w pikselach.
    """
    h, w = img.shape[:2]
    x1 = max(0, int(x1) - pad)
    y1 = max(0, int(y1) - pad)
    x2 = min(w, int(x2) + pad)
    y2 = min(h, int(y2) + pad)

    if x2 <= x1 or y2 <= y1:
        return None

    return img[y1:y2, x1:x2].copy()


def basic_preprocess(plate_bgr):
    """
    Preprocessing pod tablice rejestracyjne:
    - lekko przycina elementy przeszkadzające (pasek UE, ramki)
    - powiększa
    - delikatnie wyostrza
    - zwraca RGB (PaddleOCR)
    """
    if plate_bgr is None or plate_bgr.size == 0:
        return None

    # --- 1) Usuń pasek UE (lewy fragment) + lekko góra/dół (ramki) ---
    h, w = plate_bgr.shape[:2]

    # usuń ok. 12% z lewej (pasek UE + "PL")
    left_cut = int(w * 0.07)
    if w - left_cut > w * 0.8:
        plate_bgr = plate_bgr[:, left_cut:]

    # usuń po ~12% z góry i dołu (ramki / reklamy)
    h2, w2 = plate_bgr.shape[:2]
    top = int(h2 * 0.12)
    bot = int(h2 * 0.12)
    if (h2 - top - bot) > 10:
        plate_bgr = plate_bgr[top:h2 - bot, :]

    # --- 2) Powiększenie ---
    h3, w3 = plate_bgr.shape[:2]
    scale = 2  # możesz dać 3 jeśli tablice są małe
    plate = cv2.resize(
        plate_bgr,
        (w3 * scale, h3 * scale),
        interpolation=cv2.INTER_CUBIC
    )

    # --- 3) Delikatne wyostrzenie (bez binarizacji) ---
    blur = cv2.GaussianBlur(plate, (0, 0), 1.2)
    sharp = cv2.addWeighted(plate, 1.6, blur, -0.6, 0)

    # --- 4) BGR -> RGB dla PaddleOCR ---
    rgb = cv2.cvtColor(sharp, cv2.COLOR_BGR2RGB)
    return rgb
