# NoteClaudeToolkit

把「看到的東西」整理成 Claude 讀得懂的素材：兩個小工具，加上一份做法整理。給會用 [Claude Code](https://claude.com/claude-code) 的人。

| 工具 | 做什麼 |
|---|---|
| [NoteAuto](NoteAuto/) | 把你傳給自己的私訊（Telegram Saved Messages、IG / Threads 對話）裡的連結抓下來、截圖，用本機 `claude -p` 下標題／摘要／分類／標籤，做成可搜尋的卡片牆 |
| [YTGrabber](YTGrabber/) | 一支影片連結 → 帶時間戳的逐字稿＋關鍵幀截圖＋指定區域放大裁切，讓 Claude「不用看影片也知道它在做什麼」 |

兩個工具各自獨立，各有自己的 README 和 `CLAUDE.md`。最快的用法：在該工具的資料夾開 Claude Code，請它讀 `CLAUDE.md` 帶你跑一次。

[TECHNIQUES.md](TECHNIQUES.md) 整理了兩個工具裡可以搬去別的專案用的做法，例如用 `claude -p` 拿結構化 JSON 不需要 API key、
擋 prompt injection、仿人節奏抓網頁、讓 Claude 看影片。

## 需要

- [uv](https://docs.astral.sh/uv/)（兩個工具都用 `uv run`，第一次會自動裝好套件）
- NoteAuto：Google Chrome、已登入的 Claude Code（`claude` 指令在 PATH 上）
- YTGrabber：ffmpeg；本地轉錄建議 NVIDIA GPU（沒有就 `--device cpu`）

只在 Windows 上實際跑過。

## 使用前請注意

- 只抓**你自己的**對話和你有權存取的內容。抓網頁要尊重各網站的使用條款；NoteAuto 刻意放慢速度、只讀不寫。
- 抓下來的資料（私訊、截圖、登入狀態）都留在本機的 `data/`、`.profile/` 等資料夾，`.gitignore` 已經排除，不要 commit。
