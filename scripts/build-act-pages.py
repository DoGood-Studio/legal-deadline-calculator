# ruff: noqa: E501  (HTML templates read better unwrapped)
"""Writes one demo page per Turkish act (site/tr/sureler/<pack>-<act>/index.html) and the list
of all of them (site/tr/sureler/index.html).

Everything on a page comes from the rule packs and from the engine itself: the act's period and
start, the verbatim provision, and two worked examples computed here. Nothing legal is written by
hand, so a page cannot disagree with the calculator.

    uv run --project python python scripts/build-act-pages.py

CI runs it and fails if the result differs from the committed files.
"""

from __future__ import annotations

import html
import json
import shutil
from datetime import date, timedelta
from pathlib import Path

import lexdays

SITE = Path(__file__).resolve().parent.parent / "site"
OUT = SITE / "tr" / "sureler"
BASE = "https://dogood-studio.github.io/legal-deadline-calculator/"
# pack id -> (abbreviation, the demo's name for the pack, the statute)
PACKS = {
    "tr/hmk": ("HMK", "Hukuk davaları", "Hukuk Muhakemeleri Kanunu (6100)"),
    "tr/iik": ("İİK", "İcra ve iflas", "İcra ve İflas Kanunu (2004)"),
    "tr/cmk": ("CMK", "Ceza davaları", "Ceza Muhakemesi Kanunu (5271)"),
    "tr/iyuk": ("İYUK", "İdari ve vergi davaları", "İdari Yargılama Usulü Kanunu (2577)"),
    "tr/vuk": ("VUK", "Vergi usulü", "Vergi Usul Kanunu (213)"),
    "tr/aym": ("AYM", "Anayasa Mahkemesi", "Anayasa Mahkemesine bireysel başvuru (6216)"),
}
UNITS = {"day": "gün", "week": "hafta", "month": "ay", "year": "yıl", "business_day": "iş günü"}
MONTHS = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim",
          "Kasım", "Aralık"]
WEEKDAYS = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
# Example dates are fixed so the pages only change when the rules do.
ORDINARY_FROM = date(2026, 3, 2)
RECESS_SCAN = (date(2026, 5, 15), date(2026, 8, 31))
RECESS_TARGET = date(2026, 8, 5)
ICON = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect x='3' "
    "y='5' width='26' height='24' rx='5' fill='#fff' stroke='#1e3a5c' stroke-width='2'/%3E%3Cpath "
    "d='M3 10a5 5 0 0 1 5-5h16a5 5 0 0 1 5 5v2.5H3z' fill='#1e3a5c'/%3E%3Crect x='9' y='2' width='3.2' "
    "height='6.4' rx='1.6' fill='#1e3a5c' stroke='#fff'/%3E%3Crect x='19.8' y='2' width='3.2' "
    "height='6.4' rx='1.6' fill='#1e3a5c' stroke='#fff'/%3E%3Ctext x='16' y='26.6' text-anchor='middle' "
    "font-family='Georgia,serif' font-weight='700' font-size='15' fill='#b42318'%3E%C2%A7%3C/text%3E%3C/svg%3E"
)
MARK = (
    '<svg class="brand__mark" viewBox="0 0 32 32" aria-hidden="true"><rect x="3" y="5" width="26" '
    'height="24" rx="5" class="m-sheet"/><path d="M3 10a5 5 0 0 1 5-5h16a5 5 0 0 1 5 5v2.5H3z" '
    'class="m-band"/><rect x="9" y="2" width="3.2" height="6.4" rx="1.6" class="m-ring"/><rect '
    'x="19.8" y="2" width="3.2" height="6.4" rx="1.6" class="m-ring"/><text x="16" y="26.6" '
    'class="m-day">§</text></svg>'
)


def e(text: str) -> str:
    return html.escape(text, quote=True)


def period_text(period: lexdays.Period) -> str:
    return f"{period.amount} {UNITS[period.unit]}"


def long_date(day: date) -> str:
    return f"{day.day} {MONTHS[day.month - 1]} {day.year} {WEEKDAYS[day.weekday()]}"


def slug(pack: str, act_id: str) -> str:
    return f"{pack.split('/')[1]}-{act_id}"


def heading(label: str) -> str:
    """'Cevap dilekçesi' -> 'Cevap dilekçesi süresi'; labels that already name a period stay."""
    return label if label.lower().split(" (")[0].endswith(("süresi", "süre")) else f"{label} süresi"


