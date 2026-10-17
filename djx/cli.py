"""djx: Apple Music favorites into sequenced playlists."""

import argparse
import collections
import csv
import getpass
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

from djx import camelot, config, getsongbpm, getsongkey, music, sequence, tagger, text
from djx.library import Library


def cmd_key(args) -> int:
    """Store an API key in the login Keychain (security prompts for it)."""
    if args.anthropic:
        service = config.ANTHROPIC_KEYCHAIN_SERVICE
    elif args.getsongkey:
        service = config.GETSONGKEY_KEYCHAIN_SERVICE
    else:
        service = config.KEYCHAIN_SERVICE
    r = subprocess.run(["security", "add-generic-password", "-U", "-s", service, "-a", getpass.getuser(), "-w"])
    if r.returncode == 0:
        print(f"Saved to Keychain as service '{service}'.")
    return r.returncode


def cmd_export(args) -> int:
    flag, tracks = music.export_favorites()
    lib = Library.load()
    seen = set()
    for t in tracks:
        pid = t["persistentID"]
        seen.add(pid)
        for k in ("name", "artist", "album", "genre", "year", "playedCount", "dateAdded"):
            lib.set(pid, k, t.get(k))
        lib.set(pid, "duration", f"{float(t.get('duration') or 0):.0f}")
        lib.set(pid, "favorite", "1")
    # Keep unfavorited tracks (and any hand edits on them), just flag them.
    gone = [pid for pid, r in lib.rows.items() if pid not in seen and r.get("favorite") == "1"]
    for pid in gone:
        lib.set(pid, "favorite", "0")
    lib.save()
    print(f"Exported {len(tracks)} favorites (property: {flag}) to {config.LIBRARY_CSV}")
    if gone:
        print(f"{len(gone)} tracks are no longer favorited; kept with favorite=0.")
    return 0


