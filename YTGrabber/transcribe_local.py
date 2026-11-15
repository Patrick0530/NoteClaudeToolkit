"""Local Whisper transcription (faster-whisper). Output segments match vendor claude-video: [{start, end, text}]."""
import argparse
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

# pip 的 nvidia-* wheel 把 DLL 放在 site-packages/nvidia/*/bin，Windows 不會自己找到
if sys.platform == "win32":
    import nvidia
    for bin_dir in Path(nvidia.__path__[0]).glob("*/bin"):
        os.add_dll_directory(str(bin_dir))
        os.environ["PATH"] = f"{bin_dir}{os.pathsep}{os.environ['PATH']}"

from faster_whisper import WhisperModel


def transcribe(media: str, model: str = "large-v3-turbo", language: str | None = None,
               initial_prompt: str | None = None, device: str = "cuda") -> list[dict]:
    compute = "float16" if device == "cuda" else "int8"
    whisper = WhisperModel(model, device=device, compute_type=compute)
    segments, info = whisper.transcribe(media, language=language, initial_prompt=initial_prompt,
                                        vad_filter=True,
                                        # without this, one repeated phrase feeds the next window and
                                        # long videos degrade into "Two. Two. Two." loops
                                        condition_on_previous_text=False)
    print(f"[transcribe] {model} on {device}, language={info.language}", file=sys.stderr)
    return [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in segments]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("media")
    ap.add_argument("--model", default="large-v3-turbo")
    ap.add_argument("--language")
    ap.add_argument("--initial-prompt-file")
    ap.add_argument("--device", default="cuda", choices=["cuda", "cpu"])
    a = ap.parse_args()
    prompt = Path(a.initial_prompt_file).read_text(encoding="utf-8") if a.initial_prompt_file else None
    segs = transcribe(a.media, a.model, a.language, prompt, a.device)
    json.dump(segs, sys.stdout, ensure_ascii=False, indent=1)