def shared_labels() -> set[str]:
    """Labels used by more than one pack (istinaf, temyiz, ...): their headings name the law."""
    seen: dict[str, set[str]] = {}
    for pack in PACKS:
        rp = lexdays.rulepack(pack)
        for act_id in rp.acts:
            seen.setdefault(rp.act(act_id).label["tr"], set()).add(pack)
    return {label for label, packs in seen.items() if len(packs) > 1}


SHARED: set[str] = set()


def changed(result: lexdays.DeadlineResult, step: str) -> bool:
    return any(s.step == step and s.changed for s in result.trace)


def ordinary_example(pack: str, act_id: str) -> lexdays.DeadlineResult:
    """The first Monday from ORDINARY_FROM whose deadline needs no recess extension."""
    day = ORDINARY_FROM
    for _ in range(26):
        result = lexdays.compute(pack, day, act=act_id)
        if not changed(result, "recess"):
            return result
        day += timedelta(days=7)
    return result


def recess_example(pack: str, act_id: str) -> lexdays.DeadlineResult | None:
    """A start date whose period ends inside a recess (judicial recess, summer break), if the
    pack has one that extends this act: the one whose raw end is closest to RECESS_TARGET."""
    best: tuple[int, lexdays.DeadlineResult] | None = None
    day = RECESS_SCAN[0]
    while day <= RECESS_SCAN[1]:
        result = lexdays.compute(pack, day, act=act_id)
        if changed(result, "recess"):
            raw = next(s.after for s in result.trace if s.step == "count")
            distance = abs((raw - RECESS_TARGET).days)
            if best is None or distance < best[0]:
                best = (distance, result)
        day += timedelta(days=1)
    return best[1] if best else None


def trace_html(result: lexdays.DeadlineResult) -> str:
    items = []
    for step in result.trace:
        cite = f'<br><span class="cite">{e(step.citation.label["tr"])}</span>' if step.citation else ""
        cls = ' class="changed"' if step.changed else ""
        items.append(f"<li{cls}><span>{e(step.message['tr'])}</span>{cite}</li>")
    return '<ol class="trace">' + "".join(items) + "</ol>"


def example_html(title: str, intro: str, result: lexdays.DeadlineResult, pack: str, act_id: str) -> str:
    ends = f", saat {e(result.ends_at)}" if result.ends_at else ""
    link = f"../../?pack={pack}&amp;act={act_id}&amp;date={result.trigger.isoformat()}"
    return (
        f'<section class="ap-card"><h2>{e(title)}</h2><p>{e(intro)}</p>{trace_html(result)}'
        f'<p class="ap-last">Son gün: <strong>{e(long_date(result.deadline))}</strong>{ends}</p>'
        f'<p><a href="{link}">Bu örneği hesaplayıcıda aç</a></p></section>'
    )


def page_head(title: str, description: str, url: str, depth: str, extra: str = "") -> str:
    return f"""<!doctype html>
<!-- Generated by scripts/build-act-pages.py from the rule packs. Edit the data or the script and rerun it. -->
<html lang="tr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(title)}</title>
  <meta name="description" content="{e(description)}">
  <link rel="canonical" href="{url}">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{e(title)}">
  <meta property="og:description" content="{e(description)}">
  <meta property="og:url" content="{url}">
  <meta property="og:locale" content="tr_TR">
  <meta property="og:image" content="{BASE}assets/og.png">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="theme-color" content="#f7f9fc">
  <script>try {{ if (localStorage.getItem("lexdays-theme") === "dark") document.documentElement.dataset.theme = "dark"; }} catch {{}}</script>
  <link rel="manifest" href="{depth}manifest.webmanifest">
  <link rel="apple-touch-icon" href="{depth}assets/icon-180.png">
  <link rel="icon" href="{ICON}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
  <link rel="stylesheet" href="{depth}style.css">
{extra}</head>
<body>
  <header class="bar">
    <div class="wrap bar__row">
      <a class="brand" href="{depth}tr/">{MARK}<span>lexdays</span></a>
      <nav class="bar__nav" aria-label="Site">
        <a href="{depth}tr/">Hesapla</a>
        <a href="{depth}tr/sureler/">Tüm süreler</a>
        <a href="https://github.com/DoGood-Studio/legal-deadline-calculator">GitHub</a>
      </nav>
    </div>
  </header>
"""