def cmd_import_profiles(args) -> int:
    """Load hand-written profiles (like unplayed_rap_profiles.csv), matched by name and artist."""
    lib = Library.load()
    index = {}
    for pid, r in lib.rows.items():
        index.setdefault(text.key(r.get("name", ""), r.get("artist", "")), []).append(pid)
    fields = {"tempo_feel": "tempo_feel", "energy_1to5": "energy", "energy": "energy", "texture": "texture",
              "theme": "theme", "intro": "intro", "outro": "outro", "confidence": "confidence"}
    matched, missing, ambiguous = 0, [], []
    with open(args.csv, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = row.get("name") or row.get("track") or ""
            pids = index.get(text.key(name, row.get("artist", "")), [])
            if not pids:
                missing.append(f"{row.get('artist')} - {name}")
                continue
            if len(pids) > 1:
                ambiguous.append(f"{row.get('artist')} - {name} ({len(pids)} copies, all updated)")
            for pid in pids:
                for src, dst in fields.items():
                    if row.get(src):
                        lib.set(pid, dst, row[src])
            matched += 1
    lib.save()
    print(f"Imported {matched} profiles.")
    for m in ambiguous:
        print(f"  duplicate: {m}")
    for m in missing:
        print(f"  not in library: {m}")
    return 0 if not missing else 1


def _tempo_feel(bpm: float) -> str:
    # Rap at 140+ usually feels half time.
    if bpm >= 130:
        bpm /= 2
    return "slow" if bpm < 85 else "mid" if bpm < 105 else "up"


TAG_FIELDS = ["tempo_feel", "energy", "texture", "theme", "intro", "outro", "confidence"]


def cmd_enrich(args) -> int:
    lib = Library.load()
    if not lib.rows:
        print("Library is empty; run `djx export` first.", file=sys.stderr)
        return 1
    if not args.skip_bpm:
        _enrich_bpm(lib, args)
    if not args.skip_key:
        _enrich_key(lib, args)
    if not args.skip_tags:
        _enrich_tags(lib, args)
    return 0


def _enrich_tags(lib: Library, args) -> None:
    t = tagger.Tagger()
    todo = [r for r in lib.tracks() if any(not r.get(f) for f in TAG_FIELDS)]
    # Tracks GetSongBPM couldn't place need tags most, so they go first.
    todo.sort(key=lambda r: bool(r.get("bpm")))
    if args.limit:
        todo = todo[: args.limit]

    def apply(r: dict, tags: dict) -> None:
        pid = r["persistentID"]
        wrote = False
        for f in TAG_FIELDS:
            # Fill gaps only: never replace a value from GetSongBPM, a profile, or you.
            if not lib.rows[pid].get(f) and tags.get(f) not in (None, ""):
                wrote |= lib.set(pid, f, tags[f])
        if wrote:
            lib.set(pid, "tag_source", tagger.MODEL)

    fresh = []
    for r in todo:
        hit = t.cached(r)
        if hit:
            apply(r, hit)
        else:
            fresh.append(r)

    tagged, untagged = len(todo) - len(fresh), []
    try:
        for start in range(0, len(fresh), tagger.BATCH):
            batch = fresh[start : start + tagger.BATCH]
            got = t.tag_batch(batch)
            for i, r in enumerate(batch):
                if i in got:
                    apply(r, got[i])
                    tagged += 1
                else:
                    untagged.append(r)
            lib.save()
            t.save()
            print(f"  tagged {min(start + tagger.BATCH, len(fresh))}/{len(fresh)}  ({t.requests} Claude calls)")
    finally:
        lib.save()
        t.save()

    conf = collections.Counter(lib.rows[r["persistentID"]].get("confidence", "") for r in todo)
    print(
        f"Tagged {tagged} of {len(todo)} tracks ({t.requests} Claude calls). "
        f"Confidence: {conf.get('high', 0)} high, {conf.get('med', 0)} med, {conf.get('low', 0)} low."
    )
    for r in untagged:
        print(f"  not tagged (declined or missing from reply): {r['artist']} - {r['name']}")


def _enrich_bpm(lib: Library, args) -> None:
    client = getsongbpm.Client(config.getsongbpm_key())
    todo = [r for r in lib.tracks() if not r.get("bpm")]
    if args.limit:
        todo = todo[: args.limit]
    hits, misses = 0, []
    try:
        for i, r in enumerate(todo, 1):
            pid = r["persistentID"]
            res = client.lookup(r["name"], r["artist"], retry_misses=args.retry_misses)
            if res and res.get("tempo"):
                bpm = float(res["tempo"])
                lib.set(pid, "bpm", f"{bpm:.0f}")
                lib.set(pid, "key", res.get("key_of") or "")
                lib.set(pid, "camelot", camelot.to_camelot(res.get("key_of") or ""))
                lib.set(pid, "bpm_source", "getsongbpm")
                lib.set(pid, "key_source", "getsongbpm" if res.get("key_of") else "")
                if not lib.rows[pid].get("tempo_feel"):
                    lib.set(pid, "tempo_feel", _tempo_feel(bpm))
                hits += 1
            else:
                misses.append(r)
            if i % 25 == 0:
                lib.save()
                client.save()
                print(f"  {i}/{len(todo)}  ({client.requests} API calls)")
    finally:
        lib.save()
        client.save()
    print(f"Enriched {hits} of {len(todo)} tracks with tempo and key ({client.requests} API calls).")
    if misses:
        print(f"No GetSongBPM match for {len(misses)} (cached; use --retry-misses to ask again):")
        for r in misses[:20]:
            print(f"  {r['artist']} - {r['name']}")
        if len(misses) > 20:
            print(f"  ...and {len(misses) - 20} more (blank bpm in data/library.csv)")


def _enrich_key(lib: Library, args) -> None:
    """Fill key (and tempo, if still blank) from GetSongKey for tracks GetSongBPM left without one."""
    client = getsongkey.Client(config.getsongkey_key())
    todo = [r for r in lib.tracks() if not r.get("key")]
    if args.limit:
        todo = todo[: args.limit]
    hits, misses = 0, []
    try:
        for i, r in enumerate(todo, 1):
            pid = r["persistentID"]
            res = client.lookup(r["name"], r["artist"], retry_misses=args.retry_misses)
            if res and res.get("key_of"):
                lib.set(pid, "key", res["key_of"])
                lib.set(pid, "camelot", camelot.to_camelot(res["key_of"]))
                lib.set(pid, "key_source", "getsongkey")
                if res.get("tempo") and not lib.rows[pid].get("bpm"):
                    bpm = float(res["tempo"])
                    lib.set(pid, "bpm", f"{bpm:.0f}")
                    lib.set(pid, "bpm_source", "getsongkey")
                    if not lib.rows[pid].get("tempo_feel"):
                        lib.set(pid, "tempo_feel", _tempo_feel(bpm))
                hits += 1
            else:
                misses.append(r)
            if i % 25 == 0:
                lib.save()
                client.save()
                print(f"  {i}/{len(todo)}  ({client.requests} API calls)")
    finally:
        lib.save()
        client.save()
    print(f"Enriched {hits} of {len(todo)} tracks with key from GetSongKey ({client.requests} API calls).")
    if misses:
        print(f"No GetSongKey match for {len(misses)} (cached; use --retry-misses to ask again):")
        for r in misses[:20]:
            print(f"  {r['artist']} - {r['name']}")
        if len(misses) > 20:
            print(f"  ...and {len(misses) - 20} more (blank key in data/library.csv)")


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60] or "playlist"


