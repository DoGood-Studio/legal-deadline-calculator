// lexdays demo page. All calculations use the published ESM bundle (assets/lexdays.js).
import { calendar, compute, listCalendars, rulepack } from "./assets/lexdays.js";
import { buildIcs, googleCalendarUrl } from "./ics.js";
import { BASIC_OPTIONS, COUNTRIES, LANGUAGES, PRESETS } from "./labels.js";

// Interface text lives in i18n/<code>.js; English is always loaded as the fallback.
const dicts = { en: (await import("./i18n/en.js")).default };
async function loadDict(code) {
  dicts[code] ??= (await import(`./i18n/${code}.js`)).default;
}

// ------------------------------------------------------------------ helpers

const $ = (id) => document.getElementById(id);
const params = new URLSearchParams(location.search);
const SUPPORTED = new Set(LANGUAGES.map((l) => l.code));

// Each language has its own page (/tr/, /de/, ...; see scripts/build-site-pages.mjs) that fixes
// the language. On the root page ?lang= wins, then the browser's preferred languages, then English.
const PAGE_LANG = SUPPORTED.has(document.documentElement.dataset.pageLang) ? document.documentElement.dataset.pageLang : null;
function detectLang() {
  if (PAGE_LANG) return PAGE_LANG;
  if (SUPPORTED.has(params.get("lang"))) return params.get("lang");
  for (const tag of navigator.languages ?? [navigator.language]) {
    const base = String(tag ?? "").toLowerCase().split("-")[0];
    if (SUPPORTED.has(base)) return base;
  }
  return "en";
}

const state = { lang: detectLang(), pack: null, options: {} };

// Looks up a path such as ("packs", "tr/hmk", 0) in the current language, then in English.
function label(...path) {
  for (const dict of [dicts[state.lang], dicts.en]) {
    let value = dict;
    for (const key of path) value = value?.[key];
    if (value != null) return value;
  }
  return null;
}
function t(key, vars = {}) {
  return (label("ui", key) ?? key).replace(/\{(\w+)\}/g, (_, k) => String(vars[k] ?? ""));
}

// Text from the rule data ({en, tr, ...}). Notes and citations are not translated into every
// language; when one falls back to English the page says so.
const fellBack = new Set();
function txt(obj, area) {
  if (!obj) return "";
  if (obj[state.lang] != null) return obj[state.lang];
  if (area) fellBack.add(area);
  return obj.en ?? Object.values(obj)[0] ?? "";
}
const updateLangNote = () => ($("r-langnote").hidden = fellBack.size === 0);
const engineLang = () => state.lang;
// Label-value separator: full-width in Chinese and Japanese, spaced in French.
const colon = () => (["zh", "ja"].includes(state.lang) ? "：" : state.lang === "fr" ? " : " : ": ");
// Arabic keeps Latin digits so dates match the explanation text the library produces.
const locale = () => (state.lang === "ar" ? "ar-u-nu-latn" : state.lang);
const num = (n) => new Intl.NumberFormat(locale(), { useGrouping: false }).format(n);
const quantity = (n, unit) => new Intl.NumberFormat(locale(), { style: "unit", unit, unitDisplay: "long" }).format(n);
const utc = (iso) => {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d));
};
const fmt = (iso, opts) => new Intl.DateTimeFormat(locale(), { timeZone: "UTC", ...opts }).format(utc(iso));
const isoOf = (date) => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
const todayIso = () => isoOf(new Date());
const dayDiff = (a, b) => Math.round((utc(b) - utc(a)) / 86400000);
const addDaysIso = (iso, n) => new Date(utc(iso).getTime() + n * 86400000).toISOString().slice(0, 10);

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else if (v !== false && v != null) node.setAttribute(k, v === true ? "" : v);
  }
  for (const child of children) if (child != null) node.append(child);
  return node;
}

function radioGroup(container, items, isChecked, onPick) {
  container.replaceChildren(
    ...items.map((item) =>
      el(
        "button",
        { type: "button", role: "radio", "aria-checked": String(isChecked(item)), class: item.className ?? "", onclick: () => onPick(item) },
        ...item.content,
      ),
    ),
  );
}

// ------------------------------------------------------------ deadline form

const countryOf = (packId) => COUNTRIES.find((c) => c.packs.includes(packId));

