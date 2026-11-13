# BizSpark 接口变更记录

> 契约改动必须开 contract/ 前缀 PR 并 @全员（见需求文档 §12.1）

| 日期 | 版本 | 变更内容 | 提起人 | 状态 |
|------|------|----------|--------|------|
| 2026-11-13 | v1.0 | **F 落地 §2.4 全部状态类 cmd**（get_state/save_answers/save_idea/list_saved/clear_saved/compare_ideas/get_settings/set_settings/check_library/apply_delta/log_crash），无契约字段改名；`get_state` 额外返回 `paths`（§2.5 统一路径）与 `timeline`、`first_run`、`license_state`、`last_result` | F | 已实现 |
| 2026-11-13 | v1.0 | **交接 A**：启动 sidecar 时请设置环境变量 `BIZSPARK_LIBRARY_CURRENT=<paths.current_library_path()>`（即 `appDataDir/com.bizspark.desktop/library/current.json`），C 的 `FALLBACK_CHAIN` 会优先读工作库；不设置时 C 仍回退只读副本，不影响启动 | F | 待 A 接入 |
| 2026-11-13 | v1.0 | **交接 A**：`export_plan` 成功后 F 在 `main.py` 旁路记忆导出目录（F-10），A 的另存为默认目录可直接取 `get_settings.export_dir` | F | 待 A 接入 |
| 2026-11-13 | v1.0 | **交接 G**：`get_state.license_state` 目前只按 `license.dat` 存在性返回 `activated/none`；G 实现验签后请以真实凭证状态覆盖该字段（F 不解析凭证） | F | 待 G 接入 |
| 2026-11-13 | v1.0 | **交接 B**：`get_state` 返回字段已按 B 现有消费对齐（`last_answers`/`saved_count`/`library_version`/`license_state`/`first_run`/`saved`/`settings`/`export_dir`）；`list_saved.items[]` 含 `{id,title,saved_at,match_pct,min_capital}`；`compare_ideas` 返回 `{left,right}` 各含 `title + 三项` | F | 已对齐 |
| 2026-11-13 | v1.0 | **F 补 `main.handle` 守卫**：请求行解析为 JSON 数组/标量时回 `E_BAD_REQUEST`，不再让 sidecar 崩溃（正常 dict 请求行为不变） | F | 已实现 |
