"""Choose and order tracks, explaining every transition.

This is the rules-only first pass: a greedy walk that scores each candidate
next track on tempo, key, energy against a planned curve, and artist repeats.
Reading the free-text prompt (mood, region, era) is not wired up yet; for now
the prompt only names the playlist and --from/--genre narrow the pool.
"""

from djx import camelot

LONG_TRACK_SECONDS = 15 * 60

# Energy target (1-5) by position in the playlist: warm up, build, dip, peak, ease off.
CURVE = [(0.0, 2.0), (0.35, 4.0), (0.5, 3.0), (0.8, 5.0), (1.0, 4.0)]


def _f(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def target_energy(pos: float) -> float:
    for (x0, y0), (x1, y1) in zip(CURVE, CURVE[1:]):
        if pos <= x1:
            return y0 + (y1 - y0) * (pos - x0) / (x1 - x0)
    return CURVE[-1][1]


def tempo_ratio(a: float, b: float) -> float:
    """Relative gap, treating half and double time as matches (70 next to 140 is fine)."""
    return min(abs(b * m - a) / a for m in (0.5, 1.0, 2.0))


FEEL = {"slow": 0, "mid": 1, "up": 2}
GUESS_WEIGHT = 0.4  # how much a low-confidence energy or tempo feel counts


def guessed(t: dict) -> bool:
    """Low-confidence tags are educated guesses, not knowledge of the track."""
    return t.get("confidence") == "low"


def _w(*tracks: dict) -> float:
    return GUESS_WEIGHT if any(guessed(t) for t in tracks) else 1.0


def _g(*tracks: dict) -> str:
    return " (guessed)" if any(guessed(t) for t in tracks) else ""


def transition(a: dict, b: dict, pos: float) -> tuple[float, str]:
    cost, why = 0.0, []

    ba, bb = _f(a.get("bpm")), _f(b.get("bpm"))
    fa, fb = FEEL.get(a.get("tempo_feel", "")), FEEL.get(b.get("tempo_feel", ""))
    if ba and bb:
        r = tempo_ratio(ba, bb)
        cost += max(0.0, r - 0.06) * 20
        why.append(f"{ba:.0f}→{bb:.0f} BPM" + (" (half/double time)" if abs(bb - ba) / ba > 0.3 and r < 0.06 else ""))
    elif fa is not None and fb is not None:
        # No BPM on one side: fall back to tempo feel. A feel derived from a real
        # BPM isn't a guess even on a low-confidence track.
        g = [t for t in (a, b) if not t.get("bpm")]
        cost += abs(fa - fb) * 0.8 * _w(*g) + 0.25
        why.append(f"feel {a['tempo_feel']}→{b['tempo_feel']}{_g(*g)}")
    else:
        cost += 0.5
        why.append("tempo unknown")

    d = camelot.distance(a.get("camelot", ""), b.get("camelot", ""))
    if d is not None:
        cost += max(0, d - 1) * 0.6
        why.append(f"{a['camelot']}→{b['camelot']}" + (" same key" if d == 0 else " neighbor" if d == 1 else f" {d} steps"))

    ea, eb = _f(a.get("energy")), _f(b.get("energy"))
    if eb is not None:
        # A guessed energy can't satisfy or violate the curve as strongly, so pull
        # its cost toward the 0.5 charged for an unknown energy.
        wb = _w(b)
        cost += abs(eb - target_energy(pos)) * 0.8 * wb + 0.5 * (1 - wb)
        if ea is not None:
            cost += max(0.0, abs(eb - ea) - 1) * 0.7 * _w(a, b)
            why.append(f"energy {ea:.0f}→{eb:.0f}{_g(a, b)}")
    else:
        cost += 0.5

    if a.get("genre") and b.get("genre") and a["genre"] != b["genre"]:
        cost += 1.0
        why.append(f"genre change ({a['genre']} → {b['genre']})")

    if a.get("artist") == b.get("artist"):
        cost += 1.5
        why.append("same artist back to back")

    if a.get("outro") == "hard stop" and b.get("intro") == "long intro":
        cost += 1.0
        why.append("hard stop into long intro")

    ta, tb = a.get("texture", ""), b.get("texture", "")
    if ta and tb and ta == tb:
        cost -= 0.5
        why.append(f"same texture ({ta})")

    return cost, "; ".join(why)


def build(pool: list[dict], minutes: float) -> list[dict]:
    """Return [{track, reason}] covering about `minutes` of music."""
    pool = [t for t in pool if (_f(t.get("duration")) or 0) < LONG_TRACK_SECONDS]
    if not pool:
        return []
    total = minutes * 60

    # Open on the lowest-energy track we actually know about, else the first.
    first = min(pool, key=lambda t: 3.0 if guessed(t) else (_f(t.get("energy")) or 3.0))
    out = [{"track": first, "reason": "opener: lowest energy in the pool"}]
    used = {first["persistentID"]}
    elapsed = _f(first.get("duration")) or 0

    while elapsed < total:
        left = [t for t in pool if t["persistentID"] not in used]
        if not left:
            break
        pos = elapsed / total
        best = min(left, key=lambda t: transition(out[-1]["track"], t, pos)[0])
        dur = _f(best.get("duration")) or 0
        # Stop rather than overshoot by more than half the next track.
        if elapsed + dur / 2 > total:
            break
        out.append({"track": best, "reason": transition(out[-1]["track"], best, pos)[1]})
        used.add(best["persistentID"])
        elapsed += dur
    return out
