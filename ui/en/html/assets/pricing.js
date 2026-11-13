/* BizSpark pricing — SINGLE SOURCE OF TRUTH.
   Change ONE file to change the price everywhere.
   First release: display_mode = "hidden", amount = null.
   NO monetary amount is stored anywhere in this project. */
window.BIZSPARK_PRICING = {
  display_mode: "hidden",      /* "hidden" | "visible"                       */
  amount:       null,          /* number; set ONLY when display_mode=visible */
  currency:     "USD",         /* ISO 4217                                   */
  model:        "one-time",    /* "one-time" | "monthly" | "yearly" | "seat"*/
  billing_note: null           /* optional: "per month" / "per year"        */
};