function setPack(packId, applyPreset = true) {
  const pack = rulepack(packId);
  state.pack = packId;
  state.options = Object.fromEntries(Object.entries(pack.options).map(([k, spec]) => [k, spec.default]));
  state.calendar = pack.calendar.id;
  if (applyPreset) usePreset(PRESETS[packId]?.[0]);
}

function usePreset(preset) {
  state.preset = preset ?? null;
  if (!preset) return;
  // A preset is [period, direction, citation, options?]; options set what the act implies
  // (e.g. a filing is an act at the court office).
  const [period, direction, , options] = preset;
  const match = /^P(\d+)([DWMY])$/.exec(period);
  $("amount").value = match[1];
  $("unit").value = { D: "day", W: "week", M: "month", Y: "year" }[match[2]];
  setDirection(direction);
  if (options) Object.assign(state.options, options);
}

function setDirection(value) {
  for (const b of $("direction").querySelectorAll("button")) b.setAttribute("aria-checked", String(b.dataset.value === value));
}
const direction = () => $("direction").querySelector('[aria-checked="true"]').dataset.value;
const periodString = () => {
  const unit = $("unit").value;
  const n = Math.max(1, Math.round(Number($("amount").value) || 1));
  return unit === "business_day" ? `${n}bd` : `P${n}${unit[0].toUpperCase()}`;
};

function renderForm() {
  const country = countryOf(state.pack);
  radioGroup(
    $("countries"),
    COUNTRIES.map((c) => ({ ...c, content: [label("countries", c.id)] })),
    (c) => c.id === country.id,
    (c) => {
      if (c.id === country.id) return;
      setPack(c.packs[0]);
      renderForm();
      run();
    },
  );
  radioGroup(
    $("packs"),
    country.packs.map((id) => ({ id, className: "pack", content: [el("strong", {}, label("packs", id, 0)), el("span", {}, label("packs", id, 1))] })),
    (p) => p.id === state.pack,
    (p) => {
      setPack(p.id);
      renderForm();
      run();
    },
  );
  $("trigger-label").textContent = direction() === "before" ? t("trigger.before") : label("packs", state.pack, 2);
  renderPresets();
  renderCalendarField();
  renderOptions();
}

function renderPresets() {
  const presets = PRESETS[state.pack] ?? [];
  radioGroup(
    $("presets"),
    presets.map((p, i) => ({ p, className: "preset", content: [label("presets", state.pack, i), el("small", {}, `${periodLabel(p[0])} · ${p[2]}`)] })),
    ({ p }) => p === activePreset(presets),
    ({ p }) => {
      usePreset(p);
      renderForm();
      run();
    },
  );
}

// The preset the user picked, or else the first one matching the current period.
function activePreset(presets) {
  const matches = (p) => periodString() === p[0] && direction() === p[1];
  if (state.preset && presets.includes(state.preset) && matches(state.preset)) return state.preset;
  return presets.find(matches) ?? null;
}

function periodLabel(period) {
  const [, n, u] = /^P(\d+)([DWMY])$/.exec(period);
  return quantity(Number(n), { D: "day", W: "week", M: "month", Y: "year" }[u]);
}

function renderCalendarField() {
  const pack = rulepack(state.pack);
  const field = $("calendar-field");
  field.hidden = !pack.calendarFamily;
  if (!pack.calendarFamily) return;
  const family = pack.calendarFamily;
  const ids = listCalendars().filter((id) => id === family || id.startsWith(`${family}-`));
  $("calendar").replaceChildren(...ids.map((id) => el("option", { value: id }, txt(calendar(id).name))));
  $("calendar").value = state.calendar;
}

