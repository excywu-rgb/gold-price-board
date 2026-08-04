#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据 gold_history.json 生成漂漂猪金价看板 HTML。
用法: python3 generate_html.py <data.json> <output.html>
"""
import json, sys, html

def render(data_path, out_path):
    data = json.load(open(data_path, encoding="utf-8"))
    hist = data.get("history", [])

    # 当前快照（最新一条）
    cur = hist[-1] if hist else None

    # 序列化给 JS
    series = [{
        "time": r["time"],
        "lowest": r["lowest"],
        "weighted_avg": r["weighted_avg"],
        "main_low": r["main_low"],
        "main_high": r["main_high"],
        "n": r["n_listings"],
        "total_qty": r.get("total_qty", 0),
        "total_amount": r.get("total_amount", 0),
    } for r in hist]

    items = (cur or {}).get("items", [])

    def fmt(v, nd=2):
        if v is None: return "--"
        return f"{v:.{nd}f}"

    cur_ts = cur["time"] if cur else "--"
    low = fmt(cur["lowest"]) if cur else "--"
    wavg = fmt(cur["weighted_avg"]) if cur else "--"
    mlo = fmt(cur["main_low"]) if cur else "--"
    mhi = fmt(cur["main_high"]) if cur else "--"
    ncnt = cur["n_listings"] if cur else 0
    total_qty = (cur or {}).get("total_qty") or 0
    total_amount = (cur or {}).get("total_amount") or 0
    tq = f"{total_qty:,.0f}" if total_qty else "--"
    ta = f"¥{total_amount:,.0f}" if total_amount else "--"

    # 表格行
    rows = ""
    for it in sorted(items, key=lambda x: x["price_per_wan"]):
        q = f"{it['qty_min']}~{it['qty_max']}" if it["qty_min"] != it["qty_max"] else str(it["qty_min"])
        rows += f"<tr><td class=\"price\"><span class=\"gold\">{it['price_per_wan']:.2f}</span></td><td>{q}</td></tr>"

    js_series = json.dumps(series, ensure_ascii=False)

    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>冒险岛怀旧服 · 漂漂猪 金价看板</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.0/dist/chart.umd.js" integrity="sha384-iU8HYtnGQ8Cy4zl7gbNMOhsDTTKX02BTXptVP/vqAWIaTfM7isw76iyZCsjL2eVi" crossorigin="anonymous"></script>
<style>
:root {{
  color-scheme: dark;
  --bg-0: #0b0f17;
  --bg-1: #111827;
  --bg-2: #1a2233;
  --card: #151d2e;
  --card-border: #24304a;
  --gold: #f5c542;
  --gold-soft: #e8b93a;
  --gold-dim: #8a6d2f;
  --text-1: #f2f4f8;
  --text-2: #9aa7bd;
  --text-3: #5c6b84;
  --up: #34d399;
  --down: #f87171;
  --radius: 14px;
  --shadow: 0 2px 12px rgba(0,0,0,.35), 0 0 0 1px rgba(245,197,66,.04) inset;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ -webkit-font-smoothing: antialiased; }}
body {{
  font-family: -apple-system, "PingFang SC", "Microsoft YaHei", "Segoe UI", sans-serif;
  background:
    radial-gradient(1200px 600px at 50% -10%, rgba(245,197,66,.06), transparent 60%),
    linear-gradient(180deg, var(--bg-1), var(--bg-0));
  background-attachment: fixed;
  color: var(--text-1); padding: 32px 16px;
  min-height: 100vh;
}}
.wrap {{ max-width: 960px; margin: 0 auto; }}
.header {{
  display: flex; justify-content: space-between; align-items: flex-end;
  flex-wrap: wrap; gap: 10px; margin-bottom: 24px;
  position: relative; padding-bottom: 16px;
}}
.header::after {{
  content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 1px;
  background: linear-gradient(90deg, var(--gold-dim), var(--gold) 30%, transparent 70%);
  opacity: .5;
}}
h1 {{ font-size: 23px; font-weight: 800; letter-spacing: .02em; }}
h1 .mascot {{
  display: inline-flex; align-items: center; justify-content: center;
  width: 26px; height: 26px; margin-right: 8px; border-radius: 8px;
  background: linear-gradient(135deg, var(--gold), #b8860b);
  color: #17120a; font-size: 15px; font-weight: 900;
  box-shadow: 0 0 0 1px rgba(245,197,66,.35), 0 0 16px rgba(245,197,66,.25);
  vertical-align: -5px;
}}
h1 small {{ font-size: 13px; font-weight: 400; color: var(--text-2); margin-left: 8px; }}
.meta {{ font-size: 12px; color: var(--text-3); letter-spacing: .02em; }}
.meta b {{ color: var(--gold-soft); font-weight: 600; }}
.cards {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 18px; }}
.card {{
  background: linear-gradient(160deg, var(--card), #121a2a);
  border-radius: var(--radius); padding: 16px 18px;
  border: 1px solid var(--card-border);
  box-shadow: var(--shadow);
  position: relative; overflow: hidden;
  transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;
}}
.card::before {{
  content: ""; position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, transparent, var(--gold), transparent);
  opacity: 0; transition: opacity .2s ease;
}}
.card:hover {{ transform: translateY(-2px); border-color: #33415f; box-shadow: 0 6px 20px rgba(0,0,0,.45); }}
.card:hover::before {{ opacity: .8; }}
.card .label {{ font-size: 12px; color: var(--text-3); margin-bottom: 8px; letter-spacing: .06em; font-weight: 600; }}
.card .value {{ font-size: 26px; font-weight: 800; font-variant-numeric: tabular-nums; letter-spacing: -.01em; }}
.card .value .unit {{ font-size: 12px; font-weight: 500; color: var(--text-3); margin-left: 4px; }}
.card .sub {{ font-size: 11px; color: var(--text-3); margin-top: 6px; }}
.v-gold {{ color: var(--gold); }}
.v-up {{ color: var(--up); }}
.v-down {{ color: var(--down); }}
.panel {{
  background: linear-gradient(160deg, var(--card), #121a2a);
  border-radius: var(--radius); padding: 20px;
  border: 1px solid var(--card-border);
  box-shadow: var(--shadow); margin-bottom: 18px;
}}
.panel h2 {{ font-size: 15px; font-weight: 700; margin-bottom: 14px; color: var(--text-1); letter-spacing: .02em; }}
.panel h2::before {{ content: "◆ "; color: var(--gold-dim); font-size: 12px; }}
.panel-head {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }}
.panel-head h2 {{ margin-bottom: 0; }}
.range-switch {{ display: flex; gap: 4px; background: #0d1422; border-radius: 10px; padding: 3px; border: 1px solid #223049; }}
.range-switch button {{
  border: none; background: transparent; padding: 6px 15px; border-radius: 7px;
  font-size: 12px; font-weight: 600; color: var(--text-3); cursor: pointer;
  transition: background .15s ease, color .15s ease, box-shadow .15s ease;
}}
.range-switch button:hover {{ color: var(--text-1); }}
.range-switch button.active {{ background: var(--gold); color: #17120a; box-shadow: 0 2px 8px rgba(245,197,66,.4); }}
.chart-box {{ position: relative; height: 320px; }}
.chart-box canvas {{ filter: drop-shadow(0 4px 12px rgba(0,0,0,.25)); }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
th, td {{ padding: 9px 12px; text-align: left; border-bottom: 1px solid #1f2a3f; }}
th {{ color: var(--text-3); font-weight: 600; font-size: 12px; letter-spacing: .05em; }}
td.price {{ font-weight: 700; font-variant-numeric: tabular-nums; }}
td.price .gold {{ color: var(--gold); }}
tbody tr {{ transition: background .15s ease; }}
tbody tr:hover {{ background: #1a2337; }}
.foot {{ font-size: 12px; color: var(--text-3); line-height: 1.7; margin-top: 4px; }}
.note {{
  background: linear-gradient(160deg, rgba(245,197,66,.07), rgba(245,197,66,.02));
  border: 1px solid rgba(245,197,66,.22); border-radius: 10px;
  padding: 12px 14px; font-size: 12px; color: var(--text-2); margin-top: 16px; line-height: 1.7;
}}
@media (max-width: 560px) {{
  h1 {{ font-size: 18px; }}
  .cards {{ grid-template-columns: repeat(2, 1fr); gap: 10px; }}
  body {{ padding: 20px 12px; }}
}}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <h1><span class="mascot">◆</span>漂漂猪 <small>冒险岛怀旧服 · 金价看板</small></h1>
    <div class="meta">数据源：DD373 挂牌价 ｜ <b>每小时自动更新</b></div>
  </div>

  <div class="cards">
    <div class="card">
      <div class="label">最低挂牌</div>
      <div class="value v-up">{low}<span class="unit">元/万金</span></div>
      <div class="sub">全服在售最低</div>
    </div>
    <div class="card">
      <div class="label">主流区间</div>
      <div class="value v-gold">{mlo} ~ {mhi}<span class="unit">元/万金</span></div>
      <div class="sub">中段50%挂牌价范围</div>
    </div>
    <div class="card">
      <div class="label">加权均价</div>
      <div class="value v-down">{wavg}<span class="unit">元/万金</span></div>
      <div class="sub">按可买量加权</div>
    </div>
  </div>

  <div class="cards">
    <div class="card">
      <div class="label">在售单数</div>
      <div class="value">{ncnt}<span class="unit">单</span></div>
      <div class="sub">最后抓取：{cur_ts}</div>
    </div>
    <div class="card">
      <div class="label">总可买量</div>
      <div class="value v-gold">{tq}<span class="unit">万金</span></div>
      <div class="sub">全部在售可买量合计</div>
    </div>
    <div class="card">
      <div class="label">点天灯</div>
      <div class="value v-gold">{ta}</div>
      <div class="sub">按挂牌价买光全部在售</div>
    </div>
  </div>

  <div class="panel">
    <div class="panel-head">
      <h2>金价走势</h2>
      <div class="range-switch" id="rangeSwitch">
        <button data-range="24h" class="active">24h</button>
        <button data-range="7d">7d</button>
        <button data-range="30d">30d</button>
      </div>
    </div>
    <div class="chart-box"><canvas id="trend"></canvas></div>
  </div>

  <div class="panel">
    <div class="panel-head">
      <h2>可买量走势</h2>
      <div class="range-switch" id="rangeSwitchQty">
        <button data-range="24h" class="active">24h</button>
        <button data-range="7d">7d</button>
        <button data-range="30d">30d</button>
      </div>
    </div>
    <div class="chart-box"><canvas id="qtyTrend"></canvas></div>
  </div>

  <div class="panel">
    <h2>当前在售明细（{ncnt} 单）</h2>
    <table>
      <thead><tr><th>单价（元/万金）</th><th>可买量（万）</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>

  <div class="note">
    说明：数据抓自 DD373「冒险岛怀旧服 → 国服 → 漂漂猪」区的卖家挂牌价，单位元/万金（不含平台手续费）。开服初期金价波动大，仅供参考。页面由自动任务每小时刷新，刷新时间见卡片「最后抓取」。
  </div>
  <div class="foot">分享说明：本页面为静态文件，可直接转发给朋友打开；数据为抓取时刻快照。</div>
</div>

<script>
const SERIES = {js_series};
(function () {{
  if (typeof Chart === "undefined") {{
    document.querySelectorAll(".chart-box").forEach(box => {{
      box.innerHTML = '<div style="padding:40px;text-align:center;color:#5c6b84">图表库加载失败，请联网后刷新页面</div>';
    }});
    return;
  }}
  const RANGES = {{ "24h": 24 * 3600e3, "7d": 7 * 24 * 3600e3, "30d": 30 * 24 * 3600e3 }};
  function sliceByRange(range) {{
    const cutoff = Date.now() - RANGES[range];
    return SERIES.filter(r => {{
      const ts = new Date(r.time.replace(" ", "T")).getTime();
      return !isNaN(ts) && ts >= cutoff;
    }});
  }}

  const priceChart = new Chart(document.getElementById("trend"), {{
    type: "line",
    data: {{ labels: [], datasets: [
      {{ label: "最低挂牌", data: [], borderColor: "#34d399", backgroundColor: "#34d39922", borderWidth: 2, pointRadius: 3, pointBackgroundColor: "#34d399", tension: 0.25, fill: false }},
      {{ label: "加权均价", data: [], borderColor: "#f5c542", backgroundColor: "#f5c54222", borderWidth: 2.5, pointRadius: 3, pointBackgroundColor: "#f5c542", tension: 0.25, fill: false }},
      {{ label: "主流下限", data: [], borderColor: "#60a5fa", backgroundColor: "#60a5fa22", borderWidth: 1.5, pointRadius: 2, tension: 0.25, fill: false }},
      {{ label: "主流上限", data: [], borderColor: "#fb923c", backgroundColor: "#fb923c22", borderWidth: 1.5, pointRadius: 2, tension: 0.25, fill: false }},
    ] }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      interaction: {{ mode: "index", intersect: false }},
      scales: {{
        y: {{ title: {{ display: true, text: "元 / 万金", color: "#9aa7bd" }}, ticks: {{ color: "#5c6b84", callback: v => v.toFixed(2) }}, grid: {{ color: "#1f2a3f" }} }},
        x: {{ ticks: {{ color: "#5c6b84", maxTicksLimit: 12 }}, grid: {{ color: "#1f2a3f" }} }}
      }},
      plugins: {{
        legend: {{ position: "bottom", labels: {{ color: "#9aa7bd", usePointStyle: true, pointStyle: "line", padding: 16 }} }},
        tooltip: {{ backgroundColor: "#0d1422", titleColor: "#f2f4f8", bodyColor: "#9aa7bd", borderColor: "#24304a", borderWidth: 1, callbacks: {{ label: ctx => ctx.dataset.label + ": " + ctx.parsed.y.toFixed(2) + " 元/万金" }} }}
      }}
    }}
  }});
  const qtyChart = new Chart(document.getElementById("qtyTrend"), {{
    type: "bar",
    data: {{ labels: [], datasets: [
      {{ label: "总可买量", data: [], backgroundColor: "rgba(245,197,66,.75)", hoverBackgroundColor: "#f5c542", borderRadius: 4, maxBarThickness: 32 }},
    ] }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      interaction: {{ mode: "index", intersect: false }},
      scales: {{
        y: {{ title: {{ display: true, text: "万金", color: "#9aa7bd" }}, ticks: {{ color: "#5c6b84", callback: v => v.toFixed(0) }}, grid: {{ color: "#1f2a3f" }} }},
        x: {{ ticks: {{ color: "#5c6b84", maxTicksLimit: 12 }}, grid: {{ color: "#1f2a3f" }} }}
      }},
      plugins: {{
        legend: {{ position: "bottom", labels: {{ color: "#9aa7bd", usePointStyle: true, padding: 16 }} }},
        tooltip: {{ backgroundColor: "#0d1422", titleColor: "#f2f4f8", bodyColor: "#9aa7bd", borderColor: "#24304a", borderWidth: 1, callbacks: {{ label: ctx => ctx.dataset.label + ": " + ctx.parsed.y.toFixed(0) + " 万金" }} }}
      }}
    }}
  }});

  function render(range) {{
    const rows = sliceByRange(range);
    const labels = rows.map(r => r.time.slice(5));
    const keys = ["lowest", "weighted_avg", "main_low", "main_high"];
    priceChart.data.labels = labels;
    keys.forEach((k, i) => {{ priceChart.data.datasets[i].data = rows.map(r => r[k]); }});
    qtyChart.data.labels = labels;
    qtyChart.data.datasets[0].data = rows.map(r => r.total_qty || 0);
    priceChart.update();
    qtyChart.update();
  }}
  function bindSwitch(swId) {{
    document.getElementById(swId).addEventListener("click", e => {{
      const btn = e.target.closest("button");
      if (!btn) return;
      document.querySelectorAll("#" + swId + " button").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      render(btn.dataset.range);
    }});
  }}
  bindSwitch("rangeSwitch");
  bindSwitch("rangeSwitchQty");
  render("24h");
}})();
</script>
</body>
</html>
"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"[ok] {out_path} ({len(page)//1024} KB, 历史点 {len(series)})")

if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2])
