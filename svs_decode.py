"""Decode SVS1 script files (*.spr) and export their string pool as UTF-8 text.

Usage: python svs_decode.py <input_dir> <decoded_dir> <text_dir>

SVS1 header (little endian u32)
  +0x04 code offset, +0x08 string/data pool offset, +0x0c total size after decoding,
  +0x10 mode (1 = payload compressed, 0 = plain), +0x14 header size,
  +0x1c compressed payload size
The payload after the header uses the same LZSS as KLZ mode 1.
The decoded file keeps the header with mode set to 0. The text export lists the
NUL separated Shift-JIS strings of the pool (from +0x08 to the end), one per line.
"""
import os
import struct
import sys

from klz_extract import lz_decode


def decode_svs(b):
    if b[:4] != b"SVS1":
        raise ValueError("not SVS1")
    mode, hdr, _, clen = struct.unpack_from("<4I", b, 0x10)
    total = struct.unpack_from("<I", b, 0xC)[0]
    if mode == 0:
        return b
    if mode != 1:
        raise ValueError("unknown mode %d" % mode)
    payload = lz_decode(b[hdr:hdr + clen])
    if len(payload) != total - hdr:
        raise ValueError("size mismatch")
    head = bytearray(b[:hdr])
    struct.pack_into("<I", head, 0x10, 0)
    return bytes(head) + payload


def export_text(b):
    pool = struct.unpack_from("<I", b, 8)[0]
    lines = []
    for s in b[pool:].split(b"\0"):
        if s:
            lines.append(s.decode("cp932", "replace").replace("\r", "\\r").replace("\n", "\\n"))
    return lines


def decode_dir(src, dec_dir, txt_dir):
    """Decode every .spr in src. Returns the number of files processed."""
    os.makedirs(dec_dir, exist_ok=True)
    os.makedirs(txt_dir, exist_ok=True)
    count = 0
    for fn in sorted(os.listdir(src)):
        if not fn.lower().endswith(".spr"):
            continue
        with open(os.path.join(src, fn), "rb") as f:
            full = decode_svs(f.read())
        with open(os.path.join(dec_dir, fn), "wb") as f:
            f.write(full)
        with open(os.path.join(txt_dir, fn[:-4] + ".txt"), "w", encoding="utf-8", newline="\r\n") as f:
            f.write("\n".join(export_text(full)) + "\n")
        count += 1
    return count


def main():
    if len(sys.argv) != 4:
        sys.exit("usage: python svs_decode.py <input_dir> <decoded_dir> <text_dir>")
    print("%d files" % decode_dir(*sys.argv[1:4]))


if __name__ == "__main__":
    main()
