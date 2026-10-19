// Demo page for lexdays. Uses the published ESM bundle (copied to assets/ at build time).
import { calendar, compute, listCalendars, listRulepacks, rulepack } from "./assets/lexdays.js";

const UI = {
  en: {
    "nav.github": "GitHub", "nav.reliability": "Reliability",
    "hero.title": "Legal deadlines, explained.",
    "hero.lead": "Pick a jurisdiction, enter the date of service and the period. You get the last day, every step that led to it, and the article or decision behind each step.",
    "tab.deadline": "Deadline", "tab.business": "Business days",
    "f.pack": "Rules", "f.trigger": "Date of service / event", "f.calendar": "Court's location (holidays)",
    "f.amount": "Period", "f.unit": "Unit", "f.direction": "Direction", "f.options": "Options",
    "u.day": "days", "u.week": "weeks", "u.month": "months", "u.year": "years", "u.business_day": "business days",
    "d.after": "after the date", "d.before": "before the date (e.g. a hearing)",
    "r.deadline": "Last day", "r.endsAt": "Ends at", "r.code": "Same calculation in code",
    "b.calendar": "Calendar", "b.date": "Start date", "b.n": "± business days",
    "b.half": "Treat half days (eves) as non-working", "b.result": "Result", "b.holidays": "Holidays in",
    "b.business": "business day", "b.weekend": "weekend",
    "i.title": "Use it in your code",
    "i.text": "Zero dependencies, MIT licensed. Python and TypeScript give identical results, checked by a shared test-suite and 1,800 random differential cases.",
    "foot.disclaimer": "Informational tool, not legal advice. Statutes, case law, court orders and local practice take precedence. Always check a deadline that matters.",
    "opt.default": "default",
  },
  tr: {
    "nav.github": "GitHub", "nav.reliability": "Güvenilirlik",
    "hero.title": "Hukuki süreler, gerekçesiyle.",
    "hero.lead": "Kural paketini seçin, tebliğ tarihini ve süreyi girin. Son günü, oraya götüren her adımı ve her adımın dayandığı kanun maddesini veya kararı görürsünüz.",
    "tab.deadline": "Süre hesapla", "tab.business": "İş günü",
    "f.pack": "Kurallar", "f.trigger": "Tebliğ / olay tarihi", "f.calendar": "Mahkemenin yeri (tatiller)",
    "f.amount": "Süre", "f.unit": "Birim", "f.direction": "Yön", "f.options": "Seçenekler",
    "u.day": "gün", "u.week": "hafta", "u.month": "ay", "u.year": "yıl", "u.business_day": "iş günü",
    "d.after": "tarihten sonra", "d.before": "tarihten önce (ör. duruşma)",
    "r.deadline": "Son gün", "r.endsAt": "Bitiş saati", "r.code": "Aynı hesap kodla",
    "b.calendar": "Takvim", "b.date": "Başlangıç tarihi", "b.n": "± iş günü",
    "b.half": "Yarım günleri (arife) çalışılmayan say", "b.result": "Sonuç", "b.holidays": "Tatiller:",
    "b.business": "iş günü", "b.weekend": "hafta sonu",
    "i.title": "Kodunuzda kullanın",
    "i.text": "Bağımlılıksız, MIT lisanslı. Python ve TypeScript aynı sonucu verir; ortak test kümesi ve 1.800 rastgele karşılaştırma vakasıyla doğrulanır.",
    "foot.disclaimer": "Bilgilendirme amaçlıdır, hukuki danışmanlık değildir. Kanun, içtihat, mahkeme kararları ve yerel uygulama önceliklidir. Önemli bir süreyi mutlaka kontrol edin.",
    "opt.default": "varsayılan",
  },
};

const $ = (id) => document.getElementById(id);
const pick = (text, lang) => (text ? text[lang] ?? text.en ?? Object.values(text)[0] ?? "" : "");
const today = new Date();
const isoToday = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;

const params = new URLSearchParams(location.search);
let lang = params.get("lang") === "tr" || (!params.get("lang") && navigator.language?.startsWith("tr")) ? "tr" : "en";

function t(key) {
  return UI[lang][key] ?? UI.en[key] ?? key;
}

