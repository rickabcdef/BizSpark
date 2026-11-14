/**
 * money.ts — 货币展示口径（PM 2026-11-14，老板反馈：选了什么货币，价格一律跟什么货币）。
 * fx 来自 get_state.fx（engine 同口径：USD→本地乘数 + 友好取整）。
 * 仅用于问卷资金档 / 结果复述句；成本与金额数字的权威换算在引擎（engine.money）。
 */
export const CURRENCY_BY_COUNTRY: Record<string, string> = {
  US: "USD", CA: "CAD", GB: "GBP", UK: "GBP", AU: "AUD", SG: "SGD", PH: "PHP",
};

const SYMBOLS: Record<string, string> = {
  USD: "$", CAD: "C$", GBP: "£", AUD: "A$", SGD: "S$", PHP: "₱",
};

export function currencyOf(country?: string): string {
  return CURRENCY_BY_COUNTRY[String(country || "US").toUpperCase()] || "USD";
}

/** USD 金额 → 本地货币展示（与 engine.money.to_local 同一取整规则：half-up 分档） */
export function fmtAmount(usd: number, currency: string, fx?: Record<string, number>): string {
  const rate = fx?.[currency] ?? 1;
  const v = usd * rate;
  const hu = (x: number): number => Math.floor(x + 0.5);
  const r = v < 50 ? Math.max(1, hu(v))
    : v < 500 ? hu(v / 5) * 5
    : v < 5000 ? hu(v / 10) * 10
    : hu(v / 100) * 100;
  return (SYMBOLS[currency] || currency + " ") + r.toLocaleString("en-US");
}
