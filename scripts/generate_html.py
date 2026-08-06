#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""根据 gold_history.json 生成漂漂猪金价看板 HTML。"""
import html
import json
import sys


STYLE = r"""
:root {
  color-scheme: light;
  --sky: #8ed8ff;
  --sky-deep: #62b8ed;
  --cream: #fff9df;
  --paper: #fffdf4;
  --ink: #17324d;
  --muted: #6c8092;
  --ocean: #166c9f;
  --ocean-deep: #0d466e;
  --grass: #56b95f;
  --grass-dark: #287743;
  --leaf: #ec6a3b;
  --coin: #ffc83d;
  --coin-deep: #db8a17;
  --pink: #ff8ca1;
  --line: #d7e2df;
  --shadow: 0 10px 0 rgba(26, 80, 89, .14), 0 18px 38px rgba(30, 90, 120, .16);
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; -webkit-font-smoothing: antialiased; }
body {
  margin: 0;
  min-height: 100vh;
  color: var(--ink);
  font-family: "Avenir Next Rounded", "SF Pro Rounded", "PingFang SC", "Noto Sans SC", sans-serif;
  background: var(--sky);
  line-height: 1.7;
}
button { font: inherit; }
.world { min-height: 100vh; position: relative; overflow: hidden; padding: 28px 18px 72px; }
.world::before {
  content: ""; position: absolute; inset: 0; pointer-events: none;
  background:
    radial-gradient(circle at 12% 8%, rgba(255,255,255,.84) 0 44px, transparent 46px),
    radial-gradient(circle at 18% 8%, rgba(255,255,255,.68) 0 63px, transparent 65px),
    radial-gradient(circle at 88% 16%, rgba(255,255,255,.64) 0 54px, transparent 56px),
    linear-gradient(180deg, #8ed8ff 0%, #c7efff 53%, #5fc17a 53.2%, #399c59 57%, #1b7183 57.2%, #0f5377 100%);
}
.world::after {
  content: ""; position: absolute; left: -5%; right: -5%; top: 49%; height: 120px;
  border-radius: 50% 50% 0 0; background: #6bc76b; border-top: 8px solid #337f44;
  transform: rotate(-1deg); pointer-events: none;
}
.leaf { position: absolute; z-index: 1; width: 18px; height: 10px; border-radius: 90% 10% 90% 10%; background: var(--leaf); opacity: .74; }
.leaf.a { top: 8%; left: 5%; transform: rotate(24deg); }
.leaf.b { top: 20%; right: 7%; transform: rotate(-18deg) scale(.72); }
.leaf.c { top: 47%; left: 2%; transform: rotate(58deg) scale(1.15); }
.shell { width: min(1180px, 100%); margin: 0 auto; position: relative; z-index: 2; }
.topbar { display: flex; align-items: center; justify-content: space-between; gap: 18px; margin-bottom: 20px; }
.brand { display: flex; align-items: center; gap: 12px; }
.brand-mark {
  width: 52px; height: 52px; display: grid; place-items: center; position: relative;
  color: #73330d; font-weight: 1000; font-size: 25px; letter-spacing: -.12em;
  background: var(--coin); border: 4px solid #fff4a7; border-radius: 50%;
  box-shadow: 0 5px 0 var(--coin-deep), 0 9px 18px rgba(64,90,70,.18);
}
.brand-mark::after { content: ""; position: absolute; inset: 7px; border: 2px dashed rgba(130,72,12,.36); border-radius: 50%; }
.brand-copy strong { display: block; font-size: 21px; letter-spacing: .02em; line-height: 1.15; text-shadow: 0 2px 0 rgba(255,255,255,.45); }
.brand-copy span { font-size: 12px; font-weight: 750; color: #315f70; letter-spacing: .08em; }
.status-bar { display: flex; align-items: center; gap: 9px; padding: 8px 12px; border: 2px solid rgba(255,255,255,.72); border-radius: 999px; background: rgba(255,255,255,.52); backdrop-filter: blur(8px); font-size: 12px; font-weight: 750; }
.status-dot { width: 9px; height: 9px; border-radius: 50%; background: #3cc45a; box-shadow: 0 0 0 4px rgba(60,196,90,.16); }
.hero {
  min-height: 278px; display: grid; grid-template-columns: 1.18fr .82fr; overflow: hidden;
  background: var(--paper); border: 3px solid rgba(255,255,255,.9); border-radius: 30px;
  box-shadow: var(--shadow); position: relative;
}
.hero-main { padding: 34px 38px 32px; position: relative; background: linear-gradient(135deg, #fffdf2 0%, #fff3c8 100%); }
.eyebrow { display: flex; align-items: center; gap: 8px; color: var(--grass-dark); font-size: 12px; font-weight: 850; letter-spacing: .12em; }
.eyebrow::before { content: ""; width: 24px; height: 4px; border-radius: 9px; background: var(--grass); }
.hero h1 { font-size: clamp(27px, 4vw, 48px); line-height: 1.12; margin: 12px 0 20px; letter-spacing: -.035em; }
.price-line { display: flex; align-items: end; gap: 10px; flex-wrap: wrap; }
.big-price { font-size: clamp(58px, 9vw, 96px); line-height: .88; color: var(--leaf); font-weight: 950; letter-spacing: -.055em; font-variant-numeric: tabular-nums; text-shadow: 0 5px 0 #ffd1a9; }
.unit { color: var(--muted); font-size: 15px; font-weight: 800; padding-bottom: 8px; }
.movement { display: inline-flex; align-items: center; min-height: 32px; padding: 4px 11px; border-radius: 11px; background: #e8f7e5; color: #287743; font-size: 12px; font-weight: 850; margin-bottom: 6px; }
.movement.hot { background: #fff0e7; color: #b54a27; }
.movement.steady { background: #e9f2f8; color: #3d6a83; }
.hero-side { padding: 30px; color: #eefaff; background: var(--ocean-deep); position: relative; overflow: hidden; }
.hero-side::before { content: ""; position: absolute; width: 260px; height: 260px; border: 32px solid rgba(255,255,255,.055); border-radius: 50%; right: -100px; bottom: -120px; }
.quest-label { color: #aee8ff; font-size: 11px; font-weight: 850; letter-spacing: .14em; }
.hero-side h2 { margin: 6px 0 18px; font-size: 24px; line-height: 1.25; }
.market-lines { display: grid; gap: 12px; position: relative; }
.market-line { display: flex; align-items: center; justify-content: space-between; gap: 18px; padding-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,.13); }
.market-line span { color: #b9dbea; font-size: 12px; }
.market-line strong { font-size: 15px; font-variant-numeric: tabular-nums; text-align: right; }
.coverage { display: inline-flex; margin-top: 17px; padding: 6px 10px; color: #153a27; background: #8ee49b; border-radius: 9px; font-size: 11px; font-weight: 900; }
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 18px 0; }
.stat {
  min-height: 126px; padding: 18px; position: relative; overflow: hidden;
  border: 3px solid rgba(255,255,255,.86); border-radius: 22px; background: rgba(255,253,244,.94);
  box-shadow: 0 7px 0 rgba(20,78,89,.12), 0 14px 28px rgba(21,89,109,.10);
  transition: transform .18s ease, box-shadow .18s ease;
}
.stat:hover { transform: translateY(-4px); box-shadow: 0 11px 0 rgba(20,78,89,.11), 0 18px 34px rgba(21,89,109,.14); }
.stat-label { color: var(--muted); font-size: 11px; font-weight: 850; letter-spacing: .08em; }
.stat-value { margin-top: 8px; font-size: clamp(23px, 3vw, 31px); line-height: 1.15; font-weight: 950; font-variant-numeric: tabular-nums; }
.stat-value.gold { color: #c47a0b; }
.stat-value.blue { color: var(--ocean); }
.stat-sub { margin-top: 8px; color: #8293a0; font-size: 11px; font-weight: 650; }
.panel-grid { display: grid; grid-template-columns: minmax(0, 1.5fr) minmax(290px, .5fr); gap: 18px; align-items: stretch; }
.panel { background: var(--paper); border: 3px solid rgba(255,255,255,.88); border-radius: 26px; box-shadow: var(--shadow); overflow: hidden; }
.panel-head { display: flex; align-items: center; justify-content: space-between; gap: 14px; padding: 22px 24px 12px; flex-wrap: wrap; }
.panel-title { display: flex; align-items: center; gap: 10px; }
.panel-title i { width: 13px; height: 13px; transform: rotate(45deg); border-radius: 3px; background: var(--leaf); box-shadow: 3px 3px 0 #ffc0a0; }
.panel h2 { margin: 0; font-size: 17px; }
.panel-kicker { color: var(--muted); font-size: 11px; font-weight: 700; }
.switch { display: flex; gap: 4px; padding: 4px; background: #e8f0eb; border-radius: 13px; }
.switch button, .filter button { border: 0; cursor: pointer; font-size: 11px; font-weight: 850; color: #6b7e86; background: transparent; border-radius: 9px; padding: 7px 11px; transition: .16s ease; }
.switch button:hover, .filter button:hover { color: var(--ink); }
.switch button.active, .filter button.active { color: #fff; background: var(--ocean); box-shadow: 0 3px 0 var(--ocean-deep); }
.chart-wrap { height: 350px; padding: 8px 18px 22px; }
.market-map { padding-bottom: 18px; }
.range-stack { display: grid; gap: 17px; padding: 14px 24px 20px; }
.range-row { display: grid; grid-template-columns: 58px 1fr 42px; align-items: center; gap: 10px; }
.range-row label { color: var(--muted); font-size: 11px; font-weight: 800; }
.range-row strong { font-size: 12px; text-align: right; }
.bar { height: 13px; background: #e7eee8; border-radius: 999px; overflow: hidden; border: 2px solid #d7e2db; }
.bar span { display: block; height: 100%; border-radius: inherit; min-width: 6px; }
.bar.low span { background: var(--grass); }
.bar.main span { background: var(--coin); }
.bar.high span { background: var(--pink); }
.map-note { margin: 0 24px; padding: 14px; border-radius: 15px; color: #4c6675; background: #eef8f1; font-size: 11px; font-weight: 650; }
.list-panel { margin-top: 18px; }
.filter { display: flex; gap: 5px; padding: 4px; background: #eef2ee; border-radius: 13px; }
.table-scroll { overflow-x: auto; padding: 0 20px 18px; }
table { width: 100%; border-collapse: separate; border-spacing: 0 7px; min-width: 620px; }
th { padding: 0 14px 5px; color: #83939e; text-align: left; font-size: 10px; letter-spacing: .1em; }
td { padding: 11px 14px; background: #f3f7f2; font-size: 13px; font-weight: 700; font-variant-numeric: tabular-nums; }
td:first-child { border-radius: 13px 0 0 13px; color: #8b9aa4; }
td:last-child { border-radius: 0 13px 13px 0; }
tr[data-band="low"] td { background: #e9f7e5; }
.price { color: var(--leaf); font-size: 15px; font-weight: 950; }
.tag { display: inline-flex; padding: 3px 8px; border-radius: 999px; font-size: 10px; font-weight: 900; }
.tag.low { background: #caedc5; color: #287743; }
.tag.main { background: #ffefb4; color: #9d6508; }
.tag.high { background: #ffe0e6; color: #a9465a; }
.disclaimer { display: flex; align-items: flex-start; gap: 12px; margin-top: 18px; padding: 17px 19px; color: #436375; background: rgba(247,252,244,.9); border: 2px solid rgba(255,255,255,.72); border-radius: 18px; font-size: 11px; font-weight: 650; }
.disclaimer-mark { flex: 0 0 auto; width: 24px; height: 24px; display: grid; place-items: center; border-radius: 50%; color: white; background: var(--ocean); font-size: 13px; font-weight: 950; }
.footer { display: flex; justify-content: space-between; gap: 16px; margin-top: 14px; color: rgba(255,255,255,.75); font-size: 10px; font-weight: 700; }
@keyframes arrive { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
@media (prefers-reduced-motion: no-preference) {
  .hero, .stats, .panel-grid, .list-panel { animation: arrive .55s both; }
  .stats { animation-delay: .08s; } .panel-grid { animation-delay: .16s; } .list-panel { animation-delay: .24s; }
  .leaf { animation: leafFloat 5s ease-in-out infinite alternate; }
  @keyframes leafFloat { to { transform: translate(10px, 14px) rotate(70deg); } }
}
@media (max-width: 880px) {
  .hero { grid-template-columns: 1fr; }
  .stats { grid-template-columns: repeat(2, 1fr); }
  .panel-grid { grid-template-columns: 1fr; }
}
@media (max-width: 560px) {
  .world { padding: 18px 11px 54px; }
  .topbar { align-items: flex-start; }
  .brand-mark { width: 44px; height: 44px; }
  .brand-copy strong { font-size: 17px; }
  .status-bar { max-width: 145px; line-height: 1.35; border-radius: 14px; }
  .hero-main, .hero-side { padding: 25px 22px; }
  .hero { border-radius: 23px; }
  .stats { gap: 10px; }
  .stat { min-height: 116px; padding: 15px; border-radius: 18px; }
  .panel { border-radius: 21px; }
  .panel-head { padding: 18px 16px 10px; }
  .chart-wrap { height: 305px; padding-inline: 8px; }
  .range-stack { padding-inline: 16px; }
  .footer { flex-direction: column; }
}
"""


