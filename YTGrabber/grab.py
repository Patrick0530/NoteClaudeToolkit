"""Video URL/path → out/<id>/ : transcript.json + frames/ + crops/ + manifest.json.

Frame selection reuses vendor/claude-video (scene-aware + dedup + transcript cues).
We do our own yt-dlp download because vendor's download.py caps at 720p.
"""
import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "vendor" / "claude-video"))
from download import is_url, _pick_subtitle, _pick_video  # noqa: E402
from frames import (auto_fps, extract_at_timestamps, extract_scene_or_uniform,  # noqa: E402
                    get_metadata, merge_frames)
from transcribe import format_transcript, parse_vtt  # noqa: E402


def _has_video_stream(path: Path | None) -> bool:
    """vendor's _pick_video globs video*.webm, which also matches a leftover audio-only video.f251.webm."""
    if not path:
        return False
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=codec_type",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return "video" in r.stdout


def download(url: str, out: Path, sub_langs: str) -> tuple[Path, Path | None, dict]:
    out.mkdir(parents=True, exist_ok=True)
    # second format is the fallback when the split 1080p streams fail (HTTP 500 left only the audio part)
    for fmt in ("bv*[height<=1080]+ba/b[height<=1080]", "b[ext=mp4][height<=1080]/b"):
        if _has_video_stream(_pick_video(out)):
            break
        for partial in out.glob("video.f*.*"):
            partial.unlink()
        subprocess.run([sys.executable, "-m", "yt_dlp", "-N", "8",
                        "-f", fmt, "--merge-output-format", "mp4",
                        "--write-info-json", "--write-subs", "--write-auto-subs",
                        "--sub-langs", sub_langs, "--sub-format", "vtt", "--convert-subs", "vtt",
                        "--no-playlist", "--ignore-errors", "--no-progress", "-o", str(out / "video.%(ext)s"), "--", url])
    video = _pick_video(out)
    if not _has_video_stream(video):
        raise SystemExit(f"yt-dlp produced no video with a picture in {out}")
    info_path = out / "video.info.json"
    info = json.loads(info_path.read_text(encoding="utf-8")) if info_path.exists() else {}
    return video, _pick_subtitle(out), info


def cue_times(segments: list[dict], keywords: list[str]) -> list[float]:
    """Segment end time for every segment mentioning a keyword (the action usually lands as the sentence ends)."""
    if not keywords:
        return []
    pat = re.compile("|".join(re.escape(k) for k in keywords), re.IGNORECASE)
    return sorted({s["end"] for s in segments if pat.search(s["text"])})


def crop(video: Path, t: float, region: list[float], dest: Path, scale: int) -> None:
    x, y, w, h = region  # fractions of the source frame, resolution-independent
    vf = f"crop=iw*{w}:ih*{h}:iw*{x}:ih*{y},scale=iw*{scale}:-2:flags=lanczos"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{t:.3f}",
                    "-i", str(video), "-frames:v", "1", "-vf", vf, "-q:v", "2", str(dest)], check=True)


def read_list(path: str | None) -> list[str]:
    if not path:
        return []
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", help="URL or local video path")
    ap.add_argument("--out", default="out", help="parent dir; results go to <out>/<video id>/")
    ap.add_argument("--sub-langs", default="en.*")
    ap.add_argument("--whisper", action="store_true", help="ignore captions, always transcribe locally")
    ap.add_argument("--model", default="large-v3-turbo")
    ap.add_argument("--language")
    ap.add_argument("--initial-prompt-file")
    ap.add_argument("--device", default="cuda", choices=["cuda", "cpu"], help="for local Whisper")
    ap.add_argument("--keywords-file", help="one keyword per line; matching segments get a cue frame")
    ap.add_argument("--resolution", type=int, default=1024)
    ap.add_argument("--max-frames", type=int, default=100, help="scene frames cap (cue frames are extra)")
    ap.add_argument("--crop", action="append", default=[], metavar="NAME=X,Y,W,H",
                    help="fractional region cropped from each cue frame at source res, e.g. params=0.7,0.1,0.3,0.6")
    ap.add_argument("--crop-scale", type=int, default=2)
    a = ap.parse_args()

    if is_url(a.source):
        vid = re.sub(r"\W", "_", a.source.rstrip("/").split("v=")[-1].split("/")[-1])[:40]
        work = Path(a.out) / vid
        video, vtt, info = download(a.source, work / "download", a.sub_langs)
    else:
        video, vtt, info = Path(a.source).resolve(), None, {}
        work = Path(a.out) / video.stem
    work, video = work.resolve(), video.resolve()
    work.mkdir(parents=True, exist_ok=True)
    meta = get_metadata(str(video))

    # 1. transcript
    if vtt and not a.whisper:
        segments, t_source = parse_vtt(str(vtt)), f"captions ({vtt.name})"
        for s in segments:  # vendor parse_vtt leaves &nbsp; etc.
            s["text"] = " ".join(html.unescape(s["text"]).split())
    else:
        from transcribe_local import transcribe
        prompt = Path(a.initial_prompt_file).read_text(encoding="utf-8") if a.initial_prompt_file else None
        segments, t_source = transcribe(str(video), a.model, a.language, prompt, a.device), f"whisper-local ({a.model})"
    (work / "transcript.json").write_text(json.dumps(segments, ensure_ascii=False, indent=1), encoding="utf-8")
    (work / "transcript.txt").write_text(format_transcript(segments), encoding="utf-8")
    print(f"[grab] transcript: {len(segments)} segments via {t_source}", file=sys.stderr)

    # 2. frames: scene-aware + keyword cues
    cues = cue_times(segments, read_list(a.keywords_file))
    cue_frames, _ = extract_at_timestamps(str(video), work / "frames", cues, resolution=a.resolution)
    fps, target = auto_fps(meta["duration_seconds"], max_frames=a.max_frames)
    scene_frames, fmeta = extract_scene_or_uniform(str(video), work / "frames", fps=fps, target_frames=target,
                                                   resolution=a.resolution, max_frames=a.max_frames)
    frames = merge_frames(scene_frames, cue_frames)
    print(f"[grab] frames: {len(scene_frames)} {fmeta['engine']} + {len(cue_frames)} cue", file=sys.stderr)

    # 3. crops at source resolution for each cue
    crops = []
    if a.crop:
        (work / "crops").mkdir(exist_ok=True)
        for spec in a.crop:
            name, _, nums = spec.partition("=")
            region = [float(n) for n in nums.split(",")]
            for f in cue_frames:
                dest = work / "crops" / f"{name}_{Path(f['path']).stem}.jpg"
                crop(video, f["timestamp_seconds"], region, dest, a.crop_scale)
                crops.append({"t": f["timestamp_seconds"], "name": name, "path": dest.relative_to(work).as_posix()})

    manifest = {
        "source": a.source,
        "title": info.get("title") or video.name,
        "uploader": info.get("uploader") or info.get("channel"),
        "duration": meta["duration_seconds"],
        "video": {"path": video.relative_to(work).as_posix() if video.is_relative_to(work) else str(video),
                  "width": meta["width"], "height": meta["height"]},
        "transcript_source": t_source,
        "frames": [{"t": f["timestamp_seconds"], "reason": f["reason"],
                    "path": Path(f["path"]).relative_to(work).as_posix()} for f in frames],
        "crops": crops,
    }
    (work / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(work)


if __name__ == "__main__":
    main()
