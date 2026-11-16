# YTGrabber — 把一支影片變成「不用看也知道它在做什麼」的素材包

給 Claude 讀的影片前處理工具：一個 YouTube 連結（或本機影片）進去，出來一個資料夾——
**帶時間戳的逐字稿 + 關鍵時刻截圖 + 指定區域的放大裁切**，外加一份 `manifest.json` 描述全部內容。

原本是為了把 TouchDesigner 教學影片轉成可跑的網路，
但本身**完全不知道 TD 的存在**：關鍵詞、術語提示、裁切區域都由呼叫端傳入，任何教學／會議／操作錄影都能用。

## 跑起來

需要 [uv](https://docs.astral.sh/uv/) 與 ffmpeg（在 PATH 上）。本地轉錄建議 NVIDIA GPU（沒有就加 `--device cpu`，慢但能用）。

```bash
uv sync
uv run python grab.py "https://www.youtube.com/watch?v=..." --whisper --language en \
  --initial-prompt-file terms.txt \
  --keywords-file keywords.txt \
  --crop panel=0.32,0.07,0.23,0.38
```

| 參數 | 作用 |
| --- | --- |
| `--whisper` | 不用 YouTube 字幕，改本地 Whisper（large-v3-turbo）。技術類影片建議開：自動字幕沒標點、術語常拆錯 |
| `--language` / `--model` | 中文建議 `--language zh --model large-v3` |
| `--device cpu` | 沒有 NVIDIA GPU 時用（慢很多） |
| `--initial-prompt-file` | 領域術語清單，餵給 Whisper 提升專有名詞辨識 |
| `--keywords-file` | 一行一個關鍵詞；講到這些詞的句子，在句尾多抓一張 cue 截圖 |
| `--crop NAME=X,Y,W,H` | 對每張 cue 截圖，從**原始解析度**裁切指定區域並放大 ×2；座標是畫面比例（0–1），可重複 |
| `--sub-langs` | 抓哪些語言的字幕（預設 `en.*`） |
| `--resolution` / `--max-frames` | 截圖寬度（預設 1024）與場景截圖上限（預設 100，cue 截圖另計） |

只要逐字稿：`uv run python transcribe_local.py video.mp4 --language en > transcript.json`

6 分鐘影片：走字幕約 20 秒，走本地 Whisper 約 1 分鐘（RTX 3070，含首次模型下載）。

## 輸出

結果放在**執行時所在資料夾**的 `out/`（可用 `--out` 改）。想把素材和程式分開放，就在素材資料夾裡跑：
`uv run --project <這個資料夾> python <這個資料夾>/grab.py …`。

```
out/<video id>/
  manifest.json      # 來源、標題、長度、解析度、逐字稿來源、每張截圖的時間與原因、每張裁切圖
  transcript.json    # [{start, end, text}]（秒）
  transcript.txt     # [mm:ss] text——人或 Claude 快速掃讀用
  frames/            # frame_*.jpg（場景變化 / 均勻取樣）、cue_*.jpg（關鍵詞時刻），寬 1024
  crops/             # <name>_cue_*.jpg，原始解析度裁切 ×2
  download/          # video.mp4（≤1080p）、字幕、info.json
```

## 怎麼做的

- **抽幀**沿用 [bradautomates/claude-video](https://github.com/bradautomates/claude-video)（MIT）的場景偵測、
  去重與時間點截圖，原封 vendor 在 `vendor/claude-video/`，只 import 函式、不改一行；來源 commit 記在 `NOTICE`。
- **下載自己做**：claude-video 寫死 ≤720p，軟體介面裡的小字讀不清，這裡改抓 ≤1080p。
- **本地轉錄**：faster-whisper + CUDA（cuBLAS / cuDNN 由 uv 以 pip wheel 安裝，啟動時自動加入 DLL 路徑），
  音訊不離開本機。
- **cue 截圖取句尾**：講「把它接到…」「調成 0.95」時，畫面上的動作通常在句子講完時才完成。

## 限制

- IG Reels 需要登入 cookies（`yt-dlp --cookies-from-browser`），尚未接。
- yt-dlp 對 YouTube 的相容性常隨網站改版失效：`uv lock --upgrade-package yt-dlp && uv sync`。
- 目前只在 Windows + NVIDIA 驗證過。
