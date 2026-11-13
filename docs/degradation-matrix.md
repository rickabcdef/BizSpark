# BizSpark 降级路径矩阵（F-08 / §4 F13，负责人：F，验收：H）

> 12 个场景逐条实现。表内「落点」列写明由哪一层兜住，方便 H 逐条造场景验收。
> 全局禁令：红色弹窗 / `Please check your connection` / 错误码外露 / loading >1s。

| # | 场景 | 用户看到什么 | 落点（文件/函数） | 自测方式 |
|---|---|---|---|---|
| 1 | 首次启动 / 无网 | 一切正常，用 baseline | `state/merge.ensure_working_library()`（首启复制只读副本→工作库）+ C 的 `load_library` 回退链 | 清空 appData 启动；拔网启动 |
| 2 | 更新失败 / 托管挂了 / 忘续费 | 界面无任何变化 | A 拉取层静默跳过；F 的 `apply_delta` 对任何异常返回可恢复错误、不写盘 | 断网/404/脏 JSON 各跑一次 |
| 3 | sidecar 未就绪 / 崩一次 | 自动重启 1 次；再失败仅浏览已存点子，不弹窗 | A 的 `bridge.rs` 重启策略；F 的 `state.json` 与存档独立于 sidecar 进程 | 手动 kill sidecar |
| 4 | 匹配结果不足 3 条 | 放宽时间档一次，1–2 条 + 温和一句 | C 的 `diagnose`（F 不插手） | 极端答案组合 |
| 5 | 整库损坏 | 内置只读副本 → 再 fallback_ideas.json | `state/merge.read_current()` → `ensure_working_library(force_rebuild=True)`；C 的回退链兜底 | 把 `library/current.json` 写成垃圾 |
| 6 | `state.json` 损坏 | 静默重建空存档，不弹窗、不动其他文件 | `state/store.load_state()`：坏文件改名 `state.json.corrupt-<ts>` 留档→重建 | 写入非 JSON 后调 get_state |
| 7 | 导出路径不可写 | 只提示换文件夹 | E 的 `render/pdf.export_plan` 返回 `E_PDF_WRITE`（recoverable）；F 不改其语义 | 只读目录导出 |
| 8 | 详情页脏字段 | 兜底句补齐，无 `undefined` | E 的 `render/detail.sanitize()` | 删 pitfalls 第 3 条 |
| 9 | 第 4 台设备激活 | 引导释放席位，不报「授权失败」 | G 的 `license/activate.py`（F 只读 `license.dat` 存在性） | 伪造 3 席位凭证 |
| 10 | 系统深浅色切换 | 跟随，不闪白 | B 的 CSS 变量 + `follow_system_appearance` 设置 | 系统切换主题 |
| 11 | 用户断网一个月 | 完全无感，回来后按序合并缺失 delta | `state/merge.apply_sequence()`（按 release 排序逐包合并）+ `apply_delta` 幂等去重 | 造 3 个月 delta 乱序喂入 |
| 12 | 用户取消另存为 | 静默回详情页 | E 返回 `E_EXPORT_CANCELLED`（recoverable）；F 不写任何状态 | 另存为点取消 |

## F 额外兜住的脏输入（不在表内但同属 F13 口径）

| 场景 | 行为 | 落点 |
|---|---|---|
| IPC 收到 JSON 数组/标量 | 回一行 `E_BAD_REQUEST`，sidecar 不崩 | `main.handle()` 的 `isinstance(req, dict)` 守卫（F 补） |
| `state.json` 是合法 JSON 但不是对象 | 同 #6，静默重建 | `store.load_state()` |
| 设置里出现未知键 / 非法值 | 静默忽略，保留旧值 | `state/settings.apply_patch()` |
| 存档条数无限增长 | 上限 500 条，丢最旧，不弹提示 | `store.SAVED_MAX` |
| delta 的 `target_baseline` 不匹配（老客户端） | 静默跳过，不强行吃新包 | `merge.apply_delta()` |
| 同一 release 重复应用 | 幂等跳过（版本号不前进） | `merge.apply_delta()` 的版本比较 |
| 合并后校验失败（V-01/V-02/V-11） | **整体回滚**，磁盘库字节级不变 | `merge.apply_delta()` → `_restore()` |
| 回滚文件堆积 | 只保留最近 3 份 | `merge._prune_rollbacks()` |
| 崩溃日志开启但含用户数据 | 只写 `ts/code/version` 三字段白名单 | `settings.log_crash()` |
