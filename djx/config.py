"""Paths and secrets."""

import os
import subprocess
from pathlib import Path

# The repo root holds data/ and playlists/. DJX_HOME overrides it.
HOME = Path(os.environ.get("DJX_HOME", Path(__file__).resolve().parents[1]))
DATA = HOME / "data"
# .nosync keeps iCloud Drive from syncing the cache, which churns on every run.
CACHE = DATA / "cache.nosync"
PLAYLISTS = HOME / "playlists"

LIBRARY_CSV = DATA / "library.csv"
LIBRARY_AUTO = DATA / ".library.auto.json"
BPM_CACHE = CACHE / "getsongbpm.json"

KEYCHAIN_SERVICE = "getsongbpm"


class ConfigError(RuntimeError):
    pass


def getsongbpm_key() -> str:
    """Read the API key from the env, else the login Keychain."""
    key = os.environ.get("GETSONGBPM_API_KEY")
    if key:
        return key.strip()
    r = subprocess.run(
        ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0 or not r.stdout.strip():
        raise ConfigError(
            f"No GetSongBPM key in the login Keychain under service '{KEYCHAIN_SERVICE}'.\n"
            "Store it with `djx key` (it prompts for the key). Entries made in the\n"
            "Passwords app live in the iCloud keychain, which this can't read."
        )
    return r.stdout.strip()


def ensure_dirs() -> None:
    for d in (DATA, CACHE, PLAYLISTS):
        d.mkdir(parents=True, exist_ok=True)
