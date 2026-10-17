# djx

Turns your Apple Music favorites into sequenced playlists, ordered so each transition works: tempo, key, energy, texture, and how one track ends and the next begins. Every transition comes with a one-line reason, so you can disagree with it.

Tempo and key data comes from **[GetSongBPM](https://getsongbpm.com)**, used under their free API terms.

## Setup

Requires macOS with Music.app, Python 3.11+, and [uv](https://docs.astral.sh/uv/).

```bash
uv tool install --editable .
```

This puts `djx` on your PATH and keeps its virtualenv outside the project folder, which matters if the folder lives in iCloud Drive.

### GetSongBPM API key

1. Register at [getsongbpm.com/api](https://getsongbpm.com/api). The free tier requires a public backlink to GetSongBPM; this README is it.
2. Store the key in your login Keychain:

   ```bash
   djx key
   ```

   This runs `security add-generic-password -s getsongbpm`, which prompts for the key. Setting `GETSONGBPM_API_KEY` in the environment overrides the Keychain.

### macOS permissions

The first `djx export` or `djx push` makes macOS ask whether your terminal may control Music. Allow it. If you said no, turn it back on under System Settings > Privacy & Security > Automation.

### Favorites must be in your library

`djx` reads favorites from your library. If Music's "Add favorite songs to library" setting is off, starred songs you never added won't show up.

## Usage

```bash
djx export                                      # favorites -> data/library.csv
djx import-profiles unplayed_rap_profiles.csv   # optional: merge hand-written profiles
djx enrich                                      # tempo + key from GetSongBPM
djx build "late-night Memphis" --minutes 45 --genre Rap
djx push playlists/late-night-memphis.json      # create or replace it in Music
```

- `export` only rewrites what changed. Tracks you unfavorite stay in the file with `favorite=0`.
- `enrich` only looks up tracks without a tempo, and caches every answer, including misses, in `data/cache.nosync/`. Use `--retry-misses` to ask again. The API allows 3000 requests an hour, so the first full run takes a while.
- `build --from unplayed` limits the pool to tracks with a play count of 0.
- `push --version` makes `Name v2`, `Name v3`, and so on, instead of replacing `Name`. Replacing empties the existing playlist in place, so it keeps its spot in your sidebar.
- `push` matches tracks by persistent ID, then falls back to name and artist, and lists every track it couldn't find.

## Editing the library

`data/library.csv` is yours to edit. Any cell you change is kept from then on, and the tool won't overwrite it. To hand a cell back to the tool, blank it. The tool's last-written values live in `data/.library.auto.json`.

| column | filled by |
|---|---|
| persistentID, name, artist, album, genre, year, duration, playedCount, dateAdded, favorite | `export` |
| bpm, key, camelot, bpm_source | `enrich` (GetSongBPM) |
| tempo_feel | `enrich` derives it from bpm when empty |
| energy (1-5), texture, theme, intro, outro, confidence | profiles; Claude tagging is planned |
| notes | you |

## Status

`build` is a rules-only first pass. It aims for an energy curve, keeps neighboring tempos within about 6% (half and double time count), prefers neighboring Camelot keys, and avoids the same artist twice in a row. It doesn't read the meaning of the prompt yet; that's next, along with Claude-written tags for energy, texture and theme.
