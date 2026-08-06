# 漂漂猪港口交易所

冒险岛怀旧服国服「漂漂猪」服务器的 DD373 游戏币行情采集、历史存储与可视化看板。

- 线上看板：https://excywu-rgb.github.io/gold-price-board/
- 正式仓库：https://github.com/excywu-rgb/gold-price-board
- 项目真源目录：`/Users/wuchaoyin/gold-price-board`
- 完整项目说明、运行台账、数据契约与并行开发边界：[PROJECT_LEDGER.md](PROJECT_LEDGER.md)

## 开始开发前

1. 阅读 `PROJECT_LEDGER.md`，确认当前状态和文件保护等级。
2. 阅读 `AGENTS.md`，遵守正式数据、生成文件和自动刷新链路的保护规则。
3. 从最新 `origin/main` 建立独立分支；一个对话只负责一个工作包。
4. 新功能先使用独立数据文件、脚本和测试，不直接复用或改写金价历史。

## 当前生产刷新链路

`Cloudflare Cron（每小时 :23） → GitHub workflow_dispatch → 全量抓取 DD373 → 原子更新历史 → 生成页面 → 推送 main → GitHub Pages`

本机 launchd 在每小时 `:47` 运行 `--fallback`，仅当远端最新快照达到 75 分钟陈旧时接管。