FOOT = """  <footer class="foot">
    <div class="wrap foot__row">
      <p>Bilgilendirme amaçlıdır, hukuki danışmanlık değildir. Kanun, içtihat, mahkeme kararları ve yerel uygulama önceliklidir. Önemli bir süreyi mutlaka kontrol edin.</p>
      <p><a href="https://github.com/DoGood-Studio/legal-deadline-calculator">lexdays</a>, MIT lisansı. Bu sayfa kural paketlerinden otomatik üretilir; hesap örnekleri lexdays {version} ile yapıldı.</p>
    </div>
  </footer>
"""

def breadcrumbs(items: list[tuple[str, str]]) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": name, "item": url} for i, (name, url) in enumerate(items)
        ],
    }
    return f'  <script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>\n'


def act_page(pack: str, act_id: str, related: list[tuple[str, str, str]]) -> str:
    rp = lexdays.rulepack(pack)
    act = rp.act(act_id)
    abbr, pack_name, statute = PACKS[pack]
    label = act.label["tr"]
    cite = act.citation.label["tr"]
    period = period_text(act.period)
    url = f"{BASE}tr/sureler/{slug(pack, act_id)}/"
    h1 = f"{heading(label)} ({abbr})" if label in SHARED else heading(label)
    title = f"{heading(label)} ({cite}): {period} | lexdays"
    description = (
        f"{cite}: {period}. Başlangıç: {act.trigger['tr']}. Adli tatil ve resmî tatiller dahil son günü "
        "hesaplayın; kanun metni ve çözülmüş örneklerle."
    )
    crumbs = breadcrumbs([("lexdays", f"{BASE}tr/"), ("Süreler", f"{BASE}tr/sureler/"), (label, url)])
    quote, source = act.citation.quote, act.citation.url
    if not quote or not source:
        raise SystemExit(f"{pack} {act_id}: a page needs the quoted provision and its source URL")

    ordinary = ordinary_example(pack, act_id)
    recess = recess_example(pack, act_id)
    notices: dict[str, str] = {}
    if act.notice:
        notices["act"] = act.notice["tr"]
    for result in (ordinary, recess):
        for notice in result.notices if result else ():
            notices.setdefault(notice.code, notice.message["tr"])

    parts = [page_head(title, description, url, "../../../", crumbs), '  <main class="wrap ap">\n']
    parts.append(
        f'    <nav class="ap-crumbs" aria-label="Konum"><a href="../../">lexdays</a> › <a href="../">Süreler</a> › '
        f"<span>{e(abbr)}</span></nav>\n"
        f"    <h1>{e(h1)}</h1>\n"
        f'    <p class="ap-sub">{e(pack_name)} · {e(cite)}</p>\n'
        '    <section class="ap-card ap-facts">\n'
        f"      <dl><div><dt>Süre</dt><dd>{e(period)}</dd></div>"
        f"<div><dt>Ne zaman başlar</dt><dd>{e(act.trigger['tr'])}</dd></div>"
        f"<div><dt>Dayanak</dt><dd>{e(cite)}, {e(statute)}</dd></div></dl>\n"
        # A plain GET form: the calculator reads pack, act and date from the address.
        '      <form class="ap-calc" action="../../" method="get">'
        f'<input type="hidden" name="pack" value="{pack}"><input type="hidden" name="act" value="{act_id}">\n'
        '        <label for="ap-date">Tebliğ veya başlangıç tarihi</label>\n'
        '        <div class="ap-calc__row"><input type="date" id="ap-date" name="date">'
        '<button class="btn" type="submit">Son günü hesapla</button></div>\n'
        f'        <p class="ap-hint">Tarih seçmezseniz hesaplayıcı bugünle açılır. '
        f'<a href="../../?pack={pack}&amp;act={act_id}">Hesaplayıcıda aç</a></p>\n'
        "      </form>\n"
        "    </section>\n"
        '    <section class="ap-card">\n'
        "      <h2>Kanun metni</h2>\n"
        f'      <blockquote class="ap-quote">{e(quote["tr"])}</blockquote>\n'
        f'      <p class="ap-source">{e(cite)} · <a href="{e(source)}">Resmî metin (mevzuat.gov.tr)</a></p>\n'
        "    </section>\n"
    )
    parts.append(
        "    "
        + example_html(
            "Örnek hesap",
            f"Başlangıç tarihi {long_date(ordinary.trigger)} ise son gün şöyle bulunur:",
            ordinary,
            pack,
            act_id,
        )
        + "\n"
    )
    if recess:
        parts.append(
            "    "
            + example_html(
                "Süre tatile denk gelirse",
                f"Başlangıç tarihi {long_date(recess.trigger)} ise süre tatil içinde biter ve uzar:",
                recess,
                pack,
                act_id,
            )
            + "\n"
        )
    if notices:
        items = "".join(f"<li>{e(text)}</li>" for text in notices.values())
        parts.append(f'    <section class="ap-card"><h2>Dikkat edilecekler</h2><ul class="ap-notes">{items}</ul></section>\n')
    if related:
        links = "".join(
            f'<li><a href="../{s}/">{e(name)}</a> <span class="tag">{e(p)}</span></li>' for s, name, p in related
        )
        parts.append(
            f'    <section class="ap-card"><h2>İlgili süreler</h2><ul class="ap-related">{links}</ul>'
            f'<p><a href="../">{e(abbr)} ve diğer kanunlardaki tüm süreler</a></p></section>\n'
        )
    parts.append("  </main>\n" + FOOT.format(version=lexdays.__version__) + "</body>\n</html>\n")
    return "".join(parts)


