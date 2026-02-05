import numpy as np
from ultralytics import YOLO

class PlateDetector:
    def __init__(self, model_path: str, conf: float = 0.35):
        self.model = YOLO(model_path)
        self.conf = conf

    def detect_best(self, image_bgr):
        """
        Returns:
            (x1,y1,x2,y2,conf) as ints/floats or None
        """
        res = self.model.predict(source=image_bgr, conf=self.conf, verbose=False)[0]
        if res.boxes is None or len(res.boxes) == 0:
            return None

        xyxy = res.boxes.xyxy.cpu().numpy()
        confs = res.boxes.conf.cpu().numpy()
        i = int(np.argmax(confs))
        x1, y1, x2, y2 = xyxy[i].tolist()
        return int(x1), int(y1), int(x2), int(y2), float(confs[i])