def cmd_build(args) -> int:
    lib = Library.load()
    pool = lib.tracks()
    if args.source == "unplayed":
        pool = [t for t in pool if t.get("playedCount") in ("", "0")]
    if args.genre:
        want = {g.lower() for g in args.genre}
        pool = [t for t in pool if t.get("genre", "").lower() in want]
    seq = sequence.build(pool, args.minutes)
    if not seq:
        print("No tracks matched.", file=sys.stderr)
        return 1

    name = args.name or args.prompt
    out = {
        "name": name,
        "prompt": args.prompt,
        "minutes": round(sum(float(s["track"].get("duration") or 0) for s in seq) / 60, 1),
        "tracks": [
            {k: s["track"].get(k, "") for k in ("persistentID", "name", "artist", "bpm", "camelot", "energy")}
            | {"reason": s["reason"]}
            for s in seq
        ],
    }
    config.ensure_dirs()
    path = config.PLAYLISTS / f"{_slug(name)}.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False))

    print(f"{name}  ({len(seq)} tracks, {out['minutes']} min)\n")
    for i, t in enumerate(out["tracks"], 1):
        print(f"{i:>3}. {t['artist']} - {t['name']}")
        print(f"       {t['reason']}")
    rel = path.relative_to(config.HOME) if path.is_relative_to(config.HOME) else path
    print(f"\nSaved {path}\nPush it with: djx push {shlex.quote(str(rel))}")
    return 0


def cmd_push(args) -> int:
    pl = json.loads(Path(args.playlist).read_text())
    final, misses = music.push_playlist(pl["name"], pl["tracks"], versioned=args.version)
    added = len(pl["tracks"]) - len(misses)
    print(f"{final}: added {added} of {len(pl['tracks'])}")
    for t, why in misses:
        print(f"  missing ({why}): {t.get('artist')} - {t.get('name')}")
    return 0 if not misses else 1


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="djx", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("key", help="store your GetSongBPM (or GetSongKey, or Anthropic) API key in the Keychain")
    which = s.add_mutually_exclusive_group()
    which.add_argument("--getsongkey", action="store_true", help="store the GetSongKey API key instead")
    which.add_argument("--anthropic", action="store_true", help="store the Anthropic API key instead")
    s.set_defaults(fn=cmd_key)
    sub.add_parser("export", help="read favorites from Music into data/library.csv").set_defaults(fn=cmd_export)

    s = sub.add_parser("import-profiles", help="merge a hand-written profile CSV into the library")
    s.add_argument("csv")
    s.set_defaults(fn=cmd_import_profiles)

    s = sub.add_parser("enrich", help="add tempo and key from GetSongBPM and GetSongKey, then tags from Claude")
    s.add_argument("--retry-misses", action="store_true", help="re-query GetSongBPM/GetSongKey for tracks that had no match")
    s.add_argument("--limit", type=int, help="only process this many tracks per step (for testing)")
    s.add_argument("--skip-bpm", action="store_true", help="skip the GetSongBPM step")
    s.add_argument("--skip-key", action="store_true", help="skip the GetSongKey step")
    s.add_argument("--skip-tags", action="store_true", help="skip the Claude tagging step")
    s.set_defaults(fn=cmd_enrich)

    s = sub.add_parser("build", help="choose and sequence tracks into playlists/<name>.json")
    s.add_argument("prompt")
    s.add_argument("--from", dest="source", choices=["favorites", "unplayed"], default="favorites")
    s.add_argument("--genre", action="append", help="limit to a Music genre; repeatable")
    s.add_argument("--minutes", type=float, default=45)
    s.add_argument("--name", help="playlist name (defaults to the prompt)")
    s.set_defaults(fn=cmd_build)

    s = sub.add_parser("push", help="create or replace the playlist in Music")
    s.add_argument("playlist", help="a JSON file written by `djx build`")
    s.add_argument("--version", action="store_true", help="make 'Name v2', 'v3'... instead of replacing")
    s.set_defaults(fn=cmd_push)

    args = p.parse_args(argv)
    try:
        sys.exit(args.fn(args))
    except (config.ConfigError, music.MusicError, getsongbpm.ApiError, tagger.TagError) as e:
        print(f"djx: {e}", file=sys.stderr)
        sys.exit(1)
