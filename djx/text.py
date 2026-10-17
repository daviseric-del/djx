"""Normalizing titles and artists so different spellings still match."""

import re
import unicodedata

_PAREN = re.compile(r"\s*[\(\[][^\)\]]*(feat\.?|ft\.?|with |remaster|explicit|version|bonus track|remix|edit)[^\)\]]*[\)\]]", re.I)
_DASH_SUFFIX = re.compile(r"\s+-\s+.*(remaster|version|edit|mix).*$", re.I)


def fold(s: str) -> str:
    """Lowercase, straighten quotes, drop accents and punctuation."""
    s = (s or "").replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9*$ ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def clean_title(s: str) -> str:
    """Strip '(feat. X)', '[Bonus Track]', ' - 2010 Remaster' and similar."""
    s = _PAREN.sub("", s or "")
    s = _DASH_SUFFIX.sub("", s)
    return s.strip()


def primary_artist(s: str) -> str:
    """'21 Savage, Offset & Metro Boomin' -> '21 Savage'."""
    return re.split(r"\s*(?:,|&| feat\.? | ft\.? | x | and )\s*", s or "", maxsplit=1, flags=re.I)[0].strip()


def key(name: str, artist: str) -> tuple[str, str]:
    return fold(clean_title(name)), fold(primary_artist(artist))