SCRIPT = r"""
(function () {
  const SERIES = __SERIES__;
  const RANGES = {"24h": 24 * 3600e3, "7d": 7 * 24 * 3600e3, "30d": 30 * 24 * 3600e3};
  let priceChart = null;

  function sliceByRange(range) {
    const cutoff = Date.now() - RANGES[range];
    const filtered = SERIES.filter((r) => {
      const ts = new Date(r.time.replace(" ", "T")).getTime();
      return Number.isFinite(ts) && ts >= cutoff;
    });
    return filtered.length ? filtered : SERIES;
  }

  if (typeof Chart === "undefined") {
    document.querySelector(".chart-wrap").innerHTML = '<div class="map-note">图表组件暂未加载，挂牌明细仍可正常查看。</div>';
  } else {
    priceChart = new Chart(document.getElementById("trend"), {
      type: "line",
      data: {labels: [], datasets: [
        {label: "最低挂牌", data: [], borderColor: "#ec6a3b", backgroundColor: "rgba(236,106,59,.13)", borderWidth: 3, pointRadius: 4, pointBackgroundColor: "#fff9df", pointBorderColor: "#ec6a3b", pointBorderWidth: 3, tension: .28, fill: true},
        {label: "加权均价", data: [], borderColor: "#166c9f", borderWidth: 2.5, pointRadius: 3, pointBackgroundColor: "#166c9f", tension: .28, fill: false}
      ]},
      options: {
        responsive: true, maintainAspectRatio: false,
        interaction: {mode: "index", intersect: false},
        scales: {
          y: {ticks: {color: "#6c8092", callback: (v) => Number(v).toFixed(2)}, grid: {color: "#dfe8e2"}, border: {display: false}},
          x: {ticks: {color: "#6c8092", maxTicksLimit: 8}, grid: {display: false}, border: {display: false}}
        },
        plugins: {
          legend: {position: "bottom", labels: {color: "#456173", usePointStyle: true, padding: 18, font: {weight: 700}}},
          tooltip: {backgroundColor: "#17324d", padding: 12, cornerRadius: 10, callbacks: {label: (ctx) => ctx.dataset.label + "：" + ctx.parsed.y.toFixed(2) + " 元/万金"}}
        }
      }
    });
  }

  function renderRange(range) {
    if (!priceChart) return;
    const rows = sliceByRange(range);
    priceChart.data.labels = rows.map((r) => r.time.slice(5, 16));
    priceChart.data.datasets[0].data = rows.map((r) => r.lowest);
    priceChart.data.datasets[1].data = rows.map((r) => r.weighted_avg);
    priceChart.update();
  }

  document.getElementById("rangeSwitch").addEventListener("click", (event) => {
    const button = event.target.closest("button[data-range]");
    if (!button) return;
    document.querySelectorAll("#rangeSwitch button").forEach((node) => node.classList.toggle("active", node === button));
    renderRange(button.dataset.range);
  });

  document.getElementById("tableFilter").addEventListener("click", (event) => {
    const button = event.target.closest("button[data-filter]");
    if (!button) return;
    document.querySelectorAll("#tableFilter button").forEach((node) => node.classList.toggle("active", node === button));
    document.querySelectorAll("#listingRows tr").forEach((row) => {
      row.hidden = button.dataset.filter !== "all" && row.dataset.band !== button.dataset.filter;
    });
  });

  renderRange("24h");
})();
"""


