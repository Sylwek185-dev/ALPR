import re

# Prosty regex: PL tablice zwykle 5-8 znaków, litery/cyfry.
PLATE_RE = re.compile(r"^[A-Z0-9]{5,9}$")

# Typowe pomyłki OCR (możesz dopasować pod swoje dane)
FIXES = str.maketrans({
    "O": "0",
    "I": "1",
    "Z": "2",
    "S": "5",
    "B": "8",
})

def normalize(text: str) -> str:
    t = (text or "").upper()
    t = re.sub(r"[^A-Z0-9]", "", t)
    return t

def validate_and_fix(text: str) -> str | None:
    t = normalize(text)
    if PLATE_RE.match(t):
        return t

    t2 = t.translate(FIXES)
    if PLATE_RE.match(t2):
        return t2

    return None
