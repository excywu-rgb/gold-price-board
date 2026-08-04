#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
冒险岛怀旧服·漂漂猪区 金价抓取脚本
抓取 DD373 上"冒险岛怀旧服 → 国服 → 漂漂猪"区的游戏币挂牌价。
用法: python3 fetch_gold.py [--out /path/to/data.json]
"""
import re, json, sys, gzip, time
import urllib.request
from datetime import datetime, timezone, timedelta

URL = "https://www.dd373.com/s-063g3j-c-et9e1b-7ewcb6-gsgchv.html"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "https://www.dd373.com/s-063g3j-c-et9e1b-7ewcb6.html",
}

def fetch_raw():
    """返回 (html, http_date) —— http_date 为服务器返回的真实时间(naive, 已转UTC+8)"""
    req = urllib.request.Request(URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            data = gzip.decompress(data)
        # 服务器 Date 头是 GMT；VM 沙箱时钟可能不准，用服务器时间
        http_date = r.headers.get("Date")
        try:
            dt = datetime.strptime(http_date, "%a, %d %b %Y %H:%M:%S %Z")
            dt = dt.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=8)))
            server_cst = dt.replace(tzinfo=None)
        except Exception:
            server_cst = now_cst()
        return data.decode("utf-8", "ignore"), server_cst

def parse_items(html):
    """解析商品列表。返回 [{price_per_wan, qty_min, qty_max}]"""
    blocks = re.split(r'<p class="game-qufu-attr">', html)
    items = []
    for b in blocks[1:]:
        m = re.search(r'singleprice="([0-9.]+)"', b)
        if not m:
            continue
        sp = float(m.group(1))
        num = re.search(r'value="\d+"\s+min="(\d+)"\s+max="(\d+)"\s+singleprice', b)
        nmin = int(num.group(1)) if num else 0
        nmax = int(num.group(2)) if num else 0
        items.append({"price_per_wan": round(sp, 4), "qty_min": nmin, "qty_max": nmax})
    return items

def stats(items):
    """计算统计指标。返回 dict"""
    if not items:
        return None
    prices = sorted(i["price_per_wan"] for i in items)
    n = len(prices)
    low = prices[0]
    # 主流区间: 去掉最高25%和最低25%后的中段区间
    lo_q = prices[n // 4]
    hi_q = prices[(3 * n) // 4]
    mid = [p for p in prices if lo_q <= p <= hi_q]
    main_low = mid[0]
    main_high = mid[-1]
    main_cnt = len(mid)
    # 加权均价(按最大可买量加权, 反映实际成交倾向)
    total_qty = sum(i["qty_max"] for i in items)
    wavg = sum(i["price_per_wan"] * i["qty_max"] for i in items) / total_qty if total_qty else low
    # 点天灯: 把所有在售可买量按对应价格全部买下的总金额(元) = Σ(单价 × 可买量)
    total_amount = sum(i["price_per_wan"] * i["qty_max"] for i in items)
    return {
        "n_listings": n,
        "lowest": low,
        "main_range": [main_low, main_high],
        "main_count": main_cnt,
        "weighted_avg": round(wavg, 4),
        "total_qty": total_qty,
        "total_amount": round(total_amount, 2),
        "max_listing": prices[-1],
    }

def now_cst():
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz)

def load(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"history": []}

def main():
    out = None
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
    html, ts = fetch_raw()
    items = parse_items(html)
    st = stats(items)
    record = {
        "time": ts.strftime("%Y-%m-%d %H:%M:%S"),
        "lowest": st["lowest"],
        "main_low": st["main_range"][0],
        "main_high": st["main_range"][1],
        "main_count": st["main_count"],
        "weighted_avg": st["weighted_avg"],
        "total_qty": st["total_qty"],
        "total_amount": st["total_amount"],
        "n_listings": st["n_listings"],
        "items": items,
    }
    print(json.dumps(record, ensure_ascii=False, indent=1))
    if out:
        data = load(out)
        # 去重: 同一小时内重复抓取则覆盖
        hour = ts.strftime("%Y-%m-%d %H")
        data["history"] = [r for r in data.get("history", []) if not r["time"].startswith(hour)]
        data["history"].append(record)
        data["history"].sort(key=lambda r: r["time"])
        with open(out, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print(f"[saved] {out} (history={len(data['history'])})", file=sys.stderr)

if __name__ == "__main__":
    main()
