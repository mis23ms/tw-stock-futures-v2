import json, requests, time, os, re
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup

# 2330=CDF, 2317=DHF(來源：TAIFEX SSF 清單可看到 DHF=2317)
F_MAP = {"2330": "CDF", "2317": "DHF", "3231": "DXF", "2382": "DKF"}
F_NAMES = {"2330": "台積電期貨", "2317": "鴻海期貨", "3231": "緯創期貨", "2382": "廣達期貨"}

# ✅ 改用 TAIFEX「期貨大額交易人未沖銷部位結構表」查詢頁
TAIFEX_URL = "https://www.taifex.com.tw/cht/3/largeTraderFutQry"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/x-www-form-urlencoded",
}

def clean_int(s):
    try:
        return int(str(s).replace(",", "").strip())
    except:
        return 0

def fetch_data(ticker, date_s):
    f_code = F_MAP.get(ticker)
    if not f_code:
        return {"error": "不支援的期貨代碼"}

    try:
        q_date = f"{date_s[0:4]}/{date_s[4:6]}/{date_s[6:8]}"
        payload = {"queryDate": q_date, "commodityId": f_code}
        r = requests.post(TAIFEX_URL, data=payload, headers=HEADERS, timeout=25)
        r.encoding = "utf-8"

        if "查無資料" in r.text:
            return {"error": "期交所查無本日數據（通常盤後才完整）"}

        soup = BeautifulSoup(r.text, "lxml")
        table = soup.find("table", class_="table_f")
        if not table:
            return {"error": "找不到 TAIFEX 表格(table_f)"}

        # ✅ 同時抓 th + td，並去除所有空白，避免「所有契約」匹配不到
        all_row_cols = None
        for tr in table.find_all("tr"):
            cells = tr.find_all(["th", "td"])
            cols = [re.sub(r"\s+", "", c.get_text(strip=True)) for c in cells]
            if any("所有契約" in x for x in cols):
                all_row_cols = cols
                break

        if not all_row_cols:
            return {"error": "找不到『所有契約』數據列（TAIFEX 版面可能變動或此商品不在此表）"}

        # ✅ 欄位常包含「部位數 + 百分比」交錯，這裡用「跳過%欄」的索引
        # 2:五多(部位數), 4:十多(部位數), 6:五空(部位數), 8:十空(部位數), 10:未平倉量
        if len(all_row_cols) < 11:
            return {"error": f"表格欄位不足(len={len(all_row_cols)})，疑似 TAIFEX 版面變了"}

        t5b = clean_int(all_row_cols[2])
        t10b = clean_int(all_row_cols[4])
        t5s = clean_int(all_row_cols[6])
        t10s = clean_int(all_row_cols[8])
        oi = all_row_cols[10].replace(",", "")

        return {
            "top5": {"buy": t5b, "sell": t5s, "net": t5b - t5s},
            "top10": {"buy": t10b, "sell": t10s, "net": t10b - t10s},
            "oi": oi,
            "contract_month": "所有契約"
        }

    except Exception:
        return {"error": "網路連線或解析失敗"}

def main():
    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz)
    if now.hour < 16:
        now -= timedelta(days=1)
    date_s = now.strftime("%Y%m%d")

    results = []
    for t, n in F_NAMES.items():
        print(f"抓取 {n}...")
        res = fetch_data(t, date_s)
        results.append({"ticker": t, "name": n, "data": res})
        time.sleep(1)

    os.makedirs("docs", exist_ok=True)
    with open("docs/futures_data.json", "w", encoding="utf-8") as f:
        json.dump({"date": date_s, "items": results}, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()

