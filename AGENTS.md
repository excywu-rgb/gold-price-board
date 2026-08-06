# 项目协作约束

本文件适用于仓库内所有后续 Codex/AI 对话和人工开发。开始改动前必须先阅读根目录 `PROJECT_LEDGER.md`。

## 不可破坏的生产不变量

1. `docs/data/gold_history.json` 是正式历史真源。除正式刷新流程外，不得用测试、实验或新业务抓取改写它。
2. 历史更新必须保留全部既有小时记录；同一小时只允许替换该小时快照；写入必须原子化；失败时保留旧数据。
3. `docs/index.html` 是 `scripts/generate_html.py` 的生成物。不得只手改 HTML；页面变化必须修改生成器并重新生成。
4. 不得删除或停用 Cloudflare 正式触发、`.github/workflows/refresh.yml`、本机 `com.goldpriceboard.refresh` 兜底，除非用户明确要求变更生产调度。
5. 不得启用 GitHub 原生 `schedule` 作为正式金价定时器。影子测试工作流必须保持停用。
6. 不得提交 `logs/`、密钥、Personal Access Token、Cloudflare secrets 或本机私有配置。
7. 抓取不完整、数据为空、结构错误或分页数量不一致时必须失败关闭，不得用部分结果覆盖正式数据。

## 并行开发规则

- 一个对话对应一个工作包和一个独立分支，建议命名：`feat/<domain>-<topic>`、`fix/<domain>-<topic>`、`research/<domain>-<topic>`。
- 开始前执行 `git fetch origin`，记录基线提交；集成前重新基于最新 `origin/main` 校准。
- 每个工作包声明“允许修改文件”和“禁止修改文件”。不要顺手改其他模块。
- 新的 DD373 非金价能力默认放入独立命名空间，不导入正式金价 JSON，不共用生产写入函数，不接入正式定时器。
- 多个分支都需要修改 `scripts/generate_html.py` 时，不得并行直接合并；先确定页面组件边界，由一个集成工作包统一处理生成器。
- 任何影响生产数据、刷新调度、页面生成器或 GitHub Pages 的改动，必须通过 `PROJECT_LEDGER.md` 定义的 Gate 后才能合入。

## 最低验收

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile scripts/*.py
python3 scripts/generate_html.py docs/data/gold_history.json docs/index.html
git diff --check
```

还必须确认：正式 JSON 未被非预期改写、既有测试通过、页面桌面和手机端无溢出、生产 workflow 未被意外启用或改时。

