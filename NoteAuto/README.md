# NoteAuto

你平常看到有用的東西，是不是都順手傳給自己（Telegram Saved Messages、IG 或 Threads 私訊給自己的分身帳號）？
NoteAuto 把這些私訊抓下來，打開裡面的連結截圖，再用本機的 `claude -p` 下標題、摘要、分類、標籤，做成可搜尋的卡片牆。

全部就是 `fetch.py` 一支，用 `uv run fetch.py --help` 看所有指令。

## 流程

```
tg / web  →  resolve  →  enrich  →  look  →  merge / retag  →  wall  →  serve
抓私訊       開連結截圖   模型整理    看封面圖   標籤收斂         卡片牆    開給手機看
```

`auto` 會把 resolve 之後的步驟一路跑到完。

## 第一次設定

```bash
# Telegram：到 https://my.telegram.org 申請 API，在這個資料夾建 .env：
#   TG_API_ID=...
#   TG_API_HASH=...
uv run fetch.py tg                     # 第一次會問手機號碼與驗證碼

# IG / Threads：網址是你在網頁版打開那段對話時的網址
uv run fetch.py web ig https://www.instagram.com/direct/t/<對話id>/
uv run fetch.py web threads https://www.threads.com/messages/t/<對話id>
# 第一次會跳出 Chrome 視窗，請手動登入（之後沿用 .profile/）

uv run fetch.py auto                   # 很慢是刻意的，放背景跑
uv run fetch.py wall                   # 產生 data/wall.html，用瀏覽器打開
```

## 常用指令

| 指令 | 作用 |
|---|---|
| `find "regex1" "regex2"` | 翻卡片：每個 regex 都要中（AND），同一個裡用 `\|` 表示或，不分大小寫 |
| `pin 檔案.json` | 把一次查詢結果置頂到卡片牆最上面（格式見 `pin()` 的說明） |
| `serve [--minutes 10]` | 在 `127.0.0.1:8765` 開卡片牆；搭配 `tailscale serve --bg 8765` 給自己的手機看 |
| `check` | 自我檢查，改完程式先跑 |

## 想改成自己的

- **大分類**：改 `CATEGORIES`，再刪掉 `data/notes.jsonl` 重跑 enrich。
- **整理的方向**：改 `NOTE_PROMPT`。現在的版本特別在意硬體型號、互動裝置、創作類內容，換成你在意的東西。
- **速度**：`PAGE_WAIT`、`BATCH`、`REST`。調快容易被 IG 限流。
- **模型**：`MODEL`（預設 haiku）；看圖的 look 用 sonnet。

## 資料

全部留在本機，`.gitignore` 已經排除：

| 檔案 | 內容 |
|---|---|
| `data/{telegram,ig,threads}.jsonl` | 私訊，只會往後加 |
| `data/pages.jsonl` | 解析過的連結 |
| `data/notes.jsonl` | 模型整理的筆記 |
| `data/vocab.json`、`data/tags.json` | 固定標籤清單和標籤對照 |
| `data/shots/`、`data/covers/` | 截圖和封面 |
| `data/wall.html`、`data/review.html` | 卡片牆、待查清單 |
| `.profile/`、`.env`、`.telegram.session*` | 登入狀態和金鑰，等同帳號密碼 |

要重做某一筆：刪掉 jsonl 裡那一行再重跑。
