"""Base62 encoding and decoding algorithms.
Alphabet definition:
  0..9 (digits, 10 chars)
  a..z (lowercase, 26 chars)
  A..Z (uppercase, 26 chars)
"""

BASE62_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(BASE62_ALPHABET)  # 62


def encode_base62(num: int) -> str:
    """Encodes a positive integer into a Base62 string representation."""
    str_encode = ""
    if num == 0:
        str_encode = "0"
    elif num < 0:
        raise ValueError("Can't transform a number <0 to string.")

    while num > 0:
        r = num % 62
        num = num // 62
        str_encode += BASE62_ALPHABET[r]

    str_encode = str_encode[::-1]
    return str_encode


def decode_base62(code: str) -> int:
    """Decodes a Base62 string back into its original integer value."""
    num = 0
    if not code:
        raise ValueError("Code cannot be empty.")
    for char in code:
        try:
            val = BASE62_ALPHABET.index(char)
        except ValueError:
            raise ValueError(f"Char '{char}' is outside BASE62_ALPHABET.")
        num = num * BASE + val
    return num
