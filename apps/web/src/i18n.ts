/**
 * i18n.ts — B-10（负责人：B）
 * 极轻量 i18n：加载 locales/{en-US,zh-CN}.json，逐键镜像。
 * 规则（任务卡）：不增删键、不译白名单（BizSpark、Microsoft Store、
 * Mac App Store、PDF、CSV、AI、Google Maps、Yelp、Etsy、Shopify、
 * Nextdoor、激活码样例、文件名、版本号）。
 * 版本判定：跟随构建注入的 build-mode.txt（en 包=en-US，cn 包=zh-CN）。
 */
import enUS from "./locales/en-US.json";
import zhCN from "./locales/zh-CN.json";

type Dict = Record<string, string>;

const DICTS: Record<string, Dict> = {
  "en-US": enUS as Dict,
  "zh-CN": zhCN as Dict,
};

let current = "en-US";

/** 构建期注入（A-08 双构建写 window.BIZSPARK_BUILD.locale；缺省 en-US） */
export function initLocale(): void {
  const w = window as unknown as { BIZSPARK_BUILD?: { locale?: string } };
  const locale = w.BIZSPARK_BUILD?.locale;
  current = locale && DICTS[locale] ? locale : "en-US";
  document.documentElement.lang = current;
}

export function t(key: string, vars?: Record<string, string | number>): string {
  const s = DICTS[current][key] ?? DICTS["en-US"][key] ?? key;
  if (!vars) return s;
  return s.replace(/\{(\w+)\}/g, (_, k: string) => (vars[k] !== undefined ? String(vars[k]) : `{${k}}`));
}

export function locale(): string {
  return current;
}
