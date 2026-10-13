"""One-touch extraction of the whole game data.

Reads every *.klz in <root>/pack and writes the result under <root>/unpacked
(<root> defaults to the folder above tools; change it with --root):

  <name>.klz            -> unpacked/<name>/            (raw extracted files)
  scripts  (*.spr)      -> unpacked/<name>_decoded/    (SVS1 decoded scripts)
                           unpacked/<name>_text/       (UTF-8 text of the string pool)
  sounds   (*.kog)      -> unpacked/<name>_ogg/        (standard Ogg Vorbis)
  <root>/video/*.mov    -> unpacked/movie/             (light MPEG-1 movies for ONScripter, needs ffmpeg)

Usage: python extract_all.py [--root DIR] [--pack DIR] [--out DIR] [--only NAME ...] [--jobs N] [--no-verify]
                             [--no-movies] [--ffmpeg PATH] [--movie-width N]
"""
import argparse
import os
import sys
import time

from klz_extract import extract_archive
from kog_to_ogg import convert
from mov_to_mpg import convert as convert_movies, find_ffmpeg
from svs_decode import decode_dir

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_files(directory, ext):
    return [os.path.join(directory, f) for f in sorted(os.listdir(directory)) if f.lower().endswith(ext)]


def process(archive, out_root, jobs, verify):
    name = os.path.splitext(os.path.basename(archive))[0]
    raw_dir = os.path.join(out_root, name)
    problems = 0

    t = time.time()
    print("[%s] extracting %s ..." % (name, os.path.basename(archive)), flush=True)
    count, bad = extract_archive(archive, raw_dir, jobs)
    problems += bad
    print("[%s] %d files -> %s (%.1fs)" % (name, count, raw_dir, time.time() - t), flush=True)

    if find_files(raw_dir, ".spr"):
        dec_dir = os.path.join(out_root, name + "_decoded")
        txt_dir = os.path.join(out_root, name + "_text")
        n = decode_dir(raw_dir, dec_dir, txt_dir)
        print("[%s] %d scripts -> %s, %s" % (name, n, dec_dir, txt_dir), flush=True)

    kogs = find_files(raw_dir, ".kog")
    if kogs:
        ogg_dir = os.path.join(out_root, name + "_ogg")
        t = time.time()
        ok, failed = convert(kogs, ogg_dir, verify)
        problems += failed
        print("[%s] %d ogg files (%d failed) -> %s (%.1fs)" % (name, ok, failed, ogg_dir, time.time() - t), flush=True)
    return problems


def process_movies(root, out_root, jobs, ffmpeg, width):
    """Convert <root>/video/*.mov. Returns the number of problems (a missing ffmpeg is only reported)."""
    video = os.path.join(root, "video")
    files = find_files(video, ".mov") if os.path.isdir(video) else []
    if not files:
        return 0
    exe = find_ffmpeg(ffmpeg)
    if not exe:
        print("[movie] ffmpeg was not found, the %d movies in %s are skipped. Install ffmpeg "
              "(https://ffmpeg.org/) or use --ffmpeg PATH, then run again with --only movie." % (len(files), video))
        return 0
    movie_dir = os.path.join(out_root, "movie")
    t = time.time()
    print("[movie] converting %d movies ..." % len(files), flush=True)
    ok, failed = convert_movies(files, movie_dir, width, 3, exe, jobs)
    print("[movie] %d mpg files (%d failed) -> %s (%.1fs)" % (ok, failed, movie_dir, time.time() - t), flush=True)
    return failed


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=ROOT, help="game folder that contains pack\\ (default: the folder above tools)")
    ap.add_argument("--pack", default="pack", help="folder with the .klz files, relative to --root (default: pack)")
    ap.add_argument("--out", default="unpacked", help="output folder, relative to --root (default: unpacked)")
    ap.add_argument("--only", nargs="+", metavar="NAME", help="only these archives, e.g. script voice (movie = the movies)")
    ap.add_argument("--jobs", type=int, default=os.cpu_count(), help="worker processes")
    ap.add_argument("--no-verify", action="store_true", help="skip the Ogg CRC check")
    ap.add_argument("--no-movies", action="store_true", help="do not convert video\\*.mov")
    ap.add_argument("--ffmpeg", help="path of ffmpeg for the movies (default: ffmpeg in PATH)")
    ap.add_argument("--movie-width", type=int, default=400, help="maximum movie width in pixels (default: 400)")
    a = ap.parse_args()

    root = os.path.abspath(a.root)
    pack = os.path.join(root, a.pack)
    out = os.path.join(root, a.out)
    wanted = {n.lower().removesuffix(".klz") for n in a.only} if a.only else None
    do_movies = not a.no_movies and (wanted is None or "movie" in wanted)
    archives = find_files(pack, ".klz") if os.path.isdir(pack) else []
    if wanted is not None:
        archives = [p for p in archives if os.path.splitext(os.path.basename(p))[0].lower() in wanted]
    if not archives and not do_movies:
        sys.exit("pack folder not found: %s" % pack if not os.path.isdir(pack) else "no .klz archives to process in %s" % pack)

    start = time.time()
    problems = 0
    for archive in archives:
        problems += process(archive, out, a.jobs, not a.no_verify)
    if do_movies:
        problems += process_movies(root, out, a.jobs, a.ffmpeg, a.movie_width)
    print("Done in %.1fs, %d problem(s). Output: %s" % (time.time() - start, problems, out))
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
