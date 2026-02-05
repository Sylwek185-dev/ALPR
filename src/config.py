from dataclasses import dataclass

@dataclass(frozen=True)
class Paths:
    images_dir: str = "data/images"
    cvat_xml: str = "data/annotations.xml"
    model_path: str = "models/plate_detector.pt"

@dataclass(frozen=True)
class Thresholds:
    yolo_conf: float = 0.35
    ocr_conf: float = 0.55
