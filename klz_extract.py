"""KLZ5 archive extractor (sigma "sviu" engine).

Usage: python klz_extract.py <archive.klz> <output_dir> [--jobs N]

Layout
  header (16 bytes): "KLZ5", u32 entry_count, u32 file_size, u32 0
  entry  (52 bytes): char name[32], u32 stored_size, u32 size_field, u32 mode,
                     u32 offset (relative to end of table), u32 0
  data starts at 16 + 52 * entry_count

Modes (from sviu.exe)
  0: stored as is
  1: LZSS, 2048-byte zero-filled window, write position starts at 0x7e8,
     flags LSB first (1 = literal), match = 2 bytes: pos = b0 | (b1 & 0xe0) << 3,
     length = (b1 & 0x1f) + 2; size_field is the decoded size
  2: prefix XOR, out[i] = in[i] ^ out[i - 1]
"""
import argparse
import itertools
import operator
import os
import struct
import sys
from concurrent.futures import ProcessPoolExecutor


def lz_decode(src):
    ring = bytearray(2048)
    r = 0x7E8
    out = bytearray()
    n = len(src)
    i = 0
    flags = 0
    while True:
        flags >>= 1
        if not flags & 0x100:
            if i >= n:
                break
            flags = src[i] | 0xFF00
            i += 1
        if flags & 1:
            if i >= n:
                break
            c = src[i]
            i += 1
            out.append(c)
            ring[r] = c
            r = (r + 1) & 2047
        else:
            if i + 1 >= n:
                break
            b0 = src[i]
            b1 = src[i + 1]
            i += 2
            p = b0 | (b1 & 0xE0) << 3
            for _ in range((b1 & 0x1F) + 2):
                c = ring[p]
                p = (p + 1) & 2047
                out.append(c)
                ring[r] = c
                r = (r + 1) & 2047
    return bytes(out)


def xor_decode(src):
    return bytes(itertools.accumulate(src, operator.xor))


def decode(data, mode):
    if mode == 0:
        return data
    if mode == 1:
        return lz_decode(data)
    if mode == 2:
        return xor_decode(data)
    raise ValueError("unknown mode %d" % mode)


def extract_entry(args):
    path, base, name, stored, size_field, mode, offset, outdir = args
    with open(path, "rb") as f:
        f.seek(base + offset)
        data = f.read(stored)
    out = decode(data, mode)
    ok = mode != 1 or len(out) == size_field
    with open(os.path.join(outdir, name), "wb") as f:
        f.write(out)
    return name, ok


def extract_archive(archive, outdir, jobs=None):
    """Extract every entry of a KLZ5 archive. Returns (file_count, size_mismatch_count)."""
    os.makedirs(outdir, exist_ok=True)
    with open(archive, "rb") as f:
        head = f.read(16)
        if head[:4] != b"KLZ5":
            raise ValueError("not a KLZ5 archive: %s" % archive)
        count = struct.unpack_from("<I", head, 4)[0]
        table = f.read(52 * count)
    base = 16 + 52 * count
    tasks = []
    for i in range(count):
        e = table[52 * i:52 * (i + 1)]
        name = e[:32].split(b"\0")[0].decode("ascii")
        stored, size_field, mode, offset, _ = struct.unpack_from("<5I", e, 32)
        tasks.append((archive, base, name, stored, size_field, mode, offset, outdir))
    bad = 0
    with ProcessPoolExecutor(jobs or os.cpu_count()) as ex:
        for name, ok in ex.map(extract_entry, tasks, chunksize=4):
            if not ok:
                bad += 1
                print("size mismatch:", name)
    return count, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("archive")
    ap.add_argument("outdir")
    ap.add_argument("--jobs", type=int, default=os.cpu_count())
    a = ap.parse_args()
    try:
        count, bad = extract_archive(a.archive, a.outdir, a.jobs)
    except ValueError as e:
        sys.exit(str(e))
    print("%s: %d files, %d size mismatches" % (a.archive, count, bad))


if __name__ == "__main__":
    main()
