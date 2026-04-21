from pathlib import Path

import pytest
from PIL import Image

from tools.dither_image import convert


def _make_image(tmp_path: Path, w: int, h: int) -> Path:
    img = Image.new("RGB", (w, h), color="white")
    for y in range(h):
        for x in range(w):
            v = int(255 * (x / w))
            img.putpixel((x, y), (v, v, v))
    p = tmp_path / "src.png"
    img.save(p)
    return p


def test_output_byte_count_matches_packed_size(tmp_path):
    src = _make_image(tmp_path, 128, 128)
    out = tmp_path / "out.bin"
    convert(str(src), str(out), width=128, height=128)
    assert out.stat().st_size == 128 * 128 // 8


def test_all_black_produces_all_ones(tmp_path):
    # Pimoroni image() draws set bits with current pen, so an all-black source
    # should yield 0xFF bytes (every pixel becomes a drawn-black pixel).
    black = Image.new("L", (32, 8), color=0)
    src = tmp_path / "black.png"
    black.save(src)
    out = tmp_path / "out.bin"
    convert(str(src), str(out), width=32, height=8)
    data = out.read_bytes()
    assert data == b"\xff" * 32


def test_all_white_produces_all_zeros(tmp_path):
    white = Image.new("L", (32, 8), color=255)
    src = tmp_path / "white.png"
    white.save(src)
    out = tmp_path / "out.bin"
    convert(str(src), str(out), width=32, height=8)
    data = out.read_bytes()
    assert data == b"\x00" * 32


def test_resize_to_target_dims(tmp_path):
    src = _make_image(tmp_path, 600, 600)
    out = tmp_path / "out.bin"
    convert(str(src), str(out), width=128, height=128)
    assert out.stat().st_size == 128 * 128 // 8


def test_cli_entrypoint(tmp_path, monkeypatch):
    src = _make_image(tmp_path, 64, 64)
    out = tmp_path / "cli.bin"

    from tools import dither_image
    dither_image.main(["--in", str(src), "--out", str(out), "--width", "64", "--height", "64"])

    assert out.stat().st_size == 64 * 64 // 8