function renderOptions() {
  const pack = rulepack(state.pack);
  const basic = [];
  const advanced = [];
  fellBack.delete("form");
  for (const [name, spec] of Object.entries(pack.options)) {
    const box = el("div", { class: "opt", role: "radiogroup", "aria-labelledby": `q-${name}` });
    box.append(el("div", { class: "opt__q", id: `q-${name}` }, label("options", name) ?? name));
    const choices = el("div", { class: "opt__choices" });
    for (const value of spec.values) {
      const text = label("values", name, String(value)) ?? String(value);
      const input = el("input", { type: "radio", name: `opt-${name}`, value: JSON.stringify(value), checked: state.options[name] === value });
      input.addEventListener("change", () => {
        state.options[name] = value;
        run();
      });
      choices.append(el("label", { class: "choice" }, input, el("span", {}, text)));
    }
    box.append(choices);
    const hint = txt(spec.description, "form");
    if (hint) box.append(el("p", { class: "opt__hint" }, hint));
    (BASIC_OPTIONS.has(name) ? basic : advanced).push(box);
  }
  $("basic-options").replaceChildren(...basic);
  $("advanced-options").replaceChildren(...advanced);
  $("advanced").hidden = advanced.length === 0;
  $("details-step").hidden = basic.length === 0 && advanced.length === 0 && !pack.calendarFamily;
  updateLangNote();
}

// ------------------------------------------------------------------ result

let lastResult = null;

function run() {
  const trigger = $("trigger").value;
  $("r-error").hidden = true;
  fellBack.delete("result");
  try {
    const pack = rulepack(state.pack);
    const result = compute(state.pack, trigger, periodString(), {
      direction: direction(),
      options: state.options,
      calendar: pack.calendarFamily ? state.calendar : undefined,
    });
    lastResult = result;
    renderVerdict(result.deadline, "leaf", "r-date");
    $("r-time").textContent = result.endsAt ? `${t("r.ends")}${colon()}${result.endsAt}${result.timezone ? ` (${result.timezone})` : ""}` : "";
    const diff = dayDiff(todayIso(), result.deadline);
    const cd = $("r-countdown");
    cd.textContent = diff > 0 ? t("cd.left", { d: quantity(diff, "day") }) : diff === 0 ? t("cd.today") : t("cd.past", { d: quantity(-diff, "day") });
    cd.classList.toggle("past", diff < 0);
    renderChanges(result);
    renderMonths(result);
    renderTrace(result);
    $("r-notices").replaceChildren(...result.notices.map((n) => el("li", {}, txt(n.message, "result"))));
    renderCode(result);
    saveUrl();
    $("cal-google").href = googleCalendarUrl(calendarEvent());
    renderPresets();
    updateLangNote();
  } catch (err) {
    lastResult = null;
    $("r-error").textContent = err.message;
    $("r-error").hidden = false;
    for (const id of ["r-changes", "r-months", "r-legend", "r-trace", "r-notices"]) $(id).replaceChildren();
    $("r-countdown").textContent = "";
  }
}

function renderVerdict(iso, leafPrefix, dateId) {
  $(`${leafPrefix}-month`).textContent = fmt(iso, { month: "long", year: "numeric" }).toLocaleUpperCase(state.lang);
  $(`${leafPrefix}-day`).textContent = num(Number(iso.slice(8)));
  $(`${leafPrefix}-weekday`).textContent = fmt(iso, { weekday: "long" });
  $(dateId).textContent = fmt(iso, { day: "numeric", month: "long", year: "numeric", weekday: "long" });
}

function renderChanges(result) {
  const chips = [];
  for (const s of result.trace) {
    if (!s.changed) continue;
    const d = quantity(Math.abs(dayDiff(s.before, s.after)), "day");
    if (s.step === "shift_trigger") chips.push(t("chg.shift", { d }));
    else if (s.step === "recess") chips.push(t("chg.recess", { d }));
    else if (s.step === "roll") chips.push(t("chg.roll", { d }));
    else if (s.step === "add_days") chips.push(t("chg.add", { d }));
  }
  $("r-changes").replaceChildren(...chips.map((c) => el("li", {}, c)));
}

function recessWindows(pack, year) {
  const windows = [];
  for (const step of pack.steps) {
    if (step.type !== "recess" || step.mode === "defer_start") continue;
    for (const p of step.periods) {
      if ((p.since && year < p.since) || (p.until && year > p.until)) continue;
      const endYear = p.end < p.start ? year + 1 : year;
      windows.push([`${year}-${p.start}`, `${endYear}-${p.end}`]);
    }
  }
  return windows;
}

