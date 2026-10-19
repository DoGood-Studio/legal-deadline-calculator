// Structure of the demo page: which rule packs belong to which country, the common
// periods offered as one-click presets, and which options are shown up front.
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

// [period, direction, source]; labels are in the language files, in the same order.
export const PRESETS = {
  "tr/hmk": [["P2W", "after", "HMK m.345"], ["P2W", "after", "HMK m.361"], ["P2W", "after", "HMK m.127"]],
  "tr/iik": [["P7D", "after", "İİK m.62"], ["P5D", "after", "İİK m.168"], ["P7D", "after", "İİK m.16"], ["P2W", "after", "İİK m.363"]],
  "tr/cmk": [["P2W", "after", "CMK m.273"], ["P2W", "after", "CMK m.291"], ["P2W", "after", "CMK m.268"]],
  "tr/iyuk": [["P60D", "after", "İYUK m.7"], ["P30D", "after", "İYUK m.7"], ["P30D", "after", "İYUK m.45"]],
  "tr/vuk": [["P15D", "after", "VUK m.18"], ["P30D", "after", "VUK m.18"]],
  "tr/aym": [["P30D", "after", "6216 s.K. m.47/5"]],
  "us/frcp": [["P21D", "after", "FRCP 12(a)(1)(A)(i)"], ["P28D", "after", "FRCP 59(b)"], ["P14D", "before", "FRCP 6(c)(1)"]],
  "gb-eaw/cpr": [["P14D", "after", "CPR 10.3"], ["P28D", "after", "CPR 15.4"], ["P3D", "before", "CPR 23.7"]],
  "eu/cj": [["P2M", "after", "TFEU Art. 263"], ["P2M", "after", "Statute Art. 56"]],
  "de/zpo": [["P1M", "after", "§ 517 ZPO"], ["P2M", "after", "§ 520 ZPO"], ["P2W", "after", "§ 339 ZPO"], ["P1M", "after", "§ 548 ZPO"]],
};

// Options shown up front; the rest are disputed points under a collapsible section.
export const BASIC_OPTIONS = new Set(["service", "filing", "judicial_recess", "act", "start", "end_defined_by_event"]);
