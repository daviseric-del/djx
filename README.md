# djx

Turns your Apple Music favorites into sequenced playlists, ordered so each transition works: tempo, key, energy, texture, and how one track ends and the next begins. Every transition comes with a one-line reason, so you can disagree with it.

Tempo and key data comes from **[GetSongBPM](https://getsongbpm.com)** and **[GetSongKey](https://getsongkey.com)**, used under their free API terms.

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

### GetSongKey API key

GetSongKey fills in key (and tempo, if still missing) for tracks GetSongBPM didn't place. It's the same API with its own key.

1. Register at [getsongkey.com/api](https://getsongkey.com/api). The free tier requires a public backlink to GetSongKey; this README is it.
2. Store the key:

   ```bash
   djx key --getsongkey
   ```

   This saves it under Keychain service `getsongkey`. `GETSONGKEY_API_KEY` in the environment overrides the Keychain.

### Anthropic API key (for tags)

`djx enrich` asks Claude (`claude-opus-5-5`) to describe each track's tempo feel, energy, texture, theme, intro and outro. These come from Claude's knowledge of the songs, not from listening, and every track gets an honest confidence rating. Get a key at [platform.claude.com](https://platform.claude.com), then:

```bash
djx key --anthropic
```

`ANTHROPIC_API_KEY` in the environment, or an `ant auth login` profile, also works. Tracks go 25 to a request, so tagging 700 tracks takes about 30 calls.

### macOS permissions

The first `djx export` or `djx push` makes macOS ask whether your terminal may control Music. Allow it. If you said no, turn it back on under System Settings > Privacy & Security > Automation.

### Favorites must be in your library

`djx` reads favorites from your library. If Music's "Add favorite songs to library" setting is off, starred songs you never added won't show up.

## Usage

```bash
djx export                                      # favorites -> data/library.csv
djx import-profiles unplayed_rap_profiles.csv   # optional: merge hand-written profiles
djx enrich                                      # tempo + key from GetSongBPM/GetSongKey, then tags
djx build "late-night Memphis" --minutes 45 --genre Rap
djx push playlists/late-night-memphis.json      # create or replace it in Music
```

- `export` only rewrites what changed. Tracks you unfavorite stay in the file with `favorite=0`.
- `enrich` runs three steps. First it looks up tempo and key on GetSongBPM for tracks that don't have them, caching every answer, including misses, in `data/cache.nosync/` (use `--retry-misses` to ask again). The API allows 3000 requests an hour, so the first full run takes a while. Next it asks GetSongKey about tracks that still have no key, the same way, with its own key and cache. Then it asks Claude to tag tracks with empty tag fields, starting with the ones GetSongBPM missed. Tags only fill blanks; they never replace a value from GetSongBPM, a profile, or your own edits. Use `--skip-bpm`, `--skip-key` or `--skip-tags` to skip a step.
- `build --from unplayed` limits the pool to tracks with a play count of 0.
- `push --version` makes `Name v2`, `Name v3`, and so on, instead of replacing `Name`. Replacing empties the existing playlist in place, so it keeps its spot in your sidebar.
- `push` matches tracks by persistent ID, then falls back to name and artist, and lists every track it couldn't find.

## Editing the library

`data/library.csv` is yours to edit. Any cell you change is kept from then on, and the tool won't overwrite it. To hand a cell back to the tool, blank it. The tool's last-written values live in `data/.library.auto.json`.

| column | filled by |
|---|---|
| persistentID, name, artist, album, genre, year, duration, playedCount, dateAdded, favorite | `export` |
| bpm, key, camelot, bpm_source, key_source | `enrich` (GetSongBPM, then GetSongKey) |
| tempo_feel | `enrich` derives it from bpm when empty |
| energy (1-5), texture, theme, intro, outro, confidence, tag_source | `enrich` (Claude), or imported profiles |
| notes | you |

## Status

`build` is a rules-only first pass. It aims for an energy curve, keeps neighboring tempos within about 6% (half and double time count), prefers neighboring Camelot keys, and avoids the same artist twice in a row. It doesn't read the meaning of the prompt yet; that's next.