function renderMonths(result) {
  const count = result.trace.find((s) => s.step === "count");
  const rawEnd = count?.after;
  const start = count?.before;
  const cal = calendar(result.calendar);
  const pack = rulepack(result.rulepack);
  const showRecess = result.trace.some((s) => s.step === "recess");
  const months = [...new Set([rawEnd, result.deadline].filter(Boolean).map((d) => d.slice(0, 7)))].sort().slice(-2);
  const used = new Set();
  const weekdays = Array.from({ length: 7 }, (_, i) => fmt(addDaysIso("2024-01-01", i), { weekday: "short" }));
  const tables = months.map((ym) => {
    const [y, m] = ym.split("-").map(Number);
    const first = `${ym}-01`;
    const offset = (utc(first).getUTCDay() + 6) % 7;
    const days = new Date(Date.UTC(y, m, 0)).getUTCDate();
    const windows = showRecess ? [...recessWindows(pack, y - 1), ...recessWindows(pack, y)] : [];
    const rows = [];
    let row = [];
    for (let i = 0; i < offset; i++) row.push(el("td", { class: "out" }));
    for (let d = 1; d <= days; d++) {
      const iso = `${ym}-${String(d).padStart(2, "0")}`;
      const classes = [];
      let title = "";
      if (cal.weekend.has(((utc(iso).getUTCDay() + 6) % 7) + 1)) classes.push("we");
      try {
        const hols = cal.holidaysOn(iso, { kinds: ["public"] });
        if (hols.length) {
          classes.push(hols.every((h) => h.halfDayFrom) ? "half" : "hol", "hol");
          title = hols.map((h) => txt(h.name)).join(", ");
          used.add("hol");
        }
      } catch {
        /* outside the calendar's verified years */
      }
      if (windows.some(([a, b]) => a <= iso && iso <= b)) classes.push("recess"), used.add("recess");
      if (iso === start) classes.push("start"), used.add("start");
      if (iso === rawEnd && rawEnd !== result.deadline) classes.push("counted"), used.add("counted");
      if (iso === result.deadline) classes.push("final"), used.add("final");
      row.push(el("td", { class: classes.join(" "), title: title || false, "aria-current": iso === result.deadline ? "date" : false }, num(d)));
      if (row.length === 7) rows.push(el("tr", {}, ...row)), (row = []);
    }
    if (row.length) rows.push(el("tr", {}, ...row));
    return el(
      "div",
      { class: "month" },
      el("h3", {}, fmt(first, { month: "long", year: "numeric" })),
      el("table", { role: "grid" }, el("thead", {}, el("tr", {}, ...weekdays.map((w) => el("th", { scope: "col" }, w)))), el("tbody", {}, ...rows)),
    );
  });
  $("r-months").replaceChildren(...tables);
  const legend = [
    ["final", "k-final", "lg.final"],
    ["counted", "k-counted", "lg.counted"],
    ["recess", "k-recess", "lg.recess"],
    ["hol", "k-hol", "lg.hol"],
    ["start", "k-start", "lg.start"],
  ].filter(([key]) => used.has(key));
  $("r-legend").replaceChildren(...legend.map(([, cls, key]) => el("li", {}, el("i", { class: cls }), t(key))));
}

function renderTrace(result) {
  $("r-trace").replaceChildren(
    ...result.trace.map((s) => {
      const li = el("li", { class: s.changed ? "changed" : "" }, el("span", {}, txt(s.message)));
      if (s.citation) {
        const name = txt(s.citation.label, "result");
        const quote = txt(s.citation.quote, "result");
        const cite = s.citation.url
          ? el("a", { class: "cite", href: s.citation.url, target: "_blank", rel: "noopener", title: quote || false }, name)
          : el("span", { class: "cite", title: quote || false }, name);
        li.append(el("br"), cite);
      }
      return li;
    }),
  );
}

function renderCode(result) {
  const pack = rulepack(state.pack);
  const changed = Object.entries(state.options).filter(([k, v]) => pack.options[k].default !== v);
  const opts = changed.length ? `, options={${changed.map(([k, v]) => `"${k}": ${JSON.stringify(v)}`).join(", ")}}` : "";
  const cal = pack.calendarFamily && state.calendar !== pack.calendar.id ? `, calendar="${state.calendar}"` : "";
  const dir = direction() === "before" ? ', direction="before"' : "";
  $("r-code").textContent = `import lexdays\n\nr = lexdays.compute("${state.pack}", "${result.trigger}", "${periodString()}"${dir}${opts}${cal})\nprint(r.deadline)   # ${result.deadline}\nprint(r.explain("${engineLang()}"))`;
}

