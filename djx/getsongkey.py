"""GetSongKey client (https://getsongkey.com/api).

GetSongKey is GetSongBPM's sister site on the same API, so this reuses that
client with its own key and cache.
"""

from djx import config, getsongbpm

ApiError = getsongbpm.ApiError


class Client(getsongbpm.Client):
    name = "GetSongKey"
    cache_path = config.KEY_CACHE