def related_acts(pack: str, act_id: str) -> list[tuple[str, str, str]]:
    """Acts of the same group first, then the rest of the pack, at most eight."""
    rp = lexdays.rulepack(pack)
    act = rp.act(act_id)
    others = [rp.act(a) for a in rp.acts if a != act_id]
    same_group = [a for a in others if act.group and a.group == act.group]
    rest = [a for a in others if a not in same_group]
    return [(slug(pack, a.id), a.label["tr"], period_text(a.period)) for a in (same_group + rest)[:8]]


def list_page(packs: dict[str, list[str]]) -> str:
    total = sum(len(v) for v in packs.values())
    url = f"{BASE}tr/sureler/"
    title = f"Hukuki süreler listesi: HMK, İİK, CMK, İYUK, VUK ve AYM ({total} süre) | lexdays"
    description = (
        f"Türk hukukunda {total} işlemin süresi: istinaf, temyiz, cevap dilekçesi, ödeme emrine itiraz, "
        "dava açma ve diğerleri. Her biri kanun metniyle; son günü adli tatil dahil hesaplayın."
    )
    crumbs = breadcrumbs([("lexdays", f"{BASE}tr/"), ("Süreler", url)])
    parts = [page_head(title, description, url, "../../", crumbs), '  <main class="wrap ap">\n']
    parts.append(
        '    <nav class="ap-crumbs" aria-label="Konum"><a href="../">lexdays</a> › <span>Süreler</span></nav>\n'
        "    <h1>Türk hukukunda süreler</h1>\n"
        f'    <p class="ap-sub">{total} işlem: süresi, başlangıcı ve dayandığı madde. Bir işlemi seçin; kanun metnini, '
        'çözülmüş örnekleri ve son gün hesaplayıcısını görün.</p>\n'
    )
    for pack, act_ids in packs.items():
        abbr, pack_name, statute = PACKS[pack]
        rp = lexdays.rulepack(pack)
        rows = []
        for act_id in act_ids:
            act = rp.act(act_id)
            rows.append(
                f'<tr><td><a href="{slug(pack, act_id)}/">{e(act.label["tr"])}</a></td>'
                f"<td>{e(period_text(act.period))}</td><td>{e(act.citation.label['tr'])}</td></tr>"
            )
        parts.append(
            f'    <section class="ap-card" id="{pack.split("/")[1]}"><h2>{e(pack_name)} <span class="tag">{e(abbr)}</span></h2>'
            f'<p class="ap-hint">{e(statute)}</p><div class="ap-table"><table><thead><tr><th>İşlem</th><th>Süre</th>'
            f"<th>Dayanak</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div></section>\n"
        )
    parts.append("  </main>\n" + FOOT.format(version=lexdays.__version__) + "</body>\n</html>\n")
    return "".join(parts)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def main() -> None:
    packs = {pack: list(lexdays.rulepack(pack).acts) for pack in PACKS}
    SHARED.update(shared_labels())
    if OUT.exists():
        shutil.rmtree(OUT)
    for pack, act_ids in packs.items():
        for act_id in act_ids:
            write(OUT / slug(pack, act_id) / "index.html", act_page(pack, act_id, related_acts(pack, act_id)))
    write(OUT / "index.html", list_page(packs))
    print(f"wrote {sum(len(v) for v in packs.values())} act pages and the list in {OUT.relative_to(SITE.parent)}")


if __name__ == "__main__":
    main()
