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
KEY_CACHE = CACHE / "getsongkey.json"
TAG_CACHE = CACHE / "claude_tags.json"

KEYCHAIN_SERVICE = "getsongbpm"
GETSONGKEY_KEYCHAIN_SERVICE = "getsongkey"
ANTHROPIC_KEYCHAIN_SERVICE = "djx-anthropic"


class ConfigError(RuntimeError):
    pass


def _keychain(service: str) -> str | None:
    r = subprocess.run(
        ["security", "find-generic-password", "-s", service, "-w"],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        return None
    return r.stdout.strip() or None


def _getsong_key(env: str, service: str, site: str, flag: str) -> str:
    """Read a getsong.co API key from the env, else the login Keychain."""
    key = os.environ.get(env) or _keychain(service)
    if key:
        return key.strip()
    raise ConfigError(
        f"No {site} key in the login Keychain under service '{service}'.\n"
        f"Store it with `djx key{flag}` (it prompts for the key). Entries made in the\n"
        "Passwords app live in the iCloud keychain, which this can't read."
    )


def getsongbpm_key() -> str:
    return _getsong_key("GETSONGBPM_API_KEY", KEYCHAIN_SERVICE, "GetSongBPM", "")


def getsongkey_key() -> str:
    return _getsong_key("GETSONGKEY_API_KEY", GETSONGKEY_KEYCHAIN_SERVICE, "GetSongKey", " --getsongkey")


def anthropic_key() -> str | None:
    """Env first, then the Keychain. None lets the SDK use an `ant auth login` profile."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key.strip()
    return _keychain(ANTHROPIC_KEYCHAIN_SERVICE)


def ensure_dirs() -> None:
    for d in (DATA, CACHE, PLAYLISTS):
        d.mkdir(parents=True, exist_ok=True)
