# 商机内容抽检报告（H-09）

> 抽检方式：按 `id` 排序等距取 30 条（可复现，不依赖随机种子）；
> 判定清单：需求文档 §5.4。生成脚本：`qa/cases/test_content.py`。

## 结果

- 抽样：**30** 条（库共 312 条）
- 全过：**30** 条　不达标：**0** 条

## 逐条明细

| # | id | 资金档 | 结论 | 不达标项 |
|---|---|---|---|---|
| 1 | `bs-agt-ai-agent-setup-local-294` | 2k-10k | ✅ | — |
| 2 | `bs-agt-ai-agent-setup-local-304` | <500 | ✅ | — |
| 3 | `bs-b2b-google-maps-setup-176` | 10k+ | ✅ | — |
| 4 | `bs-b2b-inbox-tidy-208` | 10k+ | ✅ | — |
| 5 | `bs-b2b-inbox-tidy-218` | 2k-10k | ✅ | — |
| 6 | `bs-b2b-invoice-chasing-172` | <500 | ✅ | — |
| 7 | `bs-b2b-quote-templates-204` | <500 | ✅ | — |
| 8 | `bs-b2b-simple-bookkeeping-192` | 2k-10k | ✅ | — |
| 9 | `bs-cnt-local-guide-pdf-246` | 500-2k | ✅ | — |
| 10 | `bs-cnt-nbhd-newsletter-234` | <500 | ✅ | — |
| 11 | `bs-cnt-stock-photo-local-255` | 2k-10k | ✅ | — |
| 12 | `bs-cnt-template-packs-221` | 2k-10k | ✅ | — |
| 13 | `bs-hnd-market-stall-264` | <500 | ✅ | — |
| 14 | `bs-hnd-market-stall-274` | 500-2k | ✅ | — |
| 15 | `bs-hnd-repair-corner-284` | <500 | ✅ | — |
| 16 | `bs-onl-calendar-va-127` | <500 | ✅ | — |
| 17 | `bs-onl-calendar-va-137` | 500-2k | ✅ | — |
| 18 | `bs-onl-ebook-formatting-122` | <500 | ✅ | — |
| 19 | `bs-onl-online-tutoring-156` | 500-2k | ✅ | — |
| 20 | `bs-onl-product-photo-091` | 500-2k | ✅ | — |
| 21 | `bs-onl-resume-polish-101` | 500-2k | ✅ | — |
| 22 | `bs-onl-resume-polish-111` | 2k-10k | ✅ | — |
| 23 | `bs-onl-transcription-local-146` | <500 | ✅ | — |
| 24 | `bs-svc-appliance-tuneup-083` | 500-2k | ✅ | — |
| 25 | `bs-svc-errand-runner-061` | 500-2k | ✅ | — |
| 26 | `bs-svc-home-cleaning-016` | <500 | ✅ | — |
| 27 | `bs-svc-lawn-garden-037` | 500-2k | ✅ | — |
| 28 | `bs-svc-mobile-car-wash-047` | 2k-10k | ✅ | — |
| 29 | `bs-svc-pet-care-024` | 500-2k | ✅ | — |
| 30 | `bs-svc-review-reply-001` | 2k-10k | ✅ | — |

## 抽样覆盖

- 行业：6 个不同前缀分类
- 资金档：10k+, 2k-10k, 500-2k, <500
- 时间档：10-25, <10, full

