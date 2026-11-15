# NoteAuto

使用者把看到的東西用 Telegram（Saved Messages）、IG、Threads 私訊傳給自己。`fetch.py` 把這些私訊抓下來、打開連結截圖、
用本機 `claude -p` 下標題／摘要／分類／標籤，做成卡片牆。全部工具就是 `fetch.py` 一支（`uv run fetch.py --help`）。
用法和資料位置見 `README.md`。

## 第一次幫使用者設定

1. 問使用者要抓哪些來源：Telegram、IG、Threads 的哪段對話。IG / Threads 要的是網頁版打開那段對話時的網址。
2. Telegram 要 `.env` 的 `TG_API_ID` / `TG_API_HASH`，由使用者自己到 https://my.telegram.org 申請、自己填。
3. `web` 第一次會跳出 Chrome，請使用者自己登入。登入、驗證碼、金鑰一律由使用者處理。
4. 把使用者的對話網址記在這個檔案底下，之後補抓直接用。

## 最常見的工作：幫使用者翻資料

使用者會說「幫我找我存過的 ○○」：

1. `PYTHONIOENCODING=utf-8 uv run fetch.py find "regex1" "regex2"`：每個 regex 都要中（AND），同一個裡用 `|` 表示或。
   先放寬（同義詞、中英文、型號都放進同一個 regex），再自己讀摘要判斷。IG Reels 的說明常常只有幾個字，關鍵字搜不到不代表沒有。
   有疑問就看截圖：`data/pages.jsonl` 裡該網址那一行的 `cover` / `shot`。
2. 依用途分組，寫一個 pin 檔（格式見 `pin()` 說明），`uv run fetch.py pin <檔案>`。key 對不到卡片會整個拒收。
3. 在對話裡也照同樣的分組回報（標題、存的日期、重點、連結），最後給一句可行的建議。

## 補抓新訊息

```
uv run fetch.py tg
uv run fetch.py web <name> <對話網址>
uv run fetch.py auto          # 放背景跑
```

- `auto` 流程：resolve（開連結截圖）→ enrich（整理）→ look（說明太短的 IG / Threads 看封面重寫）→ merge（新標籤對進清單）
  → retag（沒有清單內標籤的補 1～4 個）→ wall（重建卡片牆）。
- `auto` 很慢是刻意的：平均每小時約 50 頁、隨機停頓，避免被 IG 限流。被限流時自己會等 6、12、24 小時。不要調快。
- `web` 和 `resolve` 共用 `.profile/` 的 Chrome，同時只能有一個程序用它。
- 有狀況先看 `data/auto.log`。
- `web` 只看到約 20 則就停、又沒接上舊的訊息：先截圖看畫面，常是對話框擋住，不要猜。
- 檢查漏抓：把各來源每天的訊息數列出來，連續幾天 0 則就要查。

## 規則

- **資料只留本地。** `data/`、`.profile/`、`.env`、`.telegram.session*` 不進 repo，也不上傳到任何地方。
- 只讀不寫：不代使用者送出任何訊息。
- 像密碼、金鑰的內容不送模型、不顯示（`SECRET`、`wanted()`）。私訊原文可能有使用者貼給自己的金鑰，不要整段印出來。
- `serve` 只開放卡片牆、待查清單和圖片；用 Tailscale 給自己看時**不要開 funnel**，那會變成公開網站。
- 哪些做成卡片由模型判斷；「零碎」「已失效」不做成卡片，列進 `data/review.html` 給使用者自己查。

## 踩過的坑

- **Windows 主控台預設不是 UTF-8**，印中文要加 `PYTHONIOENCODING=utf-8`。
- **Git Bash 的 heredoc 會把反斜線吃掉一半。** 要改 Python 字串裡的 `\n`、`\\` 時用 Edit 工具。
- **`messages()` 會讀 `data/` 底下所有 `*.jsonl`**（除了 pages / notes / pins），新增 jsonl 要記得排除。
- **改 `fetch.py` 時如果 `auto` 正在跑：** 它用的是開始時載入的舊程式。改完要自己再跑一次 `wall`。
- **`check` 模擬 `auto` 時，每個會叫模型的函式都要換成假的。** 漏了就會真的呼叫模型。新增會叫模型的步驟時，記得一起加進替換清單。
- **Windows 上 `allow_reuse_address` 會讓兩個程式綁同一個 port。** serve 已經關掉這個設定。
- 改完程式先跑 `uv run fetch.py check`。

## 使用者的對話網址

（第一次設定後填在這裡）
