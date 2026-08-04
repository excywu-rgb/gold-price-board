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
        rows += f"<tr><td>{it['price_per_wan']:.2f}</td><td>{q}</td></tr>"

    js_series = json.dumps(series, ensure_ascii=False)

    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>冒险岛怀旧服 · 漂漂猪 金价看板</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.0/dist/chart.umd.js" integrity="sha384-iU8HYtnGQ8Cy4zl7gbNMOhsDTTKX02BTXptVP/vqAWIaTfM7isw76iyZCsjL2eVi" crossorigin="anonymous"></script>
<style>
:root {{ color-scheme: light; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: -apple-system, "PingFang SC", "Microsoft YaHei", "Segoe UI", sans-serif;
  background: #f6f7fb; color: #1f2430; padding: 24px 16px;
}}
.wrap {{ max-width: 960px; margin: 0 auto; }}
.header {{
  display: flex; justify-content: space-between; align-items: flex-end;
  flex-wrap: wrap; gap: 8px; margin-bottom: 20px;
}}
h1 {{ font-size: 22px; font-weight: 700; }}
h1 small {{ font-size: 13px; font-weight: 400; color: #8a90a0; margin-left: 8px; }}
.meta {{ font-size: 12px; color: #8a90a0; }}
.cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 20px; }}
.card {{
  background: #fff; border-radius: 12px; padding: 14px 16px;
  box-shadow: 0 1px 3px rgba(20,30,60,.06); border: 1px solid #edeff4;
}}
.card .label {{ font-size: 12px; color: #8a90a0; margin-bottom: 6px; }}
.card .value {{ font-size: 22px; font-weight: 700; }}
.card .sub {{ font-size: 11px; color: #b0b6c4; margin-top: 4px; }}
.v-red {{ color: #e5484d; }}
.v-green {{ color: #30a46c; }}
.panel {{
  background: #fff; border-radius: 12px; padding: 18px;
  box-shadow: 0 1px 3px rgba(20,30,60,.06); border: 1px solid #edeff4; margin-bottom: 20px;
}}
.panel h2 {{ font-size: 15px; font-weight: 600; margin-bottom: 14px; }}
.panel-head {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }}
.panel-head h2 {{ margin-bottom: 0; }}
.range-switch {{ display: flex; gap: 4px; background: #eef0f6; border-radius: 8px; padding: 3px; }}
.range-switch button {{
  border: none; background: transparent; padding: 5px 14px; border-radius: 6px;
  font-size: 12px; font-weight: 600; color: #8a90a0; cursor: pointer;
}}
.range-switch button.active {{ background: #fff; color: #1f2430; box-shadow: 0 1px 2px rgba(20,30,60,.12); }}
.chart-box {{ position: relative; height: 320px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
th, td {{ padding: 8px 10px; text-align: left; border-bottom: 1px solid #f0f1f6; }}
th {{ color: #8a90a0; font-weight: 500; font-size: 12px; }}
td.price {{ font-weight: 600; }}
.foot {{ font-size: 12px; color: #9aa0b0; line-height: 1.7; margin-top: 4px; }}
.note {{ background: #f0f7ff; border: 1px solid #d6e8fa; border-radius: 8px; padding: 10px 12px; font-size: 12px; color: #2b5c8f; margin-top: 14px; }}
@media (max-width: 560px) {{
  h1 {{ font-size: 18px; }}
  .cards {{ grid-template-columns: repeat(2, 1fr); }}
}}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <h1>冒险岛怀旧服 · 漂漂猪 <small>金价看板</small></h1>
    <div class="meta">数据源：DD373 挂牌价 ｜ 更新：每小时</div>
  </div>

  <div class="cards">
    <div class="card">
      <div class="label">最低挂牌</div>
      <div class="value v-green">{low} <span style="font-size:13px">元/万金</span></div>
      <div class="sub">全服在售最低</div>
    </div>
    <div class="card">
      <div class="label">主流区间</div>
      <div class="value">{mlo} ~ {mhi} <span style="font-size:13px">元/万金</span></div>
      <div class="sub">中段50%挂牌价范围</div>
    </div>
    <div class="card">
      <div class="label">加权均价</div>
      <div class="value v-red">{wavg} <span style="font-size:13px">元/万金</span></div>
      <div class="sub">按可买量加权</div>
    </div>
    <div class="card">
      <div class="label">在售单数</div>
      <div class="value">{ncnt}</div>
      <div class="sub">最后抓取：{cur_ts}</div>
    </div>
    <div class="card">
      <div class="label">总可买量</div>
      <div class="value">{tq} <span style="font-size:13px">万金</span></div>
      <div class="sub">全部在售可买量合计</div>
    </div>
    <div class="card">
      <div class="label">点天灯</div>
      <div class="value v-red">{ta}</div>
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
      box.innerHTML = '<div style="padding:40px;text-align:center;color:#9aa0b0">图表库加载失败，请联网后刷新页面</div>';
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
      {{ label: "最低挂牌", data: [], borderColor: "#30a46c", backgroundColor: "#30a46c22", borderWidth: 2, pointRadius: 3, tension: 0.25, fill: false }},
      {{ label: "加权均价", data: [], borderColor: "#e5484d", backgroundColor: "#e5484d22", borderWidth: 2, pointRadius: 3, tension: 0.25, fill: false }},
      {{ label: "主流下限", data: [], borderColor: "#8b5cf6", backgroundColor: "#8b5cf622", borderWidth: 2, pointRadius: 3, tension: 0.25, fill: false }},
      {{ label: "主流上限", data: [], borderColor: "#f59f00", backgroundColor: "#f59f0022", borderWidth: 2, pointRadius: 3, tension: 0.25, fill: false }},
    ] }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      interaction: {{ mode: "index", intersect: false }},
      scales: {{
        y: {{ title: {{ display: true, text: "元 / 万金" }}, ticks: {{ callback: v => v.toFixed(2) }} }},
        x: {{ ticks: {{ maxTicksLimit: 12 }} }}
      }},
      plugins: {{
        legend: {{ position: "bottom" }},
        tooltip: {{ callbacks: {{ label: ctx => ctx.dataset.label + ": " + ctx.parsed.y.toFixed(2) + " 元/万金" }} }}
      }}
    }}
  }});
  const qtyChart = new Chart(document.getElementById("qtyTrend"), {{
    type: "bar",
    data: {{ labels: [], datasets: [
      {{ label: "总可买量", data: [], backgroundColor: "#3b82f6", borderRadius: 3, maxBarThickness: 32 }},
    ] }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      interaction: {{ mode: "index", intersect: false }},
      scales: {{
        y: {{ title: {{ display: true, text: "万金" }}, ticks: {{ callback: v => v.toFixed(0) }} }},
        x: {{ ticks: {{ maxTicksLimit: 12 }} }}
      }},
      plugins: {{
        legend: {{ position: "bottom" }},
        tooltip: {{ callbacks: {{ label: ctx => ctx.dataset.label + ": " + ctx.parsed.y.toFixed(0) + " 万金" }} }}
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