function applyLanguage() {
  document.documentElement.lang = lang;
  for (const el of document.querySelectorAll("[data-i18n]")) el.textContent = t(el.dataset.i18n);
  $("lang-toggle").textContent = lang === "tr" ? "EN" : "TR";
  fillPacks();
  fillCalendars();
  render();
  renderBusiness();
}

// ---------------------------------------------------------------- deadline

const packs = listRulepacks().map((id) => rulepack(id));

function fillPacks() {
  const select = $("pack");
  const current = select.value || params.get("pack") || (lang === "tr" ? "tr/hmk" : "us/frcp");
  select.innerHTML = "";
  const groups = new Map();
  for (const p of packs) {
    const key = p.jurisdiction ?? "";
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(p);
  }
  for (const [jurisdiction, list] of groups) {
    const group = document.createElement("optgroup");
    group.label = jurisdiction;
    for (const p of list) group.append(new Option(pick(p.name, lang), p.id));
    select.append(group);
  }
  select.value = packs.some((p) => p.id === current) ? current : packs[0].id;
  onPackChange(false);
}

function onPackChange(rerender = true) {
  const pack = rulepack($("pack").value);
  $("pack-desc").textContent = pick(pack.description, lang);
  const calField = $("calendar-field");
  const calSelect = $("calendar");
  calSelect.innerHTML = "";
  if (pack.calendarFamily) {
    const family = pack.calendarFamily;
    for (const id of listCalendars().filter((c) => c === family || c.startsWith(`${family}-`))) {
      calSelect.append(new Option(pick(calendar(id).name, lang), id));
    }
    calSelect.value = pack.calendar.id;
    calField.hidden = false;
  } else {
    calField.hidden = true;
  }
  const box = $("options");
  box.innerHTML = "";
  const names = Object.keys(pack.options);
  if (names.length) {
    const legend = document.createElement("legend");
    legend.textContent = t("f.options");
    box.append(legend);
  }
  for (const name of names) {
    const spec = pack.options[name];
    const label = document.createElement("label");
    label.className = "field";
    const title = document.createElement("span");
    title.textContent = name;
    const select = document.createElement("select");
    select.dataset.option = name;
    for (const value of spec.values) {
      const text = value === spec.default ? `${value} (${t("opt.default")})` : String(value);
      const option = new Option(text, JSON.stringify(value));
      select.append(option);
    }
    select.value = JSON.stringify(spec.default);
    const hint = document.createElement("small");
    hint.className = "hint";
    hint.textContent = pick(spec.description, lang);
    label.append(title, select, hint);
    box.append(label);
  }
  if (rerender) render();
}

function periodString(amount, unit) {
  return unit === "business_day" ? `${amount}bd` : `P${amount}${unit[0].toUpperCase()}`;
}

function render() {
  const packId = $("pack").value;
  const trigger = $("trigger").value;
  const amount = Number($("amount").value);
  const unit = $("unit").value;
  const direction = $("direction").value;
  const options = {};
  for (const select of $("options").querySelectorAll("select")) options[select.dataset.option] = JSON.parse(select.value);
  const pack = rulepack(packId);
  const cal = pack.calendarFamily ? $("calendar").value : undefined;
  $("r-error").hidden = true;
  try {
    const result = compute(packId, trigger, periodString(amount, unit), { direction, options, calendar: cal });
    const lines = result.explain(lang).split("\n");
    $("r-date").textContent = lines.find((l) => /^(Deadline|Son gün):/.test(l))?.split(": ").slice(1).join(": ") ?? result.deadline;
    $("r-time").textContent = result.endsAt ? `${t("r.endsAt")}: ${result.endsAt}${result.timezone ? ` (${result.timezone})` : ""}` : "";
    const list = $("r-trace");
    list.innerHTML = "";
    for (const step of result.trace) {
      const li = document.createElement("li");
      if (step.changed) li.className = "changed";
      li.append(document.createTextNode(pick(step.message, lang)));
      if (step.citation) {
        li.append(document.createElement("br"));
        const cite = document.createElement(step.citation.url ? "a" : "span");
        cite.className = "cite";
        cite.textContent = pick(step.citation.label, lang);
        if (step.citation.url) {
          cite.href = step.citation.url;
          cite.target = "_blank";
          cite.rel = "noopener";
        }
        const quote = pick(step.citation.quote, lang);
        if (quote) cite.title = quote;
        li.append(cite);
      }
      list.append(li);
    }
    const notices = $("r-notices");
    notices.innerHTML = "";
    for (const n of result.notices) {
      const li = document.createElement("li");
      li.textContent = pick(n.message, lang);
      notices.append(li);
    }
    const opts = Object.keys(options).length ? `, options=${JSON.stringify(options)}` : "";
    const calArg = cal && cal !== pack.calendar.id ? `, calendar="${cal}"` : "";
    const dirArg = direction === "before" ? `, direction="before"` : "";
    $("r-code").textContent =
      `import lexdays\n\nr = lexdays.compute("${packId}", "${trigger}", "${periodString(amount, unit)}"${dirArg}${opts.replace(/true/g, "True").replace(/false/g, "False")}${calArg})\nprint(r.deadline)\nprint(r.explain("${lang}"))`;
    const url = new URL(location.href);
    url.search = new URLSearchParams({ lang, pack: packId, date: trigger, n: String(amount), unit }).toString();
    history.replaceState(null, "", url);
  } catch (err) {
    $("r-date").textContent = "–";
    $("r-time").textContent = "";
    $("r-trace").innerHTML = "";
    $("r-notices").innerHTML = "";
    $("r-error").textContent = err.message;
    $("r-error").hidden = false;
  }
}

