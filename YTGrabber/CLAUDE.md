# YTGrabber

把一支影片連結（或本機影片）變成「不用看影片也知道它在做什麼」的素材包：逐字稿（含時間戳）＋關鍵幀截圖＋指定區域裁切圖。
用法、參數和輸出格式見 `README.md`。

## 用法

```bash
uv sync        # 第一次；套件一律用 uv 管理（uv add / uv run），不用 pip
uv run python grab.py <url|本機影片> --whisper --language en \
  --initial-prompt-file terms.txt --keywords-file keywords.txt \
  --crop panel=0.32,0.07,0.23,0.38
uv run python transcribe_local.py <media> [--model large-v3] [--language zh]   # 只轉錄
```

幫使用者「看」一支影片時：跑完先讀 `out/<id>/transcript.txt` 掌握內容，再挑 `frames/`、`crops/` 裡相關時間點的圖看。

## 架構

- `grab.py`：入口。自己呼叫 yt-dlp 下載（≤1080p；vendor 的 download.py 寫死 ≤720p，軟體介面的小字讀不清）→
  逐字稿（字幕或本地 Whisper）→ 關鍵詞句尾抓 cue 幀＋vendor 的場景偵測抽幀 → 對每個 cue 幀在原始解析度裁切放大。
- `transcribe_local.py`：faster-whisper（CUDA DLL 從 pip 的 `nvidia-*` 套件載入）。
- `vendor/claude-video/`：bradautomates/claude-video 的腳本，**不修改**，只 import 函式
  （`frames.extract_scene_or_uniform / extract_at_timestamps / merge_frames`、`transcribe.parse_vtt`）。
  commit SHA 記在 `NOTICE`；更新時整包覆蓋後重跑一次 grab 驗證。
- **保持領域中立**：關鍵詞、`initial_prompt`、裁切區域全部由呼叫端傳入，這裡不寫死任何領域術語。

臨時要看某個時間點的其他區域，不用改程式，直接 ffmpeg：
`ffmpeg -ss <秒> -i download/video.mp4 -frames:v 1 -vf "crop=iw*W:ih*H:iw*X:ih*Y,scale=iw*2:-2:flags=lanczos" out.jpg`

## 注意

- 下載的影片、模型、輸出都是暫存，不進 git（`out/` 已 ignore）。Whisper 模型快取在 HuggingFace 預設目錄。
- YouTube 自動字幕會有 `&nbsp;` 與術語錯字；grab.py 已 unescape，技術類影片建議一律 `--whisper`。
- IG Reels 需 `--cookies-from-browser`，還沒接。帶帳號 cookie 跑下載工具有被 IG 標記自動化的風險。
- yt-dlp 對 YouTube 常壞：先 `uv lock --upgrade-package yt-dlp && uv sync` 再查。
