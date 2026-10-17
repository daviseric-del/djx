"""GetSongBPM client (https://getsongbpm.com/api) with a cache that records misses too.

Limit is 3000 requests an hour; going over blocks the key for an hour, so
requests are spaced out.
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from djx import config, text

BASE = "https://api.getsong.co"
MIN_INTERVAL = 1.25  # seconds between requests, about 2900 an hour


class ApiError(RuntimeError):
    pass


class Client:
    name = "GetSongBPM"
    cache_path = config.BPM_CACHE

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._last = 0.0
        self.requests = 0
        self.cache = json.loads(self.cache_path.read_text()) if self.cache_path.exists() else {}

    def save(self) -> None:
        config.ensure_dirs()
        self.cache_path.write_text(json.dumps(self.cache, indent=1, sort_keys=True))

    def _get(self, path: str, params: dict) -> dict:
        wait = MIN_INTERVAL - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        url = f"{BASE}{path}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"X-API-KEY": self.api_key, "User-Agent": "djx/0.1"})
        self._last = time.monotonic()
        self.requests += 1
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:200]
            if e.code == 401:
                raise ApiError(f"{self.name} rejected the key: {body}") from e
            if e.code == 429:
                raise ApiError(f"{self.name} rate limit hit; the key is blocked for an hour.") from e
            raise ApiError(f"{self.name} HTTP {e.code}: {body}") from e

    def _search(self, type_: str, lookup: str) -> list[dict]:
        data = self._get("/search/", {"type": type_, "lookup": lookup, "limit": 15})
        res = data.get("search")
        return res if isinstance(res, list) else []  # a miss comes back as {"error": "no result"}

    @staticmethod
    def _pick(results: list[dict], want_title: str, want_artist: str) -> dict | None:
        best, best_score = None, 0
        for r in results:
            t = text.fold(text.clean_title(r.get("title", "")))
            a = text.fold(text.primary_artist((r.get("artist") or {}).get("name", "")))
            if t != want_title:
                continue
            score = 2 + (2 if a == want_artist else 1 if want_artist in a or a in want_artist else 0)
            if score > best_score:
                best, best_score = r, score
        # Title alone isn't enough; require some artist agreement.
        return best if best_score >= 3 else None

    def lookup(self, name: str, artist: str, retry_misses: bool = False) -> dict | None:
        title, art = text.key(name, artist)
        ck = f"{title}|{art}"
        if ck in self.cache and not (retry_misses and self.cache[ck]["hit"] is None):
            return self.cache[ck]["hit"]

        clean, primary = text.clean_title(name), text.primary_artist(artist)
        hit = self._pick(self._search("both", f"song:{clean} artist:{primary}"), title, art)
        if hit is None:
            hit = self._pick(self._search("song", clean), title, art)
        if hit is not None and not hit.get("tempo") and hit.get("id"):
            hit = (self._get("/song/", {"id": hit["id"]}).get("song") or hit)

        out = None
        if hit is not None:
            out = {
                "id": hit.get("id"),
                "title": hit.get("title"),
                "artist": (hit.get("artist") or {}).get("name"),
                "tempo": hit.get("tempo"),
                "key_of": hit.get("key_of"),
                "open_key": hit.get("open_key"),
            }
        self.cache[ck] = {"query": [name, artist], "hit": out, "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        return out
