"""Weekly watch of the official sources behind lexdays' holiday calendars and rule packs.

    uv run --project python --with pypdf==6.19.0 python scripts/watch_sources.py [--report FILE] [--accept]

It never changes holiday or rule data; a wrong date in lexdays means a missed deadline for
someone, so every change goes through a human. It reports, most important first:

1. quoted rule text found less than before at its source (the law may have changed);
2. EU acts that amend a cited EU act (found through the Publications Office's SPARQL endpoint);
3. a new Court of Justice list of official holidays on EUR-Lex (``eu-cj`` needs updating);
4. Resmî Gazete items of the last eight days whose titles mention a law or holiday the
   Turkish packs rely on;
5. sources whose text changed since the accepted fingerprint (content or only layout);
6. sources that cannot be read automatically, to check by hand every three months.

After reviewing a report, ``--accept`` records the current state (fingerprints, how much of
each quote was found, the newest amending act, the latest EUR-Lex list, the date of the hand
check) in
``scripts/source-fingerprints.json`` so the same change is not reported again. A source whose
page changes on every visit can be marked ``"volatile": true`` there to skip its fingerprint.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import http.client
import json
import math
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FINGERPRINTS = ROOT / "scripts" / "source-fingerprints.json"
USER_AGENT = "lexdays-source-watch/1 (+https://github.com/DoGood-Studio/legal-deadline-calculator)"
QUOTE_THRESHOLD = 0.8  # a new quote must be found at least this much; an accepted one must not drop
SHINGLE = 5  # words per compared piece of a quote
MANUAL_EVERY = timedelta(days=91)  # sources that cannot be read automatically are checked by hand
# Where a stored quote joins separate passages: an ellipsis, an article label ("m.102:", "Art. 49:")
# or a paragraph number ("(4)"). The text on either side of a break is compared separately.
_BREAKS = re.compile(
    r"\s*(?:…|\.\.\.)\s*|(?:\b(?:m|Art|Arts)\.?|§)\s*[\d./-]+[a-z]?\s*:\s*|\(\d+\)\s*", re.IGNORECASE
)
SPARQL = "https://publications.europa.eu/webapi/rdf/sparql"
CJ_LISTS = """PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
SELECT DISTINCT ?date ?title WHERE {
  ?work cdm:work_date_document ?date .
  FILTER(?date >= "2024-01-01"^^<http://www.w3.org/2001/XMLSchema#date>)
  ?exp cdm:expression_belongs_to_work ?work ;
       cdm:expression_uses_language <http://publications.europa.eu/resource/authority/language/ENG> ;
       cdm:expression_title ?title .
  FILTER(CONTAINS(LCASE(STR(?title)), "official holidays and judicial vacations"))
} ORDER BY DESC(?date) LIMIT 5"""
# The EUR-Lex website challenges automated visitors, so a cited EU act is read from the
# Publications Office repository (Cellar) instead, found by its ELI or CELEX number.
EU_FILES = """PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
SELECT ?man ?type WHERE {{
  ?work cdm:{prop} ?id . FILTER(STR(?id) = "{value}")
  ?exp cdm:expression_belongs_to_work ?work ;
       cdm:expression_uses_language <http://publications.europa.eu/resource/authority/language/ENG> .
  ?man cdm:manifestation_manifests_expression ?exp ; cdm:manifestation_type ?type .
}}"""
EU_AMENDMENTS = """PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
SELECT DISTINCT ?date ?celex WHERE {{
  ?work cdm:{prop} ?id . FILTER(STR(?id) = "{value}")
  ?act cdm:resource_legal_amends_resource_legal ?work ; cdm:work_date_document ?date .
  OPTIONAL {{ ?act cdm:resource_legal_id_celex ?celex }}
}} ORDER BY DESC(?date)"""
RESMI_GAZETE = "https://www.resmigazete.gov.tr/eskiler/{y:04d}/{m:02d}/{y:04d}{m:02d}{d:02d}.htm"
# Words in Official Gazette titles (and in the text of laws and decrees) that may touch the Turkish
# packs or the Turkish calendar: the codes the packs cite, holidays, and suspensions of time limits
# (Law 7226 in 2020, CBK 120 "Yargı Alanında Alınan Tedbirler" in 2023).
RG_KEYWORDS = (
    "Hukuk Muhakemeleri", "İcra ve İflas", "Ceza Muhakemesi", "İdari Yargılama", "Vergi Usul",
    "Tebligat", "Anayasa Mahkemesinin Kuruluşu", "Ulusal Bayram ve Genel Tatil", "genel tatil",
    "idari izin", "adli tatil", "Arabuluculuk", "Yargı Alanında", "sürelerin dur", "sürelerin uzat",
    "mücbir sebep",
)


@dataclass
class Source:
    url: str
    used_by: set[str] = field(default_factory=set)
    quotes: list[tuple[str, str]] = field(default_factory=list)  # (where, quoted text)


@dataclass
class Result:
    source: Source
    status: str  # "ok" or why the text could not be read
    fingerprint: str | None = None
    quote_shares: list[tuple[str, float]] = field(default_factory=list)  # (where, share found)
    amended_by: list[tuple[str, str]] = field(default_factory=list)  # EU acts: (date, CELEX), newest first


# ------------------------------------------------------------------ sources


def collect_sources(root: Path = ROOT) -> dict[str, Source]:
    """Every URL cited by a rule pack or listed as a calendar source, with who uses it."""
    sources: dict[str, Source] = {}

    def add(url: str, user: str) -> Source:
        src = sources.setdefault(url, Source(url))
        src.used_by.add(user)
        return src

    for path in sorted((root / "data" / "rulepacks").rglob("*.json")):
        pack = json.loads(path.read_text(encoding="utf-8"))
        for cid, cite in pack.get("citations", {}).items():
            if not cite.get("url"):
                continue
            src = add(cite["url"], f"{pack['id']} ({cid})")
            for lang, text in (cite.get("quote") or {}).items():
                src.quotes.append((f"{pack['id']} {cid} [{lang}]", text))
    for path in sorted((root / "data" / "calendars").glob("*.json")):
        cal = json.loads(path.read_text(encoding="utf-8"))
        for item in cal.get("sources", []):
            if item.get("url"):
                add(item["url"], f"calendar {cal['id']}")
    return sources


def unlinked_citations(root: Path = ROOT) -> list[str]:
    """Rule-pack citations without a link (court decisions), which only a person can review."""
    rows = []
    for path in sorted((root / "data" / "rulepacks").rglob("*.json")):
        pack = json.loads(path.read_text(encoding="utf-8"))
        for cid, cite in pack.get("citations", {}).items():
            if not cite.get("url"):
                label = cite.get("label", {})
                rows.append(f"{pack['id']} ({cid}): {label.get('en') or label.get('tr', '')}")
    return rows


# --------------------------------------------------------------- text tools


def compact(text: str) -> str:
    """Case-folded letters and digits without accents, so layout, punctuation and spelling
    variants such as "Adlî"/"Adli" do not matter."""
    text = unicodedata.normalize("NFKD", text.casefold())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[\W_]+", "", text)


def fold(text: str) -> str:
    """Lower case without accents or the dotted/dotless i distinction, keeping one character per
    character so positions in the folded text are positions in the original."""
    return "".join(unicodedata.normalize("NFKD", c.lower()[:1])[:1] for c in text).replace("ı", "i")


def decode(data: bytes, content_type: str = "") -> str:
    """Page bytes as text, using the declared charset (the Resmî Gazete index is windows-1254)."""
    declared = re.search(r"charset=[\"']?([\w-]+)", content_type, re.IGNORECASE) or re.search(
        rb"<meta[^>]+charset=[\"']?([\w-]+)", data[:4096], re.IGNORECASE
    )
    if declared:
        name = declared.group(1)
        try:
            return data.decode(name if isinstance(name, str) else name.decode("ascii"), errors="replace")
        except LookupError:
            pass
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("cp1252", errors="replace")


def html_text(markup: str) -> str:
    markup = re.sub(r"(?is)<(script|style|noscript|nav|header|footer|svg)\b.*?</\1>", " ", markup)
    markup = re.sub(r"(?s)<!--.*?-->", " ", markup)
    return html.unescape(re.sub(r"<[^>]+>", " ", markup))


def pdf_text(data: bytes) -> str:
    from pypdf import PdfReader  # noqa: PLC0415 (only a watch run needs it: uv run --with pypdf)

    return "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(data)).pages)


def page_text(data: bytes, content_type: str) -> str:
    if "pdf" in content_type.lower() or data[:5] == b"%PDF-":
        return pdf_text(data)
    return html_text(decode(data, content_type))


def quote_share_found(quote: str, page: str) -> float:
    """Share of a quote, as overlapping five-word pieces, that still appears in the page (compacted).

    Pieces make the check tolerant of an ellipsis, a short label in front of the quote
    ("§ 187 Abs. 1 BGB:") or an extra word, while a rewritten sentence still fails.
    """
    grams = []
    for part in _BREAKS.split(quote):
        words = [w for w in (compact(word) for word in part.split()) if w]
        if len(words) < SHINGLE:
            grams.extend(["".join(words)] if words else [])
            continue
        grams.extend("".join(words[i:i + SHINGLE]) for i in range(len(words) - SHINGLE + 1))
    if not grams:
        return 1.0
    return sum(1 for gram in grams if gram in page) / len(grams)


# Parts of a page that change with every visit rather than with the law, such as the date of
# the visit that revosax.sachsen.de prints as "Stand vom 20.10.2026".
_VISIT_STAMPS = re.compile(r"Stand vom\s*\d{1,2}\.\d{1,2}\.\d{4}")


def fingerprint(text: str) -> str:
    return hashlib.sha256(compact(_VISIT_STAMPS.sub(" ", text)).encode("utf-8")).hexdigest()[:16]


# ------------------------------------------------------------------ network


def fetch(url: str, timeout: int = 60) -> tuple[bytes, str]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "en, tr, de"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(), response.headers.get("Content-Type", "")


def sparql(query: str) -> list[dict]:
    url = SPARQL + "?" + urllib.parse.urlencode({"query": query})
    headers = {"User-Agent": USER_AGENT, "Accept": "application/sparql-results+json"}
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120) as response:
        return json.load(response)["results"]["bindings"]


def eu_act(url: str) -> tuple[str, str] | None:
    """(Cellar property, value) for an EU act cited by its ELI or by a EUR-Lex CELEX address."""
    if match := re.fullmatch(r"https?://data\.europa\.eu/(eli/[\w/.-]+)", url):
        return "resource_legal_eli", "http://data.europa.eu/" + match.group(1)
    if match := re.search(r"//eur-lex\.europa\.eu/.*[?&]uri=CELEX:([0-9A-Z()]+)$", url, re.IGNORECASE):
        return "resource_legal_id_celex", match.group(1)
    return None


def eu_document(prop: str, value: str) -> tuple[bytes, str]:
    """The English text of an EU act from Cellar: XHTML if there is one, otherwise the PDF."""
    rows = sparql(EU_FILES.format(prop=prop, value=value))
    files = {row["type"]["value"]: row["man"]["value"] for row in rows}
    for kind in ("xhtml", "html", "pdfa2a", "pdfa1a", "pdf"):
        if kind in files:
            return fetch(files[kind].replace("http://", "https://", 1) + "/DOC_1", timeout=45)
    raise urllib.error.URLError("no English text in the Publications Office repository")


def eu_amendments(prop: str, value: str) -> list[tuple[str, str]]:
    """(date, CELEX) of the acts that amend an EU act, newest first."""
    rows = sparql(EU_AMENDMENTS.format(prop=prop, value=value))
    return [(row["date"]["value"], row.get("celex", {}).get("value", "no CELEX number")) for row in rows]


def read_source(src: Source, attempts: int = 2) -> Result:
    act = eu_act(src.url)
    amended_by: list[tuple[str, str]] = []
    for attempt in range(attempts):
        try:
            if act:
                (data, ctype), amended_by = eu_document(*act), eu_amendments(*act)
            else:
                data, ctype = fetch(src.url, timeout=45)
            break
        except urllib.error.HTTPError as exc:
            if exc.code < 500 or attempt + 1 == attempts:
                return Result(src, f"HTTP {exc.code}")
        # A dropped connection (IncompleteRead) must not stop the whole watch.
        except (urllib.error.URLError, http.client.HTTPException, TimeoutError, OSError,
                ValueError, KeyError) as exc:
            if attempt + 1 == attempts:
                reason = getattr(exc, "reason", exc)
                name = type(reason).__name__ if isinstance(reason, BaseException) else str(reason)
                return Result(src, f"not reachable ({name})")
    try:
        text = page_text(data, ctype)
    except Exception as exc:  # a broken or scanned PDF must not stop the whole watch
        return Result(src, f"text could not be extracted ({type(exc).__name__})")
    page = compact(text)
    if len(page) < 400:
        return Result(src, "no readable text (scanned document, or the site needs a browser)")
    result = Result(src, "ok", fingerprint=fingerprint(text), amended_by=amended_by)
    result.quote_shares = [(where, quote_share_found(quote, page)) for where, quote in src.quotes]
    return result


def quotes_to_report(result: Result, accepted: dict) -> list[tuple[str, float]]:
    """Quotes found less than before: below the accepted share, or below the threshold if new.

    Some quotes are close paraphrases and never match fully; once a person has accepted their
    share, any further drop (one changed word is enough) is reported.
    """
    known = accepted.get("quotes", {})
    return [
        (where, share) for where, share in result.quote_shares
        if share < known.get(where, QUOTE_THRESHOLD) - 1e-9
    ]


def latest_cj_lists() -> list[tuple[str, str]]:
    """(date, title) of the newest Court of Justice lists of official holidays on EUR-Lex."""
    rows = sparql(CJ_LISTS)
    return [(r["date"]["value"], r["title"]["value"].replace(" ", " ")) for r in rows]


def gazette_hits(today: date, days: int = 8) -> list[tuple[str, str, str]]:
    """(date, url, title) for Resmî Gazete items of the last days that may touch the Turkish data.

    Titles are matched against ``RG_KEYWORDS``. Laws and presidential decrees are also read in
    full, because an omnibus law (Law 7226 was "Bazı Kanunlarda Değişiklik Yapılmasına Dair
    Kanun") does not name the codes it amends in its title. Extra (mükerrer) issues of the same
    day are followed from the day's index.
    """
    hits = []
    for back in range(days):
        day = today - timedelta(days=back)
        pending, seen = [RESMI_GAZETE.format(y=day.year, m=day.month, d=day.day)], set()
        while pending:
            index = pending.pop(0)
            seen.add(index)
            try:
                markup = decode(*fetch(index, timeout=30))
            except (urllib.error.URLError, http.client.HTTPException, TimeoutError, OSError):
                continue
            for link, title in gazette_items(index, markup):
                if re.search(r"/\d{8}M\d+\.htm$", link):
                    pending.extend([link] if link not in seen and link not in pending else [])
                elif keyword := gazette_match(title):
                    hits.append((day.isoformat(), link, title))
                elif is_act(title) and (keyword := gazette_match(act_text(link))):
                    hits.append((day.isoformat(), link, f"{title} (the text mentions “{keyword}”)"))
    return hits


def gazette_items(index: str, markup: str) -> list[tuple[str, str]]:
    """(absolute https link, title) for every link on a Resmî Gazete index page."""
    items = []
    for href, inner in re.findall(r"""<a\b[^>]*?href=["']([^"']+)["'][^>]*>(.*?)</a>""", markup, re.S | re.I):
        link = urllib.parse.urljoin(index, href.strip()).replace("http://", "https://", 1)
        items.append((link, re.sub(r"\s+", " ", html_text(inner)).strip("–- ")))
    return items


def gazette_match(text: str) -> str | None:
    folded = fold(text)
    return next((keyword for keyword in RG_KEYWORDS if fold(keyword) in folded), None)


def is_act(title: str) -> bool:
    """A law or a presidential decree, which may amend a code without naming it in the title."""
    return title.endswith("Kanun") or "Kararname" in title


def act_text(link: str) -> str:
    try:
        data, ctype = fetch(link, timeout=45)
        return page_text(data, ctype)
    except Exception:  # an unreadable act only loses this extra check, the title was checked
        return ""


# ------------------------------------------------------------------- report


def _lasting(status: str) -> bool:
    """A failure that is unlikely to go away by itself: not a timeout, a server error, or a site
    refusing automated visitors (403, 429), which some do only from cloud servers such as CI."""
    return not status.startswith(("not reachable", "HTTP 5", "HTTP 403", "HTTP 429"))


def render(results: list[Result], accepted: dict, *, cj_lists: list[tuple[str, str]] | None,
           cj_error: str | None, gazette: list[tuple[str, str, str]], today: date,
           unlinked: list[str] | None = None) -> tuple[str, int]:
    """Markdown report (Turkish summary, bilingual headings, English details) and the number of findings."""
    known = accepted.get("sources", {})
    quotes = [(r, rows) for r in results if (rows := quotes_to_report(r, accepted))]
    changed = [
        r for r in results
        if r.status == "ok" and not known.get(r.source.url, {}).get("volatile")
        and known.get(r.source.url, {}).get("fingerprint") not in (None, r.fingerprint)
    ]
    new = [r for r in results if r.status == "ok" and not known.get(r.source.url, {}).get("fingerprint")]
    unreadable = [r for r in results if r.status != "ok"]
    broken = [r for r in unreadable if known.get(r.source.url, {}).get("fingerprint") and _lasting(r.status)]
    reviewed = accepted.get("manual_review")
    unlinked = unlinked or []
    manual_due = bool(unreadable or unlinked) and (
        not reviewed or today - date.fromisoformat(reviewed) >= MANUAL_EVERY
    )
    cj_known = accepted.get("cj_latest_list")
    cj_new = [row for row in (cj_lists or []) if cj_known and row[0] > cj_known]
    amended = [
        (r, rows) for r in results
        if (rows := [d for d in r.amended_by if d[0] > known.get(r.source.url, {}).get("amended_until", "")])
    ]
    n_quotes = sum(len(rows) for _, rows in quotes)
    n_amended = sum(len(rows) for _, rows in amended)
    findings = n_quotes + n_amended + len(cj_new) + len(gazette) + len(changed) + len(broken)
    findings += bool(cj_error) + manual_due

    lines = [
        f"**Özet:** {today:%d.%m.%Y} tarihinde kural paketlerinin ve takvimlerin dayandığı "
        f"{len(results)} kaynak tarandı.",
        "",
        f"- Kanun metni değişmiş olabilecek alıntı: {n_quotes}",
        f"- Atıf yapılan AB metnini değiştiren işlem: {n_amended}",
        f"- Yeni AB Adalet Divanı tatil listesi: {len(cj_new)}"
        + (" (EUR-Lex sorgusu çalışmadı)" if cj_error else ""),
        f"- İlgili olabilecek Resmî Gazete maddesi (son 8 gün): {len(gazette)}",
        f"- Metni değişen kaynak: {len(changed)}",
        f"- Elle kontrol listesi: {len(unreadable)} okunamayan kaynak, "
        f"{len(unlinked)} bağlantısız yargı kararı"
        + (" (üç aylık elle kontrol zamanı geldi)" if manual_due else "")
        + (f"; {len(broken)} kaynak önceden okunabiliyordu" if broken else ""),
        "",
        "Bekçi veriyi kendisi değiştirmez; her bulguyu bir kişi kontrol eder ve gerekirse düzeltir. "
        "Takvimler ayrıca her hafta CI'da python-holidays ve GOV.UK ile karşılaştırılır.",
        "",
        f"Checked {len(results)} sources cited by the rule packs and calendars on {today.isoformat()}. "
        "The watcher never changes data; a person reviews every finding. Every calendar except eu-cj "
        "is also compared with python-holidays (and gb-eaw with GOV.UK) by the weekly CI run.",
        "",
    ]

    def section(title: str, rows: list[str], note: str = "") -> None:
        lines.extend([f"## {title}", ""])
        if note:
            lines.extend([note, ""])
        lines.extend(rows or ["Yok / None."])
        lines.append("")

    def users(r: Result) -> str:
        return ", ".join(sorted(r.source.used_by))

    section("1. Alıntı artık tam bulunamıyor / Quoted rule text no longer found (check first)", [
        f"- {r.source.url}\n" + "\n".join(
            f"  - {where}: {share:.0%} of the quote found"
            + (f" (accepted: {accepted['quotes'][where]:.0%})" if where in accepted.get("quotes", {}) else "")
            for where, share in rows
        )
        for r, rows in quotes
    ], "The law may have been amended. Compare the article with the quote and the rule built on it.")
    section("2. Değiştiren AB işlemleri / EU acts amending a cited act", [
        f"- {r.source.url} (used by {users(r)})\n"
        + "\n".join(f"  - {d}: CELEX {celex} (https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:{celex})"
                    for d, celex in rows)
        for r, rows in amended
    ], "The cited text may be out of date. Check whether the amendment touches the cited articles.")
    cj_rows = [f"- {d}: {t}" for d, t in cj_new]
    if cj_error:
        cj_rows.append(f"- The EUR-Lex query failed ({cj_error}); check the Official Journal by hand.")
    section("3. Yeni AB Adalet Divanı tatil listesi / New Court of Justice list of official holidays",
            cj_rows, "Add the new list to `data/calendars/eu-cj.json` and extend `coverage.until`.")
    section("4. Resmî Gazete (son 8 gün) / Official Gazette items of the last 8 days that may matter", [
        f"- {d}: {excerpt} ({url})" for d, url, excerpt in gazette
    ], "Titles that mention a law or a holiday the Turkish packs and calendar rely on.")
    section("5. Metni değişen kaynaklar / Source text changed since it was last accepted", [
        f"- {r.source.url} (used by {users(r)})" for r in changed
    ], "The change may be content or only layout; open the page and check the cited article.")
    section("6. Okunamayan kaynaklar, elle kontrol / Could not be read, check by hand", [
        f"- {r.source.url}: {r.status}{' (readable before)' if r in broken else ''} (used by {users(r)})"
        for r in unreadable
    ] + [f"- {row}: court decision without a link" for row in unlinked],
        "Check these by hand every three months (for decisions: look for newer case law); "
        f"last done {reviewed or 'never'}.")
    if new:
        section("Yeni kaynaklar / New sources", [f"- {r.source.url}" for r in new],
                "Not compared yet; their fingerprints are recorded with `--accept`.")
    lines.extend([
        "## İncelemeden sonra / After review",
        "",
        "Fix the data if a source really changed (with a changelog entry and vectors), then run "
        "`uv run --project python --with pypdf==6.19.0 python scripts/watch_sources.py --accept` and commit "
        "`scripts/source-fingerprints.json`. Accepting also records that section 6 was checked by hand.",
    ])
    return "\n".join(lines) + "\n", findings


def accept(results: list[Result], accepted: dict, cj_lists: list[tuple[str, str]] | None,
           today: date) -> dict:
    """The accepted state after a person reviewed this run: fingerprints, quote shares, latest lists."""
    cited = {r.source.url for r in results}
    wheres = {where for r in results for where, _ in r.source.quotes}
    sources = {url: entry for url, entry in accepted.get("sources", {}).items() if url in cited}
    quotes = {where: share for where, share in accepted.get("quotes", {}).items() if where in wheres}
    for r in results:
        if r.status == "ok":
            sources.setdefault(r.source.url, {})["fingerprint"] = r.fingerprint
            if r.amended_by:
                sources[r.source.url]["amended_until"] = max(d for d, _ in r.amended_by)
            quotes.update({where: math.floor(share * 1000 + 1e-6) / 1000 for where, share in r.quote_shares})
    state = {"sources": dict(sorted(sources.items())), "quotes": dict(sorted(quotes.items()))}
    state["cj_latest_list"] = max((d for d, _ in cj_lists or []), default=accepted.get("cj_latest_list"))
    state["manual_review"] = today.isoformat()  # accepting includes the hand check of section 6
    return state


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--report", help="write the Markdown report to this file")
    parser.add_argument("--accept", action="store_true", help="record this run's state after reviewing it")
    parser.add_argument("--today", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

    accepted = json.loads(FINGERPRINTS.read_text(encoding="utf-8")) if FINGERPRINTS.exists() else {}
    results = []
    for src in sorted(collect_sources().values(), key=lambda s: s.url):
        result = read_source(src)
        results.append(result)
        print(f"{result.status[:12]:<12} {src.url}", flush=True)
    try:
        cj_lists, cj_error = latest_cj_lists(), None
    except Exception as exc:  # the EUR-Lex endpoint being down is itself a finding
        cj_lists, cj_error = None, f"{type(exc).__name__}: {exc}"
    gazette = gazette_hits(args.today)
    report, findings = render(results, accepted, cj_lists=cj_lists, cj_error=cj_error, gazette=gazette,
                              today=args.today, unlinked=unlinked_citations())
    if args.report:
        Path(args.report).write_text(report, encoding="utf-8")
    print("\n" + report)
    if args.accept:
        state = accept(results, accepted, cj_lists, args.today)
        FINGERPRINTS.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Accepted state recorded in {FINGERPRINTS.relative_to(ROOT).as_posix()}.")
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as out:
            out.write(f"has_findings={'true' if findings else 'false'}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
