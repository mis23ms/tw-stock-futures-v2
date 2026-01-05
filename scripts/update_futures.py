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

def fetch_data(ticker, date_s):
    f_code = F_MAP.get(ticker)
    try:
        # 日期格式 YYYY/MM/DD
        q_date = f"{date_s[0:4]}/{date_s[4:6]}/{date_s[6:8]}"
        payload = {"queryDate": q_date, "commodityId": f_code}
        r = requests.post(TAIFEX_URL, data=payload, timeout=20)
        r.encoding = 'utf-8'
        
        if "查無資料" in r.text:
            return {"error": "期交所查無本日數據"}
            
        soup = BeautifulSoup(r.text, "lxml")
        table = soup.find("table", class_="table_f")
        rows = table.find_all("tr") if table else []
        
        # 尋找數據彙總列
        all_row = next((tr for tr in rows if "所有契約" in tr.get_text()), None)
        if not all_row: return {"error": "找不到『所有契約』數據列"}
            
        cols = [td.get_text(strip=True) for td in all_row.find_all("td")]
        if len(cols) < 10: return {"error": "表格結構異常"}

        # 索引 2:五多, 3:五空, 5:十多, 6:十空, 9:總未平倉量
        t5b, t5s = clean_int(cols[2]), clean_int(cols[3])
        t10b, t10s = clean_int(cols[5]), clean_int(cols[6])
        
        return {
            "top5": {"buy": t5b, "sell": t5s, "net": t5b - t5s},
            "top10": {"buy": t10b, "sell": t10s, "net": t10b - t10s},
            "oi": cols[9]
        }
    except: return {"error": "網路連線或解析失敗"}

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
