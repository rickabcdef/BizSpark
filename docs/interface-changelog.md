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
| 2026-11-13 | v1.0 | **G 接管 F10 三个 cmd**：`activate {code, device_hash?}` → `{activated, state, seats_used, seats_max, idempotent?}`；`license_status {}` → `{activated, state, seats_used(null 表示未知), seats_max}`；`release_seat {}` → `{released:false, manual:true, support_email, message, seats_used, seats_max}`。失败只回 `E_LICENSE_BAD_CODE` / `E_LICENSE_SEAT_FULL`（均 `recoverable:true`，文案不含 fail/授权失败） | G | 已实现 |
| 2026-11-13 | v1.0 | **G 覆盖 `get_state.license_state`**（兑现 F 的交接）：取值扩为 `activated` / `unseated`（凭证合法但本机不在席位，多为拷来的文件）/ `invalid`（损坏或被改）/ `none`；只改这一个字段，F 的其它逻辑与字段一字未动 | G | 已实现（A/B 若 switch 该字段请加上两个新值） |
| 2026-11-13 | v1.0 | **交接 B（G-05 页面缺口）**：`release_seat` 已按"无后台"返回说明文案与支持邮箱，但 `Activate.vue` 目前点完静默、用户看不到说明。建议加 1 个键（如 `activate.release_note`）在释放按钮下方展示 `message`，不新增账号/输入框 | G | 待 B 接入 |
| 2026-11-13 | v1.0 | **交接 A**：①`fingerprint.rs` 需按 `docs/fingerprint-spec.md` 补齐四个分量；**对齐前不要**注入 `BIZSPARK_DEVICE_HASH`（否则同机两套指纹、席位重复占用）。②`pack.sh` 排除 `tools/`，Store 构建排除 `apps/core/license/`。③`tauri.conf.json` 的 `csp` 建议改为非 null（见 `docs/security-review.md` §2.1） | G | 待 A 接入 |
| 2026-11-13 | v1.0 | **新增构建产物**：`apps/core/license/pool.json`（Ed25519 签名的码池，须随包分发）；签发工具 `tools/issue.py` **不打包**；演示池 `demo=true`，发版前必须重新签发（`qa/security/release_preflight.py` 会拦住） | G | 已实现 |
