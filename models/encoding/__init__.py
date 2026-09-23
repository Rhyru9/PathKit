"""
models.encoding - Encoding detection + iterative decoding for URL path tokens.

Runs BEFORE any identifier detector or the slug classifier. Detects the
encoding type (urlencode, hex, base64, unicode, double) and decodes the token
to plain text so downstream detectors see canonical content.

Usage
-----
    from models.encoding import detect_type, decode, decode_layers

    detect_type("Asmunandar%3D3AM%3D3A%3D3A")   # -> "urlencode"
    decode("Asmunandar%3D3AM%3D3A%3D3A")         # -> "Asmunandar:M::"
    decode_layers("setjen%3D5Fpdspk")            # -> ["setjen%3D5Fpdspk",
                                                 #     "setjen=5Fpdspk",
                                                 #     "setjen_pdspk"]
"""

from .decode import decode, decode_layers, hex_decode, url_decode
from .detect import detect_type, has_encoding

__all__ = [
    "detect_type",
    "has_encoding",
    "decode",
    "decode_layers",
    "url_decode",
    "hex_decode",
]