// ------------------------------------------------------------ business days

function fillCalendars() {
  const select = $("b-calendar");
  const current = select.value || (lang === "tr" ? "tr" : "us");
  select.innerHTML = "";
  for (const id of listCalendars()) select.append(new Option(`${id} — ${pick(calendar(id).name, lang)}`, id));
  select.value = current;
}

function renderBusiness() {
  const cal = calendar($("b-calendar").value);
  const date = $("b-date").value;
  const n = Number($("b-n").value);
  const halfDays = $("b-half").checked ? "non_working" : "working";
  try {
    const out = cal.addBusinessDays(date, n, { halfDays });
    $("b-out").textContent = out;
    const why = cal.nonWorkingReason(date, { halfDays });
    const label = why === null ? t("b.business") : why === "weekend" ? t("b.weekend") : pick(why.name, lang);
    $("b-reason").textContent = `${date}: ${label}`;
    const year = Number(date.slice(0, 4));
    $("b-year").textContent = String(year);
    const list = $("b-holidays");
    list.innerHTML = "";
    for (const h of cal.holidays(year)) {
      const li = document.createElement("li");
      const time = document.createElement("time");
      time.dateTime = h.date;
      time.textContent = h.date;
      li.append(time, document.createTextNode(pick(h.name, lang)));
      for (const tag of [h.kind !== "public" ? h.kind : null, h.halfDayFrom ? `${h.halfDayFrom}–` : null, h.observedFrom ? "observed" : null]) {
        if (!tag) continue;
        const span = document.createElement("span");
        span.className = "tag";
        span.textContent = tag;
        li.append(span);
      }
      list.append(li);
    }
  } catch (err) {
    $("b-out").textContent = "–";
    $("b-reason").textContent = err.message;
    $("b-holidays").innerHTML = "";
  }
}

// ------------------------------------------------------------------- wiring

function selectTab(name) {
  for (const tab of ["deadline", "business"]) {
    $(`tab-${tab}`).setAttribute("aria-selected", String(tab === name));
    $(`panel-${tab}`).hidden = tab !== name;
  }
}

$("trigger").value = params.get("date") ?? isoToday;
$("amount").value = params.get("n") ?? "2";
$("unit").value = params.get("unit") ?? "week";
$("b-date").value = isoToday;
$("pack").addEventListener("change", () => onPackChange());
$("calendar").addEventListener("change", render);
for (const id of ["trigger", "amount", "unit", "direction"]) $(id).addEventListener("input", render);
$("options").addEventListener("change", render);
for (const id of ["b-calendar", "b-date", "b-n", "b-half"]) $(id).addEventListener("input", renderBusiness);
$("tab-deadline").addEventListener("click", () => selectTab("deadline"));
$("tab-business").addEventListener("click", () => selectTab("business"));
$("lang-toggle").addEventListener("click", () => {
  lang = lang === "tr" ? "en" : "tr";
  applyLanguage();
});
document.addEventListener("submit", (event) => event.preventDefault());
applyLanguage();
