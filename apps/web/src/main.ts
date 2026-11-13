/**
 * main.ts — B（负责人：B）：应用入口。
 * 顺序：tokens.css（B-01 设计 token）→ i18n init（B-10）→ router（B-04）。
 */
import { createApp } from "vue";
import App from "./App.vue";
import { router } from "./router";
import { initLocale } from "./i18n";
import "./assets/tokens.css";

initLocale();
createApp(App).use(router).mount("#app");
