"""The enriched library: one CSV you can open and hand-edit.

Hand edits win. Next to library.csv the tool keeps .library.auto.json, the
last value it wrote to each cell. A non-blank cell that differs from that
value was edited by hand, and the tool leaves it alone from then on. Blank
a cell to hand it back to the tool.
"""

import csv
import json

from djx import config

COLUMNS = [
    "persistentID", "name", "artist", "album", "genre", "year", "duration",
    "playedCount", "dateAdded", "favorite",
    "bpm", "key", "camelot", "bpm_source", "key_source",
    "tempo_feel", "energy", "texture", "theme", "intro", "outro", "confidence", "tag_source",
    "notes",
]


class Library:
    def __init__(self, rows: dict[str, dict], auto: dict[str, dict], extra: list[str]):
        self.rows = rows
        self.auto = auto
        self.extra = extra  # columns Eric added himself; kept as-is

    @classmethod
    def load(cls) -> "Library":
        rows, extra = {}, []
        if config.LIBRARY_CSV.exists():
            with config.LIBRARY_CSV.open(newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                extra = [c for c in reader.fieldnames or [] if c not in COLUMNS]
                for r in reader:
                    rows[r["persistentID"]] = {k: (v or "") for k, v in r.items()}
        auto = json.loads(config.LIBRARY_AUTO.read_text()) if config.LIBRARY_AUTO.exists() else {}
        return cls(rows, auto, extra)

    def save(self) -> None:
        config.ensure_dirs()
        cols = COLUMNS + self.extra
        rows = sorted(self.rows.values(), key=lambda r: (r.get("artist", "").lower(), r.get("name", "").lower()))
        tmp = config.LIBRARY_CSV.with_suffix(".csv.tmp")
        with tmp.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow({c: r.get(c, "") for c in cols})
        tmp.replace(config.LIBRARY_CSV)
        config.LIBRARY_AUTO.write_text(json.dumps(self.auto, indent=0, sort_keys=True))

    def is_hand(self, pid: str, field: str) -> bool:
        v = self.rows.get(pid, {}).get(field, "")
        return v != "" and v != self.auto.get(pid, {}).get(field, "")

    def set(self, pid: str, field: str, value) -> bool:
        """Write an automatic value unless the cell was hand-edited."""
        if self.is_hand(pid, field):
            return False
        v = "" if value is None else str(value)
        self.rows.setdefault(pid, {"persistentID": pid})[field] = v
        self.auto.setdefault(pid, {})[field] = v
        return True

    def tracks(self, favorites_only: bool = True) -> list[dict]:
        rows = self.rows.values()
        if favorites_only:
            rows = [r for r in rows if r.get("favorite") == "1"]
        return list(rows)
