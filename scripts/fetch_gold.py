#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
冒险岛怀旧服·漂漂猪区 金价抓取脚本
抓取 DD373 上"冒险岛怀旧服 → 国服 → 漂漂猪"区的游戏币挂牌价。
用法: python3 fetch_gold.py [--out /path/to/data.json]
"""
import re, json, sys, gzip, os, tempfile
import urllib.request
from urllib.parse import urljoin
from datetime import datetime, timezone, timedelta

URL = "https://www.dd373.com/s-063g3j-c-et9e1b-7ewcb6-gsgchv.html"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "https://www.dd373.com/s-063g3j-c-et9e1b-7ewcb6.html",
}

def fetch_url(url):
    """返回 (html, http_date)；http_date 为服务器时间（UTC+8 naive）。"""
    req = urllib.request.Request(url, headers=HEADERS)
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


def fetch_raw():
    """兼容旧调用：只读取列表第一页。"""
    return fetch_url(URL)


def discover_page_urls(html):
    """从分页器读取全部数字页链接；第一页始终使用规范 URL。"""
    urls = [URL]
    box = re.search(r'<div id="pagination-box">(.*?)</div>\s*</div>', html, re.S)
    scope = box.group(1) if box else html
    for href, label in re.findall(
        r'<a\s+href="([^"]+)"[^>]*class="[^"]*ui-pagination-page-item[^"]*"[^>]*>\s*(\d+)\s*</a>',
        scope,
        re.S,
    ):
        if int(label) > 1:
            url = urljoin(URL, href)
            if url not in urls:
                urls.append(url)
    return urls


def reported_listing_count(html):
    m = re.search(r'为您找到\s*<span[^>]*>\s*(\d+)\s*</span>\s*条记录', html)
    return int(m.group(1)) if m else None

def parse_items(html):
    """解析商品列表。返回 [{price_per_wan, qty_min, qty_max}]"""
    blocks = re.split(r'<div class="goods-list-item\b[^>]*>', html)
    items = []
    for b in blocks[1:]:
        m = re.search(r'singleprice="([0-9.]+)"', b)
        if not m:
            continue
        sp = float(m.group(1))
        num = re.search(r'value="\d+"\s+min="(\d+)"\s+max="(\d+)"\s+singleprice', b)
        nmin = int(num.group(1)) if num else 0
        nmax = int(num.group(2)) if num else 0
        shop = re.search(r'[?&]shopNumber=([^&"]+)', b)
        item = {"price_per_wan": round(sp, 4), "qty_min": nmin, "qty_max": nmax}
        if shop:
            item["shop_number"] = shop.group(1)
        items.append(item)
    return items


def fetch_all_items():
    """遍历 DD373 全部分页，并核对页面宣称的挂牌总数。"""
    first_html, ts = fetch_url(URL)
    page_urls = discover_page_urls(first_html)
    pages = [first_html]
    for url in page_urls[1:]:
        page_html, _ = fetch_url(url)
        pages.append(page_html)

    items = []
    seen = set()
    for page_html in pages:
        for item in parse_items(page_html):
            key = item.get("shop_number") or (
                item["price_per_wan"], item["qty_min"], item["qty_max"]
            )
            if key in seen:
                continue
            seen.add(key)
            items.append(item)

    reported = reported_listing_count(first_html)
    if reported is not None and len(items) < reported:
        raise RuntimeError(
            f"分页抓取不完整：页面报告 {reported} 单，实际只解析到 {len(items)} 单"
        )
    if not items:
        raise RuntimeError("未解析到任何挂牌，拒绝覆盖历史数据")
    return items, ts, len(pages), reported

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
    """严格读取历史；只有文件确实不存在时才允许创建空历史。"""
    if not os.path.exists(path):
        return {"history": []}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or not isinstance(data.get("history"), list):
        raise ValueError("历史数据结构无效，拒绝覆盖正式文件")
    for index, record in enumerate(data["history"]):
        if not isinstance(record, dict) or not isinstance(record.get("time"), str):
            raise ValueError(f"历史记录 #{index} 缺少有效 time，拒绝覆盖正式文件")
    return data


def save_history_atomic(path, old_history, new_record):
    """保留全部既有小时记录，以原子替换方式写入本小时快照。"""
    hour = new_record["time"][:13]
    retained = [record for record in old_history if not record["time"].startswith(hour)]
    new_history = retained + [new_record]
    new_history.sort(key=lambda record: record["time"])

    expected_count = len(retained) + 1
    if len(new_history) != expected_count:
        raise RuntimeError("历史条数校验失败，拒绝写入")
    for record in retained:
        if record not in new_history:
            raise RuntimeError("既有历史记录发生丢失，拒绝写入")
    times = [record["time"] for record in new_history]
    if len(times) != len(set(times)):
        raise RuntimeError("历史时间戳重复，拒绝写入")

    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix="gold-history-", suffix=".json", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"history": new_history}, f, ensure_ascii=False, indent=1)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.chmod(temp_path, 0o644)
        os.replace(temp_path, path)
    except Exception:
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass
        raise
    return len(new_history)

def main():
    out = None
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
    items, ts, source_pages, source_reported_total = fetch_all_items()
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
        "source_pages": source_pages,
        "source_reported_total": source_reported_total,
        "coverage_complete": source_reported_total is None or st["n_listings"] >= source_reported_total,
        "items": items,
    }
    print(json.dumps(record, ensure_ascii=False, indent=1))
    if out:
        data = load(out)
        count = save_history_atomic(out, data["history"], record)
        print(f"[saved] {out} (history={count})", file=sys.stderr)

if __name__ == "__main__":
    main()
