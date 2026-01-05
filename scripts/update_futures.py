import json, requests, time, os
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup

# 正確代碼映射：2330=CDF, 2317=DHF, 3231=DXF, 2382=DKF
F_MAP = {"2330": "CDF", "2317": "DHF", "3231": "DXF", "2382": "DKF"}
F_NAMES = {"2330": "台積電期貨", "2317": "鴻海期貨", "3231": "緯創期貨", "2382": "廣達期貨"}
# 採用股票期貨專屬查詢網址
TAIFEX_URL = "https://www.taifex.com.tw/cht/3/largeTraderStockQry"

def clean_int(s):
    try: return int(str(s).replace(",", "").strip())
    except: return 0

import re  # 確保檔案頂部有 import re

# ... (fetch_data 函式內部)
        rows = table.find_all("tr") if table else []
        
        # 🟢 [最小修改]：使用混合抓取與空白正規化
        all_row_cols = None
        for tr in rows:
            # 同時抓取標題格(th)與數據格(td)
            cells = tr.find_all(["th", "td"])
            # 1. 抓取文字 2. 去除所有換行與空白 3. 轉為乾淨列表
            cols = [re.sub(r"\s+", "", c.get_text(strip=True)) for c in cells]
            
            # 判斷這列是否包含「所有契約」
            if any("所有契約" in x for x in cols):
                all_row_cols = cols
                break
        
        if not all_row_cols:
            return {"error": "找不到『所有契約』數據列"}
            
        # 🟢 [索引對齊]：根據正規化後的 cols 抓取數據
        # 索引通常為：2:五多, 3:五空, 5:十多, 6:十空, 9:總未平倉
        t5b, t5s = clean_int(all_row_cols[2]), clean_int(all_row_cols[3])
        t10b, t10s = clean_int(all_row_cols[5]), clean_int(all_row_cols[6])
        oi = all_row_cols[9]
        
        return {
            "top5": {"buy": t5b, "sell": t5s, "net": t5b - t5s},
            "top10": {"buy": t10b, "sell": t10s, "net": t10b - t10s},
            "oi": oi,
            "contract_month": "所有契約" # 強制標準化輸出
        }

def main():
    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz)
    # 每日 15:30 盤後資料更新
    if now.hour < 16: now -= timedelta(days=1)
    date_s = now.strftime("%Y%m%d")

    results = []
    for t, n in F_NAMES.items():
        print(f"抓取 {n}...")
        res = fetch_data(t, date_s)
        results.append({"ticker": t, "name": n, "data": res})
        time.sleep(2)

    os.makedirs("docs", exist_ok=True)
    with open("docs/futures_data.json", "w", encoding="utf-8") as f:
        json.dump({"date": date_s, "items": results}, f, ensure_ascii=False, indent=2)

if __name__ == "__main__": main()
