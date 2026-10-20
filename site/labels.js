// Structure of the demo page: which rule packs belong to which country and which options are
// shown up front. The one-click acts (appeal, objection...) come from the rule packs themselves.
// All visible text lives in site/i18n/<language>.js.

export const LANGUAGES = [
  { code: "tr", name: "Türkçe" },
  { code: "en", name: "English" },
  { code: "de", name: "Deutsch" },
  { code: "fr", name: "Français" },
  { code: "es", name: "Español" },
  { code: "it", name: "Italiano" },
  { code: "pt", name: "Português" },
  { code: "nl", name: "Nederlands" },
  { code: "ru", name: "Русский" },
  { code: "ar", name: "العربية", dir: "rtl" },
  { code: "zh", name: "中文" },
  { code: "ja", name: "日本語" },
];

export const COUNTRIES = [
  { id: "tr", packs: ["tr/hmk", "tr/iik", "tr/cmk", "tr/iyuk", "tr/vuk", "tr/aym"] },
  { id: "us", packs: ["us/frcp"] },
  { id: "gb", packs: ["gb-eaw/cpr"] },
  { id: "eu", packs: ["eu/cj"] },
  { id: "de", packs: ["de/zpo"] },
];

// Options shown up front; the rest are disputed points under a collapsible section.
export const BASIC_OPTIONS = new Set(["service", "filing", "judicial_recess", "act", "start", "end_defined_by_event"]);