def fmt(value, digits=2):
    return "--" if value is None else f"{value:.{digits}f}"


def render(data_path, out_path):
    with open(data_path, encoding="utf-8") as handle:
        history = json.load(handle).get("history", [])
    current = history[-1] if history else {}
    previous = history[-2] if len(history) > 1 else None
    items = sorted(current.get("items", []), key=lambda item: item["price_per_wan"])

    low = current.get("lowest")
    low_delta = (low - previous["lowest"]) if previous and low is not None else None
    if low_delta is None or abs(low_delta) < 0.005:
        movement_class, movement_text = "steady", "与上次持平"
    elif low_delta > 0:
        movement_class, movement_text = "hot", f"较上次 +{low_delta:.2f}"
    else:
        movement_class, movement_text = "", f"较上次 {low_delta:.2f}"

    main_low = current.get("main_low", 0)
    main_high = current.get("main_high", 0)
    bands = {"low": 0, "main": 0, "high": 0}
    table_rows = []
    for index, item in enumerate(items, 1):
        price = item["price_per_wan"]
        if price < main_low:
            band, band_label = "low", "低价区"
        elif price <= main_high:
            band, band_label = "main", "主流区"
        else:
            band, band_label = "high", "高价区"
        bands[band] += 1
        quantity = str(item["qty_min"]) if item["qty_min"] == item["qty_max"] else f'{item["qty_min"]}–{item["qty_max"]}'
        listing_value = price * item["qty_max"]
        table_rows.append(
            f'<tr data-band="{band}"><td>#{index:02d}</td><td class="price">{price:.4f}</td>'
            f'<td>{quantity} 万</td><td>¥{listing_value:,.2f}</td><td><span class="tag {band}">{band_label}</span></td></tr>'
        )

    total_items = max(len(items), 1)
    bars = "".join(
        f'<div class="range-row"><label>{label}</label><div class="bar {key}"><span style="width:{bands[key] / total_items * 100:.1f}%"></span></div><strong>{bands[key]} 单</strong></div>'
        for key, label in (("low", "低价区"), ("main", "主流区"), ("high", "高价区"))
    )

    series = [{
        "time": row["time"], "lowest": row["lowest"], "weighted_avg": row["weighted_avg"],
        "main_low": row["main_low"], "main_high": row["main_high"],
        "n": row["n_listings"], "total_qty": row.get("total_qty", 0),
    } for row in history]
    n_listings = current.get("n_listings", 0)
    source_pages = current.get("source_pages")
    reported_total = current.get("source_reported_total")
    coverage_complete = current.get("coverage_complete")
    if coverage_complete:
        coverage_text = f"全量抓取完成 · {source_pages or 1} 页 / {reported_total or n_listings} 单"
    elif source_pages:
        coverage_text = f"已抓取 {source_pages} 页 · 请复核覆盖率"
    else:
        coverage_text = "历史快照 · 当时未记录分页覆盖率"

    page = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#8ed8ff">
