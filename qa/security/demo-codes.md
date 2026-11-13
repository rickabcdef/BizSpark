# 演示码（仅开发/验收用，禁止随发布版分发）

当前 `apps/core/license/pool.json` 是**演示池**（`pool_id=2026-11-dev`，`demo=true`，20 枚码）。
下面 5 枚可直接用于 H 的 T-41…T-44 验收；私钥在签发人机器上（`%APPDATA%/BizSpark-issuer/issuer.key`），
**发版前必须 `python tools/issue.py new-pool --count N --pool-id <正式号>` 重新签发**，
`qa/security/release_preflight.py`（不带 `--allow-demo`）会拦住演示池。

| # | 码 | 用途 |
|---|---|---|
| 1 | `BZSP-DPG5-Q2SM-BZR6` | T-41 首次激活（席位 1/3） |
| 2 | `BZSP-E9JZ-XC2Y-SELS` | T-43 幂等（同机重复激活不占位） |
| 3 | `BZSP-HVXA-C4PE-GUFX` | T-44 三席位与第 4 台（需模拟三台设备） |
| 4 | `BZSP-SH74-EBPP-N7GF` | 凭证损坏后重新激活 |
| 5 | `BZSP-MNKT-RXU5-PJGY` | 释放席位（人工流程文案） |

## 验收步骤（命令行复现，等价于界面操作）

```bash
# 用一个干净的 appData，避免污染真实状态
export BIZSPARK_APP_DATA=$(mktemp -d)

# T-41 首次激活：应 activated=true, seats_used=1，并生成 license.dat
printf '{"req_id":"a","cmd":"activate","payload":{"code":"BZSP-DPG5-Q2SM-BZR6"}}\n' | python apps/core/main.py

# 权限：Windows 看 icacls 只有当前用户；macOS/Linux 应为 600
icacls "$BIZSPARK_APP_DATA/license.dat"          # Windows
# stat -c '%a' "$BIZSPARK_APP_DATA/license.dat"  # Linux

# T-43 幂等：同一台机器再激活，seats_used 仍是 1，且返回 idempotent=true
printf '{"req_id":"b","cmd":"activate","payload":{"code":"BZSP-DPG5-Q2SM-BZR6"}}\n' | python apps/core/main.py

# T-44 第 4 台：用 payload.device_hash 模拟另外三台（64 hex），第 4 次应回 E_LICENSE_SEAT_FULL
#   文案里必须出现 Release a seat 的引导，且不含 "failed"/"授权失败"
#   见 apps/core/tests/test_license.py::test_three_seats_then_soft_seat_full

# T-45 拔网/断网可用：激活后关掉网络，get_state.license_state 仍为 activated（全程无 socket）
printf '{"req_id":"c","cmd":"get_state","payload":{}}\n' | python apps/core/main.py
```

自动化覆盖：`python -m unittest tests.test_license`（25 项，含 RFC 8032 向量与"零出网"桩）。
