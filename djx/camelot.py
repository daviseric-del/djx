"""Musical key to Camelot wheel notation, and wheel distance."""

import re

_PITCH = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
# Camelot number by pitch class, for major (B) and minor (A) keys.
_MAJOR = {11: 1, 6: 2, 1: 3, 8: 4, 3: 5, 10: 6, 5: 7, 0: 8, 7: 9, 2: 10, 9: 11, 4: 12}
_MINOR = {8: 1, 3: 2, 10: 3, 5: 4, 0: 5, 7: 6, 2: 7, 9: 8, 4: 9, 11: 10, 6: 11, 1: 12}

_KEY_RE = re.compile(r"^\s*([A-Ga-g])\s*([#♯b♭]?)\s*(m|min|minor|maj|major)?\s*$")


def to_camelot(key: str) -> str:
    """'Em' -> '9A', 'F#' -> '2B'. Returns '' if the key can't be parsed."""
    m = _KEY_RE.match(key or "")
    if not m:
        return ""
    note, acc, quality = m.groups()
    pc = _PITCH[note.upper()]
    if acc in ("#", "♯"):
        pc += 1
    elif acc in ("b", "♭"):
        pc -= 1
    pc %= 12
    if quality and quality.startswith("m") and not quality.startswith("maj"):
        return f"{_MINOR[pc]}A"
    return f"{_MAJOR[pc]}B"


def _parse(c: str) -> tuple[int, str] | None:
    m = re.match(r"^(\d{1,2})([AB])$", c or "")
    return (int(m.group(1)), m.group(2)) if m else None


def distance(a: str, b: str) -> int | None:
    """Steps between two Camelot keys: 0 same, 1 neighbor, larger is a clash."""
    pa, pb = _parse(a), _parse(b)
    if not pa or not pb:
        return None
    d = abs(pa[0] - pb[0]) % 12
    d = min(d, 12 - d)
    return d + (0 if pa[1] == pb[1] else 1)
