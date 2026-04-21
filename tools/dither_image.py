import argparse
from pathlib import Path

import numpy as np
from PIL import Image


def _pack_bits(bits: np.ndarray) -> bytes:
    h, w = bits.shape
    if w % 8 != 0:
        raise ValueError("width must be a multiple of 8")
    out = bytearray()
    for y in range(h):
        row = bits[y]
        for x in range(0, w, 8):
            byte = 0
            for b in range(8):
                byte = (byte << 1) | int(row[x + b])
            out.append(byte)
    return bytes(out)


def convert(src_path: str, out_path: str, width: int, height: int) -> None:
    img = Image.open(src_path).convert("L")
    img = img.resize((width, height), Image.LANCZOS)
    img = img.convert("1", dither=Image.FLOYDSTEINBERG)
    arr = np.array(img, dtype=np.uint8)
    bits = (arr > 0).astype(np.uint8)
    data = _pack_bits(bits)
    Path(out_path).write_bytes(data)


def main(argv=None):
    p = argparse.ArgumentParser(description="1-bit dither for Badger 2040 W")
    p.add_argument("--in", dest="src", required=True)
    p.add_argument("--out", dest="out", required=True)
    p.add_argument("--width", type=int, required=True)
    p.add_argument("--height", type=int, required=True)
    args = p.parse_args(argv)
    convert(args.src, args.out, args.width, args.height)


if __name__ == "__main__":
    main()
