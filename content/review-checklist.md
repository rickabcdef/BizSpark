# 商机内容审核清单（负责人：D 自检 + H 抽检 30 条，见 §5.4）

每条商机逐项过以下清单；任何一项不过即打回重写。

## 内容质量（§5.3/§5.4）

- [ ] `title` 一眼知道卖什么，不含 `AI-powered / revolutionary / 一站式` 等虚词
- [ ] `one_liner` 回答了「谁付钱」
- [ ] `steps[0]` 是**明天早上能做的具体动作**（有地点/对象/数量）
- [ ] `steps` 恰好 7 条，每条 ≤60 字符、动词开头
- [ ] `cost_breakdown` 逐项列钱，合计 ≈ `min_capital`（±15%）
- [ ] `pricing_hint` 含具体数字
- [ ] `first_customers` ≥3 且是具体渠道名，**不是** "social media / online promotion / 广告"
- [ ] `pitfalls` 恰好 3 条且是可执行告诫
- [ ] `compliance_note` 只有一句，不是法律意见
- [ ] 无空话、无 emoji、无中文（英文版内容库）

## 数据契约（§3.2 / §3.8）

- [ ] `id` 唯一且匹配 `^[a-z]{2}-[a-z]{2,4}-[a-z0-9-]{1,20}-\d{3}$`（V-01）
- [ ] 必填字段齐全、类型正确（V-02）
- [ ] 全部枚举命中（V-05）
- [ ] 6 国覆盖或明确回退主条目（V-06）；SG/PH 渠道写成 Facebook / WhatsApp / Google Maps 本地形态

## 分布与巡检（§5.1 / D-10）

- [ ] `saturated` 占比 ≤20%（V-07 巡检）
- [ ] `ai-llm/ai-agent/bi-agent` 合计 ≤12%（V-08 巡检）
- [ ] `wave` 与 `maturity` 符合 §5.1 分布（V-12）

## 工具

- [ ] `python apps/core/library/validate.py` 全绿（0 error；V-12 合并期警告需说明）
- [ ] H 抽检 30 条记录在案（抽检结果由 H 回填）
