"""Descriptive tags from Claude's knowledge of the songs (no listening).

Claude is asked for tempo feel, energy, texture, theme, intro and outro, and
told to say confidence: low rather than invent a description for a song it
doesn't know. Answers are cached, keyed like the GetSongBPM cache.
"""

import json
from datetime import datetime, timezone

import anthropic

from djx import config, text

MODEL = "claude-opus-5-5"
BATCH = 25

INTROS = ["cold open", "short intro", "long intro", "skit", "unknown"]
OUTROS = ["hard stop", "fade", "long outro", "skit", "unknown"]

SYSTEM = """You tag songs for a playlist sequencer. The sequencer orders tracks so each transition works: tempo, energy, sonic texture, theme, and how one song ends and the next begins.

For each track, answer from what you actually know about that recording. You have not heard the audio file.

- tempo_feel: slow, mid or up, as a listener feels it. Rap at 140+ BPM with half-time drums usually feels slow or mid.
- energy: 1 (hushed, sparse) to 5 (peak, aggressive, party).
- texture: a short phrase about the production and sound, like "dark Memphis keys", "sparse Neptunes drums", "jangly 60s folk-rock".
- theme: a few words on what the song is about.
- intro: cold open, short intro, long intro, skit, or unknown.
- outro: hard stop, fade, long outro, skit, or unknown.
- confidence: high if you know this specific recording well; med if you know the artist and era well enough to describe it reliably but not this exact track; low if you are guessing.

When you don't know a song, say so: confidence low, texture and theme "unknown", intro and outro "unknown", and tempo_feel and energy as your best guess from the artist's typical style. A wrong confident description is worse than an honest unknown, because the user tunes playlists by disagreeing with your reasons.

Return one entry per input track, using the id given."""

SCHEMA = {
    "type": "object",
    "properties": {
        "tracks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "tempo_feel": {"type": "string", "enum": ["slow", "mid", "up"]},
                    "energy": {"type": "integer", "enum": [1, 2, 3, 4, 5]},
                    "texture": {"type": "string"},
                    "theme": {"type": "string"},
                    "intro": {"type": "string", "enum": INTROS},
                    "outro": {"type": "string", "enum": OUTROS},
                    "confidence": {"type": "string", "enum": ["high", "med", "low"]},
                },
                "required": ["id", "tempo_feel", "energy", "texture", "theme", "intro", "outro", "confidence"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["tracks"],
    "additionalProperties": False,
}


class TagError(RuntimeError):
    pass


def _describe(i: int, r: dict) -> str:
    parts = [f'id={i}', f'"{r.get("name", "")}"', f'by {r.get("artist", "")}']
    if r.get("album"):
        parts.append(f'from "{r["album"]}"')
    if r.get("year"):
        parts.append(f'({r["year"]})')
    if r.get("genre"):
        parts.append(f'genre {r["genre"]}')
    if r.get("bpm"):
        parts.append(f'{r["bpm"]} BPM')
    return " ".join(parts)


class Tagger:
    def __init__(self):
        key = config.anthropic_key()
        # With no key, the SDK falls back to ANTHROPIC_AUTH_TOKEN or an `ant auth login` profile.
        self.client = anthropic.Anthropic(api_key=key) if key else anthropic.Anthropic()
        if not (key or self.client.auth_token or self.client.credentials):
            raise TagError(
                f"No Anthropic API key in the Keychain under service '{config.ANTHROPIC_KEYCHAIN_SERVICE}'.\n"
                "Store it with `djx key --anthropic`, or set ANTHROPIC_API_KEY."
            )
        self.cache = json.loads(config.TAG_CACHE.read_text()) if config.TAG_CACHE.exists() else {}
        self.requests = 0

    def save(self) -> None:
        config.ensure_dirs()
        config.TAG_CACHE.write_text(json.dumps(self.cache, indent=1, sort_keys=True, ensure_ascii=False))

    @staticmethod
    def _ck(r: dict) -> str:
        return "|".join(text.key(r.get("name", ""), r.get("artist", "")))

    def cached(self, r: dict) -> dict | None:
        hit = self.cache.get(self._ck(r))
        return hit["tags"] if hit else None

    def tag_batch(self, rows: list[dict]) -> dict[int, dict]:
        """Tag up to BATCH tracks in one request. Returns {index in rows: tags}."""
        listing = "\n".join(_describe(i, r) for i, r in enumerate(rows))
        try:
            resp = self.client.beta.messages.create(
                model=MODEL,
                max_tokens=16000,
                # Route policy declines to a fallback model instead of losing the batch.
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                output_config={"effort": "medium", "format": {"type": "json_schema", "schema": SCHEMA}},
                system=SYSTEM,
                messages=[{"role": "user", "content": f"Tag these {len(rows)} tracks:\n\n{listing}"}],
            )
        except anthropic.AuthenticationError as e:
            raise TagError("Anthropic rejected the API key. Store one with `djx key --anthropic`.") from e
        except anthropic.RateLimitError as e:
            raise TagError("Anthropic rate limit hit; rerun later and cached tags will be kept.") from e
        except anthropic.APIConnectionError as e:
            raise TagError(f"Couldn't reach the Anthropic API: {e}") from e
        except anthropic.APIStatusError as e:
            raise TagError(f"Anthropic API error {e.status_code}: {e.message}") from e
        self.requests += 1

        if resp.stop_reason == "refusal":
            return {}
        if resp.stop_reason == "max_tokens":
            raise TagError("Tagging response was cut off; lower the batch size.")
        body = next(b.text for b in resp.content if b.type == "text")
        out = {}
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        for t in json.loads(body)["tracks"]:
            try:
                i = int(t.pop("id"))
            except (KeyError, ValueError):
                continue
            if 0 <= i < len(rows):
                out[i] = t
                self.cache[self._ck(rows[i])] = {
                    "query": [rows[i].get("name"), rows[i].get("artist")],
                    "tags": t,
                    "model": resp.model,
                    "at": now,
                }
        return out
