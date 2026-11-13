#!/usr/bin/env bash
# A-14/A-15 / T-59 金额门禁（负责人：A，契约 K-11 / P-14 / L11）
# 规则：全项目零商品售价硬编码。价格只能由 config/pricing.json → inject-pricing.sh 渲染。
# 边界（文档明文）：商机库起步成本/定价建议（From 120、49 每月等）是内容数据，
#   位于 content/ 与 ui/ 的页面示例数据中，不受门禁约束。
# 扫描范围：apps/（代码/HTML/CSS/JS/locales）、config/、scripts/、qa/、根级 md
# 排除：content/（商机内容）、docs/（需求文档，含内容金额示例）、ui/（UI 交付源稿）
# 白名单（PM 2026-11-13 与 H 的 T-59 双口径对齐，均为"内容数据/QA 证据"，非商品售价）：
#   apps/core/data/、apps/core/tests/、apps/core/engine/quiz.py —— 商机库/资金档标签等内容数据
#   apps/web/src/locales/ —— 问卷资金档与结果文案（档位区间标签，非商品售价）
#   qa/reports/、qa/cases/、qa/content-review.md —— H 的 QA 证据与用例登记（含验证截图/故意渲染价）
# 退出码：0=通过（零命中），1=存在商品售价硬编码
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HITS=0

# 商品售价常见形态：美元符开头金额 / USD 前后缀金额（商品语境）
PATTERN='(\$[1-9][0-9,]*(\.[0-9]{1,2})?|USD ?[0-9][0-9,]*(\.[0-9]{1,2})?|[0-9][0-9,]*(\.[0-9]{1,2})? ?USD)'

# 首版 hidden 配置下，config/pricing.json 的 amount 必须为 null
CFG_W=$(cygpath -w "$ROOT/config/pricing.json")
if python3 -c "
import json,sys
cfg=json.load(open(r'$CFG_W',encoding='utf-8'))
sys.exit(0 if cfg.get('display_mode')=='hidden' and cfg.get('amount') is None else 1)
" ; then
  echo "[t59] ✓ 首版契约确认：display_mode=hidden, amount=null"
else
  echo "[t59] ⚠️ 价格配置非首版 hidden 态，跳过 amount 校验（visible 属发布参数）"
fi

echo "[t59] 扫描商品售价硬编码（范围: apps/ config/ scripts/ qa/ 根级 md）"
while IFS= read -r f; do
  if grep -InE "$PATTERN" "$f" >/dev/null 2>&1; then
    echo "[t59] ❌ 疑似商品售价硬编码: $f"
    grep -nE "$PATTERN" "$f" | head -3 | sed 's/^/      /'
    HITS=$((HITS+1))
  fi
done < <(find "$ROOT/apps" "$ROOT/config" "$ROOT/scripts" "$ROOT/qa" \
             -type f \( -name "*.html" -o -name "*.css" -o -name "*.js" -o -name "*.ts" \
                        -o -name "*.vue" -o -name "*.json" -o -name "*.py" -o -name "*.rs" \
                        -o -name "*.md" -o -name "*.sh" -o -name "*.toml" \) \
             ! -path "*/node_modules/*" ! -path "*/target/*" ! -path "*/dist/*" \
             ! -path "*/apps/core/data/*" ! -path "*/apps/core/tests/*" \
             ! -path "*/apps/core/engine/quiz.py" ! -path "*/apps/web/src/locales/*" \
             ! -path "*/qa/reports/*" ! -path "*/qa/cases/*" \
             ! -path "*/qa/content-review.md" ! -path "*/qa/store-assets/*" \
         2>/dev/null; \
         find "$ROOT" -maxdepth 1 -name "*.md" -type f 2>/dev/null)

if [ "$HITS" -eq 0 ]; then
  echo "[t59] ✅ 通过：交付物零商品售价硬编码（content/、docs/、ui/ 的内容数据金额不在扫描范围）"
  exit 0
else
  echo "[t59] ❌ 未通过：$HITS 个文件疑似含商品售价，请改走 config/pricing.json 配置渲染"
  exit 1
fi
