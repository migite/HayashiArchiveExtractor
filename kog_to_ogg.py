"""Convert KOGG (.kog) files to standard Ogg Vorbis (.ogg).

Usage: python kog_to_ogg.py <input_file_or_dir> <output_dir> [--verify]

A .kog file is a plain Ogg Vorbis stream with a prefix header (sviu.exe / kogg.dll):
  +0x00 "KOGG", +0x04 u32 header size (0x24), +0x0c u32 PCM size in bytes,
  +0x10 WAVEFORMATEX-like fields (format, channels, rate, byte rate, align, bits)
The Ogg stream starts at the header size offset, so the conversion just strips the header.
--verify also checks the Ogg page structure and CRCs of the converted stream.
"""
import argparse
import os
import struct
import sys


def _crc_table():
    table = []
    for i in range(256):
        r = i << 24
        for _ in range(8):
            r = ((r << 1) ^ 0x04C11DB7) & 0xFFFFFFFF if r & 0x80000000 else (r << 1) & 0xFFFFFFFF
        table.append(r)
    return table


_CRC = _crc_table()


def ogg_crc(data):
    c = 0
    for x in data:
        c = ((c << 8) & 0xFFFFFFFF) ^ _CRC[(c >> 24) ^ x]
    return c


def verify_ogg(d):
    pos = 0
    while pos < len(d):
        if d[pos:pos + 4] != b"OggS" or pos + 27 > len(d):
            return False
        nseg = d[pos + 26]
        size = 27 + nseg + sum(d[pos + 27:pos + 27 + nseg])
        page = bytearray(d[pos:pos + size])
        stored = struct.unpack_from("<I", page, 22)[0]
        page[22:26] = b"\0\0\0\0"
        if len(page) != size or ogg_crc(page) != stored:
            return False
        pos += size
    return True


def kog_to_ogg(data, verify=False):
    if data[:4] != b"KOGG":
        raise ValueError("not a KOGG file")
    header_size = struct.unpack_from("<I", data, 4)[0]
    ogg = data[header_size:]
    if ogg[:4] != b"OggS":
        raise ValueError("no Ogg stream after the KOGG header")
    if verify and not verify_ogg(ogg):
        raise ValueError("Ogg page/CRC check failed")
    return ogg


def convert(files, outdir, verify=False):
    """Convert .kog files to .ogg. Returns (converted, failed)."""
    os.makedirs(outdir, exist_ok=True)
    failed = 0
    for path in files:
        try:
            with open(path, "rb") as f:
                ogg = kog_to_ogg(f.read(), verify)
        except ValueError as e:
            failed += 1
            print("%s: %s" % (path, e), file=sys.stderr)
            continue
        out = os.path.join(outdir, os.path.splitext(os.path.basename(path))[0] + ".ogg")
        with open(out, "wb") as f:
            f.write(ogg)
    return len(files) - failed, failed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("outdir")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    if os.path.isdir(a.input):
        files = [os.path.join(a.input, f) for f in sorted(os.listdir(a.input)) if f.lower().endswith(".kog")]
    else:
        files = [a.input]
    ok, failed = convert(files, a.outdir, a.verify)
    print("%d converted, %d failed" % (ok, failed))


if __name__ == "__main__":
    main()
