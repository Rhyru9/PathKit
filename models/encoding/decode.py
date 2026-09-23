"""
decode.py - Iterative decoding of URL path tokens.

Handles the layered encoding seen in the data:
    raw:  Asmunandar%3D3AM%3D3A%3D3A
    url:  Asmunandar=3AM=3A=3A      (%3D -> =)
    hex:  Asmunandar:M::             (=3A -> :)
"""

import re
from urllib.parse import unquote

from .constants import HEX_ENCODE_RE, URL_ENCODE_RE


def url_decode(s: str) -> str:
    """Decode %XX percent-encoding to characters."""
    return unquote(s, encoding="utf-8", errors="replace")


def hex_decode(s: str) -> str:
    """
    Decode =XX in-path hex encoding to characters.

    Only decodes when the resulting character is a known delimiter
    (: . _ = + / space). This avoids corrupting query values like
    ``?npsn=10800463`` (where ``=10`` is a value digit pair, not hex).
    """
    delimiters = set(":._=+/ -")

    def _sub(m):
        c = chr(int(m.group(1), 16))
        if c in delimiters:
            return c
        return m.group(0)  # keep as-is (value, not delimiter encoding)

    return HEX_ENCODE_RE.sub(_sub, s)


def _decode_path(raw: str, max_layers: int) -> str:
    """Decode only a path, where ``=XX`` routing escapes are meaningful."""
    s = raw
    for _ in range(max_layers):
        nxt = hex_decode(url_decode(s))
        if nxt == s:
            break
        s = nxt
    return s


def decode(raw: str, max_layers: int = 5) -> str:
    """
    Fully decode a token: apply url_decode -> hex_decode iteratively until
    the string stops changing (or max_layers is reached).
    """
    path, separator, query = raw.partition("?")
    decoded_path = _decode_path(path, max_layers)
    if not separator:
        return decoded_path
    return f"{decoded_path}?{url_decode(query)}"


def decode_layers(raw: str, max_layers: int = 5) -> list[str]:
    """
    Return the intermediate decoding layers (for debugging / inspection).
    First element is the raw token, last is the fully-decoded form.
    """
    layers = [raw]
    path, separator, query = raw.partition("?")
    s = path
    for _ in range(max_layers):
        nxt = hex_decode(url_decode(s))
        if nxt == s:
            break
        layers.append(f"{nxt}?{url_decode(query)}" if separator else nxt)
        s = nxt
    return layers
