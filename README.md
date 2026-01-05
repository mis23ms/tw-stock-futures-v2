# tw-stock-futures-v2
v2 of TW key stock vs futures contact
```md
# 個股期貨大額交易人監控（GitHub Pages + Actions 自動更新）

這是一個獨立的 GitHub Pages 小站：每天盤後自動抓取 **TAIFEX「期貨大額交易人未沖銷部位結構表」**，輸出 JSON，前端顯示 4 檔個股期貨的「所有契約」彙總（前五/前十、多空、未平倉量）。

---

## 功能
- 固定監控 4 檔個股期貨：
  - 2330 台積電期貨
  - 2317 鴻海期貨
  - 3231 緯創期貨
  - 2382 廣達期貨
- 顯示欄位（所有契約彙總列）：
  - 前五大淨部位（買 - 賣）
  - 前十大淨部位（買 - 賣）
  - 前五大多/空（口數）
  - 前十大多/空（口數）
  - 全市場未平倉量（OI）
- 每天 16:00 後（盤後）由 GitHub Actions 自動更新資料

---

## 專案結構（必須長這樣）
```

.github/workflows/update.yml
docs/
index.html
futures_data.json   (由 Actions 產生/更新)
scripts/
update_futures.py
requirements.txt
README.md

````

---

## 重要：為什麼之前「綠燈但沒資料」？
> Actions 綠燈只代表「腳本成功執行 + 成功輸出 JSON」，不代表 JSON 內容一定是正確數據。

### 根因（已修）
- `largeTraderFutQry` 是互動查詢頁（下拉選單/流程偏動態），用 `commodityId=CDF/DHF...` 直接 POST 常會回「查無資料」→ JSON 只剩 error → 頁面顯示錯誤。
- 正確做法是改抓 **靜態表格頁**：  
  `https://www.taifex.com.tw/cht/3/largeTraderFutQryTbl`  
  一次抓整張表，再從 HTML 解析出 4 檔的「所有契約」列。

---

## GitHub Pages 設定（必做）
1. Repo → **Settings** → **Pages**
2. Source：Deploy from a branch
3. Branch：`main`
4. Folder：`/docs`
5. Save  
完成後會得到網址：  
`https://<username>.github.io/<repo>/`

---

## GitHub Actions（自動更新）
- workflow 檔：`.github/workflows/update.yml`
- 會執行：`python scripts/update_futures.py`
- 產出/更新：`docs/futures_data.json`
- 會 commit 回 repo（所以你會看到 futures_data.json 的 commit 記錄在更新）

---

## 輸出 JSON 格式（前端依賴）
`docs/futures_data.json` 格式如下：

```json
{
  "date": "YYYYMMDD",
  "items": [
    {
      "ticker": "2330",
      "name": "台積電期貨",
      "data": {
        "top5":  { "buy": 0, "sell": 0, "net": 0 },
        "top10": { "buy": 0, "sell": 0, "net": 0 },
        "oi": "0",
        "contract_month": "所有契約"
      }
    }
  ]
}
````

---

## 驗收方式（3 步）

1. Actions → 最新一次 workflow **綠燈**
2. Repo 內 `docs/futures_data.json` 的 `date` 有更新
3. 打開 Pages 網址，四張卡片顯示數字（不是錯誤訊息）

---

## 常見踩雷（避免重踩）

* **不要把 AI 回覆的 ``` 或說明文字一起貼進 index.html**
  否則瀏覽器會把程式碼當文字印出來，頁面看起來像「整段 JS 外露」。
* `futures_data.json` 必須和 `index.html` 在同一個 Pages 來源資料夾
  （本專案 Pages 用 `/docs`，所以 JSON 必須輸出到 `docs/futures_data.json`）。

---

## 免責

本專案僅做資料整理與視覺化，非投資建議。資料以 TAIFEX 公告為準，可能因網站調整而需更新解析規則。

```
::contentReference[oaicite:0]{index=0}
```
