import pytest

from src.core.base62 import decode_base62, encode_base62


def test_encode() -> None:
    assert encode_base62(0) == "0"
    assert encode_base62(10) == "a"
    assert encode_base62(61) == "Z"
    assert encode_base62(62) == "10"
    assert encode_base62(125380) == "wCg"


def test_decode() -> None:
    assert decode_base62("0") == 0
    assert decode_base62("a") == 10
    assert decode_base62("wCg") == 125380


def test_neg_value_encode() -> None:
    """Negative value"""
    with pytest.raises(ValueError):
        encode_base62(-1)

    with pytest.raises(ValueError):
        encode_base62(-100)


def test_invalid_decode() -> None:
    """Empty string, Spaces, Accents, Special symbols, Dashes"""
    with pytest.raises(ValueError):
        decode_base62("")
    with pytest.raises(ValueError):
        decode_base62("a b")
    with pytest.raises(ValueError):
        decode_base62("a#b")
    with pytest.raises(ValueError):
        decode_base62("aàb")
    with pytest.raises(ValueError):
        decode_base62("a-b")