<title>漂漂猪港口交易所 · 金价看板</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.0/dist/chart.umd.js" integrity="sha384-iU8HYtnGQ8Cy4zl7gbNMOhsDTTKX02BTXptVP/vqAWIaTfM7isw76iyZCsjL2eVi" crossorigin="anonymous"></script>
<style>__STYLE__</style>
</head>
<body lang="zh">
<main class="world" data-screen-label="漂漂猪港口交易所">
  <span class="leaf a"></span><span class="leaf b"></span><span class="leaf c"></span>
  <div class="shell">
    <header class="topbar">
      <div class="brand"><div class="brand-mark">PP</div><div class="brand-copy"><strong>漂漂猪港口交易所</strong><span>怀旧服 · 国服 · 游戏币行情</span></div></div>
      <div class="status-bar"><span class="status-dot"></span>云端每小时第 23 分自动巡价</div>
    </header>

    <section class="hero">
      <div class="hero-main">
        <div class="eyebrow">今日港口最低挂牌</div>
        <h1>现在一万金，要花多少钱？</h1>
        <div class="price-line"><span class="big-price">__LOW__</span><span class="unit">元 / 万金</span><span class="movement __MOVEMENT_CLASS__">__MOVEMENT_TEXT__</span></div>
      </div>
      <aside class="hero-side">
        <div class="quest-label">MARKET QUEST / 市场任务板</div>
        <h2>漂漂猪行情快照</h2>
        <div class="market-lines">
          <div class="market-line"><span>主流成交带</span><strong>__MAIN_RANGE__ 元</strong></div>
          <div class="market-line"><span>抓取时间</span><strong>__CURRENT_TIME__</strong></div>
          <div class="market-line"><span>数据来源</span><strong>DD373 挂牌</strong></div>
        </div>
        <div class="coverage">__COVERAGE__</div>
      </aside>
    </section>

    <section class="stats">
      <article class="stat"><div class="stat-label">挂牌加权均价</div><div class="stat-value blue">__WEIGHTED__</div><div class="stat-sub">元 / 万金 · 按最大可买量加权</div></article>
      <article class="stat"><div class="stat-label">全量在售单数</div><div class="stat-value">__LISTINGS__ 单</div><div class="stat-sub">自动遍历全部分页</div></article>
      <article class="stat"><div class="stat-label">港口总货量</div><div class="stat-value gold">__TOTAL_QTY__ 万</div><div class="stat-sub">当前挂牌最大可买量合计</div></article>
      <article class="stat"><div class="stat-label">一键扫货预算</div><div class="stat-value gold">¥__TOTAL_AMOUNT__</div><div class="stat-sub">按挂牌价买光全部在售</div></article>
    </section>

    <section class="panel-grid">
      <article class="panel">
        <div class="panel-head"><div><div class="panel-title"><i></i><h2>金价航线</h2></div><div class="panel-kicker">最低挂牌与加权均价的时间走势</div></div><div class="switch" id="rangeSwitch"><button class="active" data-range="24h">24 小时</button><button data-range="7d">7 天</button><button data-range="30d">30 天</button></div></div>
        <div class="chart-wrap"><canvas id="trend"></canvas></div>
      </article>
      <aside class="panel market-map">
        <div class="panel-head"><div><div class="panel-title"><i></i><h2>摊位分布</h2></div><div class="panel-kicker">按主流价格带切分当前挂牌</div></div></div>
        <div class="range-stack">__BARS__</div>
        <p class="map-note">主流区间取挂牌价中段 50%。低价单更便宜，但库存和卖家条件仍需进入平台逐单确认。</p>
      </aside>
    </section>

    <section class="panel list-panel">
      <div class="panel-head"><div><div class="panel-title"><i></i><h2>港口摊位清单</h2></div><div class="panel-kicker">当前 __LISTINGS__ 单 · 已按单价从低到高排序</div></div><div class="filter" id="tableFilter"><button class="active" data-filter="all">全部</button><button data-filter="low">低价</button><button data-filter="main">主流</button><button data-filter="high">高价</button></div></div>
      <div class="table-scroll"><table><thead><tr><th>序号</th><th>单价（元/万）</th><th>可买量</th><th>扫货金额</th><th>价格带</th></tr></thead><tbody id="listingRows">__ROWS__</tbody></table></div>
    </section>

    <div class="disclaimer"><span class="disclaimer-mark">i</span><span>数据抓自 DD373「冒险岛怀旧服 → 国服 → 漂漂猪 → 游戏币」卖家挂牌，不含平台手续费，也不代表真实成交价。开服初期波动较大，请把本页当作市场雷达，不要当作交易承诺。</span></div>
    <footer class="footer"><span>静态看板 · 云端定时刷新，本机异常兜底</span><span>最近快照：__CURRENT_TIME__</span></footer>
  </div>
</main>
<script>__SCRIPT__</script>
</body>
</html>'''

    replacements = {
        "__STYLE__": STYLE,
        "__SCRIPT__": SCRIPT.replace("__SERIES__", json.dumps(series, ensure_ascii=False)),
        "__LOW__": fmt(low, 4),
        "__MOVEMENT_CLASS__": movement_class,
        "__MOVEMENT_TEXT__": movement_text,
        "__MAIN_RANGE__": f'{fmt(current.get("main_low"), 2)} – {fmt(current.get("main_high"), 2)}',
        "__CURRENT_TIME__": html.escape(current.get("time", "--")),
        "__COVERAGE__": html.escape(coverage_text),
        "__WEIGHTED__": fmt(current.get("weighted_avg"), 2),
        "__LISTINGS__": str(n_listings),
        "__TOTAL_QTY__": f'{current.get("total_qty", 0):,.0f}',
        "__TOTAL_AMOUNT__": f'{current.get("total_amount", 0):,.0f}',
        "__BARS__": bars,
        "__ROWS__": "".join(table_rows),
    }
    for token, value in replacements.items():
        page = page.replace(token, value)

    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write(page)
    print(f"[ok] {out_path} ({len(page) // 1024} KB, 历史点 {len(series)})")


if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2])
