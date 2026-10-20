// Writes the demo's per-language pages (site/<lang>/index.html) and site/sitemap.xml from
// site/index.html and the title and description in site/i18n/<lang>.js, and fills the head of
// site/index.html with the language links search engines need (hreflang).
//
//   node scripts/build-site-pages.mjs
//
// CI runs it and fails if the result differs from the committed files.
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const SITE = join(dirname(fileURLToPath(import.meta.url)), "..", "site");
const BASE = "https://dogood-studio.github.io/legal-deadline-calculator/";
const LANGS = ["en", "tr", "de", "fr", "es", "it", "pt", "nl", "ru", "ar", "zh", "ja"];
const OG_LOCALE = { en: "en_US", tr: "tr_TR", de: "de_DE", fr: "fr_FR", es: "es_ES", it: "it_IT", pt: "pt_PT", nl: "nl_NL", ru: "ru_RU", ar: "ar_AR", zh: "zh_CN", ja: "ja_JP" };
const START = "  <!-- seo:start (written by scripts/build-site-pages.mjs) -->";
const END = "  <!-- seo:end -->";

const esc = (s) => s.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const dict = {};
for (const lang of LANGS) dict[lang] = (await import(pathToFileURL(join(SITE, "i18n", `${lang}.js`)).href)).default.ui;

const alternates = [
  ...LANGS.map((l) => `  <link rel="alternate" hreflang="${l}" href="${BASE}${l}/">`),
  `  <link rel="alternate" hreflang="x-default" href="${BASE}">`,
].join("\n");

// The head block for one page: the root page (lang null) speaks English to search engines and
// leaves the visitor's language to the browser; a language page is that language only.
function head(lang) {
  const ui = dict[lang ?? "en"];
  const url = lang ? `${BASE}${lang}/` : BASE;
  return [
    START,
    `  <title>${esc(ui["doc.title"])}</title>`,
    `  <meta name="description" content="${esc(ui["doc.description"])}">`,
    `  <link rel="canonical" href="${url}">`,
    alternates,
    `  <meta property="og:type" content="website">`,
    `  <meta property="og:title" content="${esc(ui["doc.title"])}">`,
    `  <meta property="og:description" content="${esc(ui["doc.description"])}">`,
    `  <meta property="og:url" content="${url}">`,
    `  <meta property="og:locale" content="${OG_LOCALE[lang ?? "en"]}">`,
    `  <meta property="og:image" content="${BASE}assets/og.png">`,
    `  <meta property="og:image:width" content="1280">`,
    `  <meta property="og:image:height" content="640">`,
    `  <meta name="twitter:card" content="summary_large_image">`,
    END,
  ].join("\n");
}
const fill = (html, lang) => {
  const a = html.indexOf(START);
  const b = html.indexOf(END);
  if (a < 0 || b < a) throw new Error("site/index.html has no seo:start / seo:end block");
  return html.slice(0, a) + head(lang) + html.slice(b + END.length);
};

const indexPath = join(SITE, "index.html");
const index = fill(readFileSync(indexPath, "utf8"), null);
writeFileSync(indexPath, index);

for (const lang of LANGS) {
  const dir = lang === "ar" ? ' dir="rtl"' : "";
  const page = fill(index, lang)
    .replace(/<html lang="[^"]*">/, `<html lang="${lang}"${dir} data-page-lang="${lang}">`)
    .replace("<!doctype html>", "<!doctype html>\n<!-- Generated from ../index.html by scripts/build-site-pages.mjs. Edit that file and rerun the script. -->")
    .replace('href="style.css"', 'href="../style.css"')
    .replace('href="manifest.webmanifest"', 'href="../manifest.webmanifest"')
    .replace('href="assets/icon-180.png"', 'href="../assets/icon-180.png"')
    .replace('href="opensearch.xml"', 'href="../opensearch.xml"')
    .replace('src="app.js"', 'src="../app.js"');
  mkdirSync(join(SITE, lang), { recursive: true });
  writeFileSync(join(SITE, lang, "index.html"), page);
}

const links = (indent) =>
  [...LANGS.map((l) => `${indent}<xhtml:link rel="alternate" hreflang="${l}" href="${BASE}${l}/"/>`),
    `${indent}<xhtml:link rel="alternate" hreflang="x-default" href="${BASE}"/>`].join("\n");
const urls = [BASE, ...LANGS.map((l) => `${BASE}${l}/`)]
  .map((loc) => `  <url>\n    <loc>${loc}</loc>\n${links("    ")}\n  </url>`)
  .join("\n");
writeFileSync(
  join(SITE, "sitemap.xml"),
  `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n${urls}\n</urlset>\n`,
);
console.log(`wrote site/index.html head, ${LANGS.length} language pages and site/sitemap.xml`);
