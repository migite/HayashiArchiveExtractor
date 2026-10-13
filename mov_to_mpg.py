"""Convert the game's movies (video\\*.mov, "MOV1" format) to light MPEG-1 files (.mpg) for ONScripter.

Usage: python mov_to_mpg.py <input_file_or_dir> <output_dir> [--width N] [--quality Q] [--ffmpeg PATH] [--jobs N]

Needs ffmpeg (https://ffmpeg.org/). ONScripter plays MPEG-1 video with MP2 audio (mpegplay), which is cheap to decode.

MOV1 layout (little endian u32)
  +0x00 "MOV1"  +0x08 frame count  +0x0c frames per second (15)  +0x14 width  +0x18 height  +0x1c bits per pixel
  +0x20 file size  +0x28 track count (2)  +0x2c offset of the data area
  +0x30 index: (frame count + 1) records of 24 bytes = index, size, raw size, codec, offset, 0
        records 0 .. n-1 are JPEG frames (codec 2); the last record is the audio track (a KOGG file, see kog_to_ogg.py)
        record offsets are relative to the data area.

The frames are fed to ffmpeg as a Motion JPEG stream and the audio as Ogg Vorbis. The output is
MPEG-1 video at 30 fps (MPEG-1 has no 15 fps, so every frame is shown twice, which costs almost nothing)
scaled down to --width pixels (4:3, default 400) and MP2 audio at 44.1 kHz.
"""
import argparse
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor

from kog_to_ogg import kog_to_ogg

HEADER = struct.Struct("<4sIIIIIIIQII")    # magic .. data area offset, 48 bytes
RECORD = struct.Struct("<6I")


class Mov:
    def __init__(self, data):
        if len(data) < HEADER.size or data[:4] != b"MOV1":
            raise ValueError("not a MOV1 file")
        (_, _, count, fps, _, self.width, self.height, _, size, tracks, base) = HEADER.unpack_from(data, 0)
        if size != len(data) or tracks != 2 or not count or not fps:
            raise ValueError("unexpected header (size %d, %d tracks, %d frames)" % (size, tracks, count))
        if HEADER.size + RECORD.size * (count + 1) > len(data):
            raise ValueError("truncated index")
        self.fps = fps
        recs = [RECORD.unpack_from(data, HEADER.size + RECORD.size * i) for i in range(count + 1)]
        self.frames = []
        for i, (idx, n, _, codec, off, _) in enumerate(recs[:-1]):
            if idx != i or codec != 2 or base + off + n > len(data) or data[base + off:base + off + 2] != b"\xff\xd8":
                raise ValueError("bad video record %d" % i)
            self.frames.append(data[base + off:base + off + n])
        _, n, _, _, off, _ = recs[-1]
        if base + off + n > len(data):
            raise ValueError("bad audio record")
        self.audio = kog_to_ogg(data[base + off:base + off + n])


def output_size(width, height, max_width):
    """Scale down (never up) to max_width, keeping the aspect ratio; both sides even."""
    if width > max_width:
        height = height * max_width // width
        width = max_width
    return width & ~1, height & ~1


def convert_file(args):
    src, dst, max_width, quality, ffmpeg = args
    with open(src, "rb") as f:
        mov = Mov(f.read())
    w, h = output_size(mov.width, mov.height, max_width)
    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    tmp = dst + ".tmp.mpg"
    with tempfile.TemporaryDirectory() as td:
        ogg = os.path.join(td, "audio.ogg")
        with open(ogg, "wb") as f:
            f.write(mov.audio)
        cmd = [ffmpeg, "-v", "error", "-y",
               "-f", "image2pipe", "-c:v", "mjpeg", "-framerate", str(mov.fps), "-i", "-",
               "-i", ogg,
               "-vf", "format=rgb24,colorchannelmixer=rr=0:rb=1:br=1:bb=0,"
                      "scale=%d:%d:flags=lanczos:out_range=tv,fps=30,format=yuv420p" % (w, h),
               "-c:v", "mpeg1video", "-qscale:v", str(quality), "-g", "15", "-bf", "0",
               "-c:a", "mp2", "-b:a", "128k", "-ar", "44100", "-ac", "2",
               "-shortest", "-f", "mpeg", tmp]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            for frame in mov.frames:
                p.stdin.write(frame)
            p.stdin.close()
        except BrokenPipeError:
            pass
        err = p.stderr.read().decode("utf-8", "replace")
        if p.wait() != 0:
            raise RuntimeError(err.strip() or "ffmpeg failed")
    os.replace(tmp, dst)
    return os.path.getsize(dst)


def convert(files, outdir, max_width=400, quality=3, ffmpeg="ffmpeg", jobs=1):
    """Convert .mov files to .mpg. Returns (converted, failed)."""
    os.makedirs(outdir, exist_ok=True)
    tasks = [(p, os.path.join(outdir, os.path.splitext(os.path.basename(p))[0] + ".mpg"), max_width, quality, ffmpeg)
             for p in files]
    failed = 0
    with ProcessPoolExecutor(max_workers=max(1, min(jobs, len(tasks) or 1))) as pool:
        futures = [(t, pool.submit(convert_file, t)) for t in tasks]
        for t, fut in futures:
            try:
                size = fut.result()
                print("%s -> %s (%.1f MB)" % (os.path.basename(t[0]), os.path.basename(t[1]), size / 1048576), flush=True)
            except (ValueError, RuntimeError, OSError) as e:
                failed += 1
                print("%s: %s" % (t[0], e), file=sys.stderr)
    return len(tasks) - failed, failed


def find_ffmpeg(path=None):
    return shutil.which(path or "ffmpeg")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("outdir")
    ap.add_argument("--width", type=int, default=400, help="maximum output width (default 400; the engine scales to the screen)")
    ap.add_argument("--quality", type=int, default=3, help="MPEG-1 quantizer 1 (best) .. 31 (default 3)")
    ap.add_argument("--ffmpeg", help="path of ffmpeg (default: ffmpeg in PATH)")
    ap.add_argument("--jobs", type=int, default=os.cpu_count())
    a = ap.parse_args()
    ffmpeg = find_ffmpeg(a.ffmpeg)
    if not ffmpeg:
        sys.exit("ffmpeg was not found. Install it from https://ffmpeg.org/ or pass --ffmpeg PATH.")
    if os.path.isdir(a.input):
        files = [os.path.join(a.input, f) for f in sorted(os.listdir(a.input)) if f.lower().endswith(".mov")]
    else:
        files = [a.input]
    ok, failed = convert(files, a.outdir, a.width, a.quality, ffmpeg, a.jobs)
    print("%d converted, %d failed" % (ok, failed))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

