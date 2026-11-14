/**
 * main.ts — B（负责人：B）：应用入口。
 * 顺序：style.css（基线唯一视觉源）→ tokens.css（仅深色覆盖）→ i18n → router。
 * AL-A1/AL-B7：全项目只有一份设计系统，页面内不再各写一套 scoped 样式。
 */
import { createApp } from "vue";
import App from "./App.vue";
import { router } from "./router";
import { initLocale } from "./i18n";
import "./assets/style.css";
import "./assets/tokens.css";

initLocale();
createApp(App).use(router).mount("#app");
