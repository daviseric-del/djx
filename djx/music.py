"""Talk to Music.app. Reads go through JXA, writes go through AppleScript.

JXA can create a playlist but fails with -1700 on every `duplicate`, so
anything that writes to Music is AppleScript.
"""

import json
import subprocess

EXPORT_JS = r"""
function run() {
  const M = Application("Music");
  const lib = M.libraryPlaylists[0];
  let t, flag;
  // Newer macOS calls it favorited; older releases call it loved.
  try { t = lib.tracks.whose({favorited: true}); t.name(); flag = "favorited"; }
  catch (e) { t = lib.tracks.whose({loved: true}); flag = "loved"; }
  const f = ["persistentID", "name", "artist", "album", "genre", "year",
             "duration", "playedCount", "dateAdded"];
  // Bulk property fetches return arrays and are far faster than per-track reads.
  const cols = {};
  f.forEach(k => { cols[k] = t[k](); });
  const rows = [];
  for (let i = 0; i < cols.name.length; i++) {
    const r = {};
    f.forEach(k => {
      let v = cols[k][i];
      if (v instanceof Date) v = v.toISOString();
      r[k] = v;
    });
    rows.push(r);
  }
  return JSON.stringify({flag: flag, tracks: rows});
}
"""

PUSH_TEMPLATE = r"""
on findTrack(pid, n, a)
	tell application "Music"
		if pid is not "" then
			set hits to (every track of library playlist 1 whose persistent ID is pid)
			if (count of hits) > 0 then return item 1 of hits
		end if
		set hits to (every track of library playlist 1 whose name is n and artist is a)
		if (count of hits) > 0 then return item 1 of hits
	end tell
	return missing value
end findTrack

set plName to "%(name)s"
set versioned to %(versioned)s
set theList to %(tracks)s
set out to ""
tell application "Music"
	if versioned and (exists user playlist plName) then
		set i to 2
		repeat while exists user playlist (plName & " v" & i)
			set i to i + 1
		end repeat
		set plName to plName & " v" & i
	end if
	if exists user playlist plName then
		-- Empty it in place so the playlist keeps its folder and sidebar spot.
		set pl to user playlist plName
		delete every track of pl
	else
		set pl to make new user playlist with properties {name:plName}
	end if
end tell
set idx to 0
repeat with x in theList
	set idx to idx + 1
	try
		set tr to my findTrack(item 1 of x, item 2 of x, item 3 of x)
		if tr is missing value then
			set out to out & "miss" & tab & idx & tab & "not found" & linefeed
		else
			tell application "Music" to duplicate tr to pl
			set out to out & "ok" & tab & idx & linefeed
		end if
	on error e
		set out to out & "miss" & tab & idx & tab & e & linefeed
	end try
end repeat
return "name" & tab & plName & linefeed & out
"""


class MusicError(RuntimeError):
    pass


def _osascript(args: list[str], script: str) -> str:
    r = subprocess.run(["osascript", *args, "-"], input=script, capture_output=True, text=True)
    if r.returncode != 0:
        msg = r.stderr.strip()
        if "-1743" in msg or "Not authorized" in msg:
            msg += (
                "\nAllow your terminal to control Music in System Settings > "
                "Privacy & Security > Automation."
            )
        raise MusicError(msg)
    return r.stdout


def export_favorites() -> tuple[str, list[dict]]:
    """Return (flag property used, list of favorited tracks)."""
    data = json.loads(_osascript(["-l", "JavaScript"], EXPORT_JS))
    return data["flag"], data["tracks"]


def _as_str(s) -> str:
    return '"' + str(s or "").replace("\\", "\\\\").replace('"', '\\"') + '"'


def push_playlist(name: str, tracks: list[dict], versioned: bool = False) -> tuple[str, list[tuple[dict, str]]]:
    """Create or refill a playlist. Returns (final name, [(track, reason)] for misses)."""
    items = ", ".join(
        "{" + ", ".join(_as_str(t.get(k)) for k in ("persistentID", "name", "artist")) + "}"
        for t in tracks
    )
    script = PUSH_TEMPLATE % {
        "name": str(name).replace("\\", "\\\\").replace('"', '\\"'),
        "versioned": "true" if versioned else "false",
        "tracks": "{" + items + "}",
    }
    final_name = name
    misses = []
    for line in _osascript([], script).splitlines():
        parts = line.split("\t")
        if parts[0] == "name":
            final_name = parts[1]
        elif parts[0] == "miss":
            misses.append((tracks[int(parts[1]) - 1], parts[2] if len(parts) > 2 else ""))
    return final_name, misses
