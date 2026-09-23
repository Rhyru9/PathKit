"""
decode.py - Iterative decoding of URL path tokens.

Handles the layered encoding seen in the data:
    raw:  Asmunandar%3D3AM%3D3A%3D3A
    url:  Asmunandar=3AM=3A=3A      (%3D -> =)
    hex:  Asmunandar:M::             (=3A -> :)
"""

import re

from .constants import HEX_ENCODE_RE, URL_ENCODE_RE


def url_decode(s: str) -> str:
    """Decode %XX percent-encoding to characters."""
    return re.sub(
        r"%([0-9A-Fa-f]{2})",
        lambda m: chr(int(m.group(1), 16)),
        s,
    )


def hex_decode(s: str) -> str:
    """
    Decode =XX in-path hex encoding to characters.

    Only decodes when the resulting character is non-alphanumeric (a
    delimiter such as : . _ =). This avoids corrupting query-string
    values like ?page=20 (where "20" is a literal value, not hex).
    """
    def _sub(m):
        c = chr(int(m.group(1), 16))
        if c.isalnum():
            return m.group(0)  # keep as-is (looks like a value, not encoding)
        return c

    return HEX_ENCODE_RE.sub(_sub, s)


def decode(raw: str, max_layers: int = 5) -> str:
    """
    Fully decode a token: apply url_decode -> hex_decode iteratively until
    the string stops changing (or max_layers is reached).
    """
    s = raw
    for _ in range(max_layers):
        nxt = hex_decode(url_decode(s))
        if nxt == s:
            break
        s = nxt
    return s


def decode_layers(raw: str, max_layers: int = 5) -> list[str]:
    """
    Return the intermediate decoding layers (for debugging / inspection).
    First element is the raw token, last is the fully-decoded form.
    """
    layers = [raw]
    s = raw
    for _ in range(max_layers):
        nxt = hex_decode(url_decode(s))
        if nxt == s:
            break
        layers.append(nxt)
        s = nxt
    return layers
