/* Price renderer — never hardcodes an amount. All amounts come from pricing.js. */
(function () {
  var p = window.BIZSPARK_PRICING || { display_mode:"hidden", amount:null, currency:"USD", model:"one-time" };
  var cn = (document.documentElement.lang || "").indexOf("zh") === 0;
  var SYM = { USD:"$", GBP:"£", EUR:"€", CAD:"C$", AUD:"A$", SGD:"S$", PHP:"₱" };
  function money() {
    if (p.amount == null) return "";
    var s = SYM[p.currency] || (p.currency + " ");
    return s + Number(p.amount).toFixed(2);
  }
  function modelWord() {
    var m = { "one-time": cn ? "一次买断" : "one-time",
              "monthly":  cn ? "按月"     : "per month",
              "yearly":   cn ? "按年"     : "per year",
              "seat":     cn ? "每席位"   : "per seat" };
    return m[p.model] || m["one-time"];
  }
  var show = p.display_mode === "visible" && p.amount != null;
  var T = {
    "hero-trust": {
      hidden: cn ? "<b>一次买断</b> &nbsp;· 永久归你" : "<b>One-time purchase</b> &nbsp;· Yours forever",
      visible: function (m) {
        var sub = p.model === "monthly" || p.model === "yearly";
        return cn ? "<b>" + m + "</b> &nbsp;" + modelWord() + (sub ? "，随时可取消" : "，永久归你")
                  : "<b>" + m + "</b> &nbsp;" + modelWord() + (sub ? ", cancel anytime" : ", yours forever");
      }
    },
    "hero-foot": {
      hidden: cn ? "Microsoft Store · Mac App Store · 一次买断"
                 : "Microsoft Store · Mac App Store · One-time purchase",
      visible: function (m) { return "Microsoft Store · Mac App Store · " + m + " " + modelWord(); }
    },
    "export-note": {
      hidden: cn ? "无订阅、不自动续费。买一次，想用多久用多久——就算断网也一样。"
                 : "No subscription. No auto-renew. Buy once, use it as long as you like — even with the internet off.",
      visible: function (m) {
        var sub = p.model === "monthly" || p.model === "yearly";
        return cn
          ? (sub ? m + " " + modelWord() + "，随时可取消；已导出的方案一直归你，断网也能用。"
                 : "无订阅、不自动续费。" + m + " 买一次，想用多久用多久——就算断网也一样。")
          : (sub ? m + " " + modelWord() + ", cancel anytime. Your exported plans stay yours — even offline."
                 : "No subscription. No auto-renew. Buy once at " + m + ", use it as long as you like — even with the internet off.");
      }
    },
    "activate-eyebrow": {
      hidden: cn ? "一次买断" : "One-time purchase",
      visible: function (m) { return m + " · " + modelWord(); }
    }
  };
  document.querySelectorAll("[data-price-slot]").forEach(function (el) {
    var t = T[el.getAttribute("data-price-slot")];
    if (!t) return;
    el.innerHTML = show ? t.visible(money()) : t.hidden;
  });
})();
