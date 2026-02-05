import xml.etree.ElementTree as ET
from dataclasses import dataclass

@dataclass(frozen=True)
class CvatBox:
    image_name: str
    width: int
    height: int
    label: str
    xtl: float
    ytl: float
    xbr: float
    ybr: float
    plate_number: str | None

def load_cvat_boxes(xml_path: str) -> list[CvatBox]:
    """
    Obsługuje CVAT XML w formie:
    <image name="10.jpg" width="..." height="...">
      <box label="plate" xtl="..." ytl="..." xbr="..." ybr="...">
        <attribute name="plate number">SK404XK</attribute>
      </box>
    </image>
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    boxes: list[CvatBox] = []

    for img in root.findall(".//image"):
        name = img.attrib.get("name")
        w = int(float(img.attrib.get("width", "0")))
        h = int(float(img.attrib.get("height", "0")))

        for box in img.findall("./box"):
            label = box.attrib.get("label", "")
            xtl = float(box.attrib.get("xtl", "0"))
            ytl = float(box.attrib.get("ytl", "0"))
            xbr = float(box.attrib.get("xbr", "0"))
            ybr = float(box.attrib.get("ybr", "0"))

            plate_number = None
            for attr in box.findall("./attribute"):
                if (attr.attrib.get("name") or "").strip().lower() == "plate number":
                    plate_number = (attr.text or "").strip()

            boxes.append(CvatBox(
                image_name=name,
                width=w,
                height=h,
                label=label,
                xtl=xtl,
                ytl=ytl,
                xbr=xbr,
                ybr=ybr,
                plate_number=plate_number
            ))

    return boxes

def get_ground_truth_plate(xml_path: str, image_name: str) -> str | None:
    """
    Zwraca plate_number dla danego pliku, jeśli jest w XML.
    Jeśli jest kilka boxów w obrazie, bierze pierwszy z plate_number.
    """
    boxes = load_cvat_boxes(xml_path)
    for b in boxes:
        if b.image_name == image_name and b.plate_number:
            return b.plate_number
    return None
