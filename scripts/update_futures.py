import re # 確保頂部有這行

def fetch_data(ticker, date_s):
    f_code = F_MAP.get(ticker)
    try:
        q_date = f"{date_s[0:4]}/{date_s[4:6]}/{date_s[6:8]}"
        payload = {"queryDate": q_date, "commodityId": f_code}
        # 使用專屬股票期貨網址
        r = requests.post(TAIFEX_URL, data=payload, timeout=20)
        r.encoding = 'utf-8'
        
        if "查無資料" in r.text:
            return {"error": "期交所今日尚無資料"}
            
        soup = BeautifulSoup(r.text, "lxml")
        table = soup.find("table", class_="table_f")
        rows = table.find_all("tr") if table else []
        
        all_row_cols = None
        for tr in rows:
            cells = tr.find_all(["th", "td"])
            # [修正]：抓取文字並去除所有空白與換行 [cite: 16, 58]
            cols = [re.sub(r"\s+", "", c.get_text(strip=True)) for c in cells]
            
            if any("所有契約" in x for x in cols):
                all_row_cols = cols
                break
        
        if not all_row_cols:
            return {"error": "找不到『所有契約』數據列"}

        # [修正索引]：跳過百分比欄位，對齊張數
        # 0:名稱, 1:所有契約, 2:五買, 4:十買, 6:五賣, 8:十賣, 10:未平倉 [cite: 17-19]
        t5b = clean_int(all_row_cols[2])
        t10b = clean_int(all_row_cols[4])
        t5s = clean_int(all_row_cols[6])
        t10s = clean_int(all_row_cols[8])
        oi = all_row_cols[10]
        
        return {
            "top5": {"buy": t5b, "sell": t5s, "net": t5b - t5s},
            "top10": {"buy": t10b, "sell": t10s, "net": t10b - t10s},
            "oi": oi,
            "contract_month": "所有契約" # 強制標準化
        }
    except Exception as e:
        return {"error": "網路連線或解析失敗"}