function saveUrl() {
  const q = new URLSearchParams({ lang: state.lang, pack: state.pack, date: $("trigger").value, period: periodString(), dir: direction() });
  if (PAGE_LANG) q.delete("lang");
  const pack = rulepack(state.pack);
  if (pack.calendarFamily && state.calendar !== pack.calendar.id) q.set("cal", state.calendar);
  for (const [k, v] of Object.entries(state.options)) if (pack.options[k].default !== v) q.set(`o.${k}`, String(v));
  history.replaceState(null, "", `${location.pathname}?${q}`);
}

function loadUrl() {
  const pack = params.get("pack");
  const known = COUNTRIES.flatMap((c) => c.packs);
  setPack(known.includes(pack) ? pack : state.lang === "tr" ? "tr/hmk" : state.lang === "de" ? "de/zpo" : "us/frcp", true);
  const period = params.get("period");
  const match = period && /^P(\d+)([DWMY])$|^(\d+)bd$/.exec(period);
  if (match) {
    $("amount").value = match[1] ?? match[3];
    $("unit").value = match[3] ? "business_day" : { D: "day", W: "week", M: "month", Y: "year" }[match[2]];
  }
  if (params.get("dir") === "before") setDirection("before");
  const spec = rulepack(state.pack);
  if (params.get("cal") && spec.calendarFamily) state.calendar = params.get("cal");
  for (const [k, s] of Object.entries(spec.options)) {
    const raw = params.get(`o.${k}`);
    const value = s.values.find((v) => String(v) === raw);
    if (value !== undefined) state.options[k] = value;
  }
  $("trigger").value = /^\d{4}-\d{2}-\d{2}$/.test(params.get("date") ?? "") ? params.get("date") : todayIso();
}

// ------------------------------------------------------------ business days

function renderBusiness() {
  const calId = $("b-calendar").value;
  const cal = calendar(calId);
  const date = $("b-date").value;
  const n = Math.round(Number($("b-n").value) || 0);
  const halfDays = $("b-half").checked ? "non_working" : "working";
  $("b-error").hidden = true;
  try {
    const out = cal.addBusinessDays(date, n, { halfDays });
    renderVerdict(out, "b-leaf", "b-date-out");
    const why = cal.nonWorkingReason(date, { halfDays });
    const label = why === null ? t("b.business") : why === "weekend" ? t("b.weekend") : txt(why.name);
    $("b-start").textContent = `${fmt(date, { day: "numeric", month: "long", year: "numeric" })}${colon()}${label}`;
    const year = Number(out.slice(0, 4));
    $("b-year").textContent = num(year);
    $("b-holidays").replaceChildren(
      ...cal.holidays(year).map((h) =>
        el(
          "li",
          {},
          el("time", { datetime: h.date }, fmt(h.date, { day: "numeric", month: "short", weekday: "short" })),
          el("span", {}, txt(h.name)),
          h.kind !== "public" ? el("span", { class: "tag" }, h.kind) : null,
          h.halfDayFrom ? el("span", { class: "tag" }, `${h.halfDayFrom}–`) : null,
        ),
      ),
    );
  } catch (err) {
    $("b-error").textContent = err.message;
    $("b-error").hidden = false;
    $("b-holidays").replaceChildren();
  }
}

function renderBusinessCalendars() {
  const current = $("b-calendar").value || (state.lang === "tr" ? "tr" : "us");
  $("b-calendar").replaceChildren(...listCalendars().map((id) => el("option", { value: id }, txt(calendar(id).name))));
  $("b-calendar").value = current;
}

// ------------------------------------------------------------------ wiring

async function applyLanguage() {
  await loadDict(state.lang);
  const root = document.documentElement;
  root.lang = state.lang;
  root.dir = LANGUAGES.find((l) => l.code === state.lang)?.dir ?? "ltr";
  document.title = t("doc.title");
  for (const node of document.querySelectorAll("[data-i18n]")) node.textContent = t(node.dataset.i18n);
  renderForm();
  run();
  renderBusinessCalendars();
  renderBusiness();
}

