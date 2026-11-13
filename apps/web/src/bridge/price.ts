/**
 * price.ts — B-13（负责人：B）
 * [data-price-slot] 占位 + price-render.js 渲染器（Vue 适配层）。
 * 逻辑逐句移植 ui/en/html/assets/price-render.js；所有金额来自
 * 构建期注入的 window.BIZSPARK_PRICING（A 的 inject-pricing.sh），
 * 本文件零金额硬编码。文案走 locales 的 price.* 键（不含金额，
 * visible 模板用 {amount} 占位）。
 */
import { t, locale } from "../i18n";

interface Pricing {
  display_mode: "hidden" | "visible";
  amount: number | null;
  currency: string;
  model: "one-time" | "monthly" | "yearly" | "seat";
}

const SYM: Record<string, string> = { USD: "$", GBP: "£", EUR: "€", CAD: "C$", AUD: "A$", SGD: "S$", PHP: "₱" };

function pricing(): Pricing {
  const w = window as unknown as { BIZSPARK_PRICING?: Pricing };
  return (
    w.BIZSPARK_PRICING || { display_mode: "hidden", amount: null, currency: "USD", model: "one-time" }
  );
}

function money(p: Pricing): string {
  if (p.amount == null) return "";
  const s = SYM[p.currency] || p.currency + " ";
  return s + Number(p.amount).toFixed(2);
}

function modelWord(p: Pricing): string {
  const m: Record<string, string> = {
    "one-time": t("price.model_one_time"),
    monthly: t("price.model_monthly"),
    yearly: t("price.model_yearly"),
    seat: t("price.model_seat"),
  };
  return m[p.model] || m["one-time"];
}

/** 四个价格槽：与 price-render.js 的 T 表一一对应 */
function slotText(slot: string, p: Pricing): string {
  const show = p.display_mode === "visible" && p.amount != null;
  const m = money(p);
  const sub = p.model === "monthly" || p.model === "yearly";
  if (slot === "hero-trust") {
    if (!show) return t("price.hero_trust_hidden");
    return sub
      ? t("price.hero_trust_visible_sub", { amount: m, model: modelWord(p) })
      : t("price.hero_trust_visible", { amount: m, model: modelWord(p) });
  }
  if (slot === "hero-foot") {
    return show
      ? "Microsoft Store · Mac App Store · " + m + " " + modelWord(p)
      : t("price.hero_foot_hidden");
  }
  if (slot === "export-note") {
    if (!show) return t("price.export_note_hidden");
    return sub
      ? t("price.export_note_visible_sub", { amount: m, model: modelWord(p) })
      : t("price.export_note_visible_once", { amount: m });
  }
  if (slot === "activate-eyebrow") {
    return show ? m + " · " + modelWord(p) : t("price.activate_eyebrow_hidden");
  }
  return "";
}

/** 渲染当前文档内全部 [data-price-slot]（视图在 onMounted 后调用） */
export function renderPriceSlots(): void {
  const p = pricing();
  const isZh = locale().indexOf("zh") === 0;
  void isZh; // 文案已由 locales 承载双语；保留判断位与 price-render.js 对齐
  document.querySelectorAll("[data-price-slot]").forEach((el) => {
    const slot = el.getAttribute("data-price-slot");
    if (!slot) return;
    el.innerHTML = slotText(slot, p);
  });
}