function toast(key) {
  $("toast").textContent = t(key);
  setTimeout(() => ($("toast").textContent = ""), 2500);
}

async function copy(text, okKey) {
  try {
    await navigator.clipboard.writeText(text);
    toast(okKey);
  } catch {
    toast("copyFail");
  }
}

// The result as plain text: rule pack, last day, the numbered explanation and this page's link.
function resultText() {
  const head = `${label("packs", state.pack, 0)} (${state.pack})\n${t("r.last")}${colon()}${$("r-date").textContent}\n\n`;
  return head + lastResult.explain(engineLang()) + `\n\n${location.href}`;
}

function calendarEvent() {
  return {
    date: lastResult.deadline,
    summary: `${t("r.last")}${colon()}${label("packs", state.pack, 0)}`,
    description: `${resultText()}\n\n${t("foot")}`,
    url: location.href,
  };
}

function downloadIcs() {
  const event = calendarEvent();
  const id = globalThis.crypto?.randomUUID?.() ?? String(Math.random()).slice(2);
  const file = new Blob([buildIcs({ ...event, uid: `${event.date}-${id}@lexdays` })], { type: "text/calendar;charset=utf-8" });
  const link = el("a", { href: URL.createObjectURL(file), download: `lexdays-${event.date}.ics` });
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(link.href), 10_000);
  toast("calSaved");
}

$("lang").replaceChildren(...LANGUAGES.map((l) => el("option", { value: l.code, lang: l.code }, l.name)));
$("lang").value = state.lang;
// Switching language opens that language's page and keeps the inputs, which saveUrl() keeps in the query.
$("lang").addEventListener("change", () => {
  const q = new URLSearchParams(location.search);
  q.delete("lang");
  const query = q.toString();
  location.href = `${PAGE_LANG ? "../" : "./"}${$("lang").value}/${query ? `?${query}` : ""}`;
});
$("today").addEventListener("click", () => {
  $("trigger").value = todayIso();
  run();
});
$("trigger").addEventListener("input", run);
for (const id of ["amount", "unit"]) $(id).addEventListener("input", run);
$("direction").addEventListener("click", (event) => {
  const button = event.target.closest("button");
  if (!button) return;
  setDirection(button.dataset.value);
  renderForm();
  run();
});
$("calendar").addEventListener("change", () => {
  state.calendar = $("calendar").value;
  run();
});
$("copy-result").addEventListener("click", () => {
  if (lastResult) copy(resultText(), "copied");
});
// The calendar menu is a <details>: it opens with the keyboard on its own; Escape or a click
// elsewhere closes it. run() keeps the Google Calendar link up to date.
$("cal").addEventListener("keydown", (event) => {
  if (event.key !== "Escape" || !$("cal").open) return;
  $("cal").open = false;
  $("cal").querySelector("summary").focus();
});
document.addEventListener("click", (event) => {
  if (!$("cal").contains(event.target)) $("cal").open = false;
});
$("cal-ics").addEventListener("click", () => {
  if (lastResult) downloadIcs();
  $("cal").open = false;
});
$("cal-google").addEventListener("click", () => ($("cal").open = false));
$("copy-link").addEventListener("click", () => copy(location.href, "linkCopied"));
for (const id of ["b-calendar", "b-date", "b-n", "b-half"]) $(id).addEventListener("input", renderBusiness);
$("b-today").addEventListener("click", () => {
  $("b-date").value = todayIso();
  renderBusiness();
});
for (const tab of ["deadline", "business"]) {
  $(`tab-${tab}`).addEventListener("click", () => {
    for (const other of ["deadline", "business"]) {
      $(`tab-${other}`).setAttribute("aria-selected", String(other === tab));
      $(`panel-${other}`).hidden = other !== tab;
    }
  });
}
for (const button of document.querySelectorAll(".codetabs button")) {
  button.addEventListener("click", () => {
    for (const b of document.querySelectorAll(".codetabs button")) b.setAttribute("aria-selected", String(b === button));
    for (const pre of document.querySelectorAll(".snippet")) pre.hidden = pre.dataset.code !== button.dataset.code;
  });
}
document.addEventListener("submit", (event) => event.preventDefault());

$("b-date").value = todayIso();
loadUrl();
await applyLanguage();
