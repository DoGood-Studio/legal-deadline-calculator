"""The source watcher (scripts/watch_sources.py) without network access.

The network calls are replaced by canned pages, so these tests check what the watcher makes of
a page: whether a quote is still there, which Resmî Gazete items it reports, and how a report
and the accepted state follow each other.
"""

from __future__ import annotations

import http.client
import importlib.util
import json
import sys
import urllib.error
from datetime import date
from types import ModuleType

import pytest

from .conftest import REPO


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("watch_sources", REPO / "scripts" / "watch_sources.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses look their module up while the class is built
    spec.loader.exec_module(module)
    return module


ws = _load()

ARTICLE = (
    "Adlî tatil MADDE 102- (1) Adlî tatil her yıl yirmi Temmuz gününden başlar ve otuzbir Ağustos "
    "gününe kadar devam eder. (2) Adlî yılın sona ermesinden önce, mahkemeler hangi davalara adlî "
    "tatil içinde bakılacağını belirler."
)
QUOTE = (
    "m.102: (1) Adli tatil her yıl yirmi Temmuz gününden başlar ve otuzbir Ağustos gününe kadar "
    "devam eder. … (2) Adli yılın sona ermesinden önce, mahkemeler hangi davalara adli tatil "
    "içinde bakılacağını belirler."
)


def test_compact_ignores_case_accents_and_layout() -> None:
    assert ws.compact("Adlî  tatil,\nİCRA") == ws.compact("ADLİ TATİL icra") == "adlitatilicra"


def test_fold_keeps_positions() -> None:
    text = "İCRA VE İFLAS Hâkimler Yargılama"
    assert ws.fold(text) == "icra ve iflas hakimler yargilama"
    assert len(ws.fold(text)) == len(text)


def test_quote_is_found_across_layout_labels_and_ellipsis() -> None:
    assert ws.quote_share_found(QUOTE, ws.compact(ARTICLE)) == 1.0


def test_one_changed_word_lowers_the_share() -> None:
    amended = ARTICLE.replace("yirmi Temmuz", "on beş Temmuz")
    share = ws.quote_share_found(QUOTE, ws.compact(amended))
    assert 0 < share < 1.0
    result = ws.Result(ws.Source("https://example.test"), "ok", "f", [("tr/hmk hmk_102 [tr]", share)])
    assert ws.quotes_to_report(result, {}) == ([] if share >= ws.QUOTE_THRESHOLD else result.quote_shares)
    assert ws.quotes_to_report(result, {"quotes": {"tr/hmk hmk_102 [tr]": 1.0}}) == result.quote_shares


def test_fingerprint_ignores_the_date_of_the_visit() -> None:
    page = "Sächsisches Sonn- und Feiertagsgesetz Aktuelle Fassung Stand vom\n{}\n§ 1 Gesetzliche Feiertage"
    assert ws.fingerprint(page.format("19.10.2026")) == ws.fingerprint(page.format("20.10.2026"))
    assert ws.fingerprint(page.format("20.10.2026")) != ws.fingerprint(page.format("20.10.2026") + " § 2")


def test_html_text_drops_scripts_and_tags() -> None:
    markup = "<html><script>var x = 1;</script><p>Adl&icirc; tatil</p><!-- note --></html>"
    assert ws.html_text(markup).split() == ["Adlî", "tatil"]


def test_decode_uses_the_declared_charset() -> None:
    page = '<meta http-equiv="Content-Type" content="text/html; charset=windows-1254">Yargılama'
    assert ws.decode(page.encode("cp1254")).endswith("Yargılama")
    assert ws.decode("Yargılama".encode("cp1254"), "text/html; charset=windows-1254") == "Yargılama"
    assert ws.decode("Yargılama".encode()) == "Yargılama"


def _fake_fetch(pages: dict[str, tuple[bytes, str]], fetched: list[str]):  # type: ignore[no-untyped-def]
    def fetch(url: str, timeout: int = 60) -> tuple[bytes, str]:
        fetched.append(url)
        if url not in pages:
            raise urllib.error.URLError("not in the test")
        return pages[url]

    return fetch


def test_read_source_reports_quote_shares_and_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    page = (f"<html><body><p>{ARTICLE}</p>" + "<p>Diğer hükümler.</p>" * 40 + "</body></html>").encode()
    fetched: list[str] = []
    pages = {"https://law.test": (page, "text/html; charset=utf-8")}
    monkeypatch.setattr(ws, "fetch", _fake_fetch(pages, fetched))
    src = ws.Source("https://law.test", {"tr/hmk (hmk_102)"}, [("tr/hmk hmk_102 [tr]", QUOTE)])
    result = ws.read_source(src)
    assert result.status == "ok"
    assert result.quote_shares == [("tr/hmk hmk_102 [tr]", 1.0)]
    assert result.fingerprint == ws.fingerprint(ws.html_text(page.decode()))

    gone = ws.read_source(ws.Source("https://gone.test"))
    assert gone.status.startswith("not reachable")
    assert fetched.count("https://gone.test") == 2  # one retry

    def not_found(url: str, timeout: int = 60) -> tuple[bytes, str]:
        raise urllib.error.HTTPError(url, 404, "Not Found", None, None)  # type: ignore[arg-type]

    monkeypatch.setattr(ws, "fetch", not_found)
    assert ws.read_source(ws.Source("https://law.test")).status == "HTTP 404"

    def dropped(url: str, timeout: int = 60) -> tuple[bytes, str]:
        raise http.client.IncompleteRead(b"partial")

    monkeypatch.setattr(ws, "fetch", dropped)
    assert ws.read_source(ws.Source("https://law.test")).status == "not reachable (IncompleteRead)"

    monkeypatch.setattr(ws, "fetch", lambda url, timeout=60: (b"<p>Needs a browser.</p>", "text/html"))
    assert ws.read_source(ws.Source("https://law.test")).status.startswith("no readable text")


def test_eu_acts_are_found_by_eli_or_celex() -> None:
    assert ws.eu_act("http://data.europa.eu/eli/C/2026/1114/oj") == (
        "resource_legal_eli", "http://data.europa.eu/eli/C/2026/1114/oj")
    assert ws.eu_act("https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32012Q0929(01)") == (
        "resource_legal_id_celex", "32012Q0929(01)")
    assert ws.eu_act("https://www.gov.uk/bank-holidays") is None
    assert ws.eu_act('http://data.europa.eu/eli/x"} DROP') is None  # nothing that could break the query


def test_eu_acts_are_read_from_cellar_with_their_amendments(monkeypatch: pytest.MonkeyPatch) -> None:
    cellar = "http://publications.europa.eu/resource/cellar/938687cb.0006"
    queries: list[str] = []

    def sparql(query: str) -> list[dict]:
        queries.append(query)
        if "manifestation_type" in query:
            return [{"man": {"value": f"{cellar}.01"}, "type": {"value": "pdfa1a"}},
                    {"man": {"value": f"{cellar}.04"}, "type": {"value": "xhtml"}}]
        return [{"date": {"value": "2026-06-02"}, "celex": {"value": "32026Q01335"}},
                {"date": {"value": "2024-07-02"}, "celex": {"value": "32024Q02094"}}]

    page = (f"<p>{ARTICLE}</p>" * 5).encode()
    fetched: list[str] = []
    monkeypatch.setattr(ws, "sparql", sparql)
    pages = {f"https{cellar[4:]}.04/DOC_1": (page, "application/xhtml+xml")}
    monkeypatch.setattr(ws, "fetch", _fake_fetch(pages, fetched))
    result = ws.read_source(ws.Source("https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32012Q0929(01)"))
    assert result.status == "ok"
    assert result.amended_by == [("2026-06-02", "32026Q01335"), ("2024-07-02", "32024Q02094")]
    assert all('STR(?id) = "32012Q0929(01)"' in query for query in queries)

    run = {"cj_lists": [], "cj_error": None, "gazette": [], "today": date(2026, 10, 20)}
    report, findings = ws.render([result], {}, **run)
    assert findings == 2
    assert "  - 2026-06-02: CELEX 32026Q01335" in report
    state = ws.accept([result], {}, [], date(2026, 10, 20))
    assert state["sources"][result.source.url]["amended_until"] == "2026-06-02"
    assert ws.render([result], state, **run)[1] == 0


def test_gazette_follows_extra_issues_and_reads_laws(monkeypatch: pytest.MonkeyPatch) -> None:
    base = "https://www.resmigazete.gov.tr/eskiler/2023/02/"
    index = (
        '<meta http-equiv="Content-Type" content="text/html; charset=windows-1254">'
        "YÖNETMELİKLER"
        '<a href="20230211-1.htm">–– Su Ürünleri Üretiminde Kiralama Yönetmeliği</a>'
        '<a href="20230211-2.htm">–– 7999 Bazı Kanunlarda Değişiklik Yapılmasına Dair Kanun</a>'
        '<a href="20230211-3.htm">–– 8000 Bir Anlaşmanın Onaylanmasının Uygun Bulunduğuna Dair Kanun</a>'
        '<a href="http://www.resmigazete.gov.tr/eskiler/2023/02/20230211M1.htm">mükerrer</a>'
    )
    extra = (
        '<meta charset="windows-1254"><a href="20230211M1-1.pdf">–– Olağanüstü Hal Kapsamında Yargı '
        "Alanında Alınan Tedbirlere İlişkin Cumhurbaşkanlığı Kararnamesi (Kararname Numarası: 120)</a>"
    )
    pages = {
        base + "20230211.htm": (index.encode("cp1254"), "text/html"),
        base + "20230211M1.htm": (extra.encode("cp1254"), "text/html"),
        base + "20230211-2.htm": ("<p>İcra ve İflas Kanununun 89. maddesi</p>".encode(), "text/html"),
        base + "20230211-3.htm": ("<p>Anlaşma onaylanmıştır.</p>".encode(), "text/html"),
    }
    fetched: list[str] = []
    monkeypatch.setattr(ws, "fetch", _fake_fetch(pages, fetched))
    hits = ws.gazette_hits(date(2023, 2, 11), days=1)
    assert [(link.rsplit("/", 1)[1], title) for _, link, title in hits] == [
        ("20230211-2.htm", "7999 Bazı Kanunlarda Değişiklik Yapılmasına Dair Kanun "
                           "(the text mentions “İcra ve İflas”)"),
        ("20230211M1-1.pdf", "Olağanüstü Hal Kapsamında Yargı Alanında Alınan Tedbirlere İlişkin "
                             "Cumhurbaşkanlığı Kararnamesi (Kararname Numarası: 120)"),
    ]
    assert base + "20230211-1.htm" not in fetched  # a regulation title is enough; only acts are read


def test_every_cited_source_is_watched() -> None:
    expected, quotes, unlinked = set(), 0, 0
    for path in (REPO / "data" / "rulepacks").rglob("*.json"):
        for cite in json.loads(path.read_text(encoding="utf-8")).get("citations", {}).values():
            if cite.get("url"):
                expected.add(cite["url"])
                quotes += len(cite.get("quote") or {})
            else:
                unlinked += 1
    for path in (REPO / "data" / "calendars").glob("*.json"):
        expected |= {s["url"] for s in json.loads(path.read_text(encoding="utf-8")).get("sources", [])}
    sources = ws.collect_sources(REPO)
    assert set(sources) == expected
    assert sum(len(s.quotes) for s in sources.values()) == quotes
    assert len(ws.unlinked_citations(REPO)) == unlinked


def _result(url: str, status: str = "ok", fp: str = "abc", share: float | None = None):  # type: ignore[no-untyped-def]
    shares = [] if share is None else [("tr/hmk hmk_102 [tr]", share)]
    src = ws.Source(url, {"tr/hmk (hmk_102)"}, [(where, QUOTE) for where, _ in shares])
    return ws.Result(src, status, fp if status == "ok" else None, shares)


def test_report_and_accepted_state_follow_each_other() -> None:
    today = date(2026, 10, 20)
    ok, down = _result("https://a.test", share=0.82), _result("https://b.test", status="no readable text")
    run = {"cj_lists": [("2026-02-18", "List")], "cj_error": None, "gazette": [], "today": today,
           "unlinked": ["tr/hmk (hgk_2017): Court of Cassation"]}

    report, findings = ws.render([ok, down], {}, **run)
    assert report.startswith("**Özet:**")
    assert "https://b.test" in report
    assert "tr/hmk (hgk_2017): Court of Cassation: court decision without a link" in report
    assert findings == 1  # 82% is above the threshold for a new quote; the hand check is due

    state = ws.accept([ok, down], {}, run["cj_lists"], today)
    assert state == {
        "sources": {"https://a.test": {"fingerprint": "abc"}},
        "quotes": {"tr/hmk hmk_102 [tr]": 0.82},
        "cj_latest_list": "2026-02-18",
        "manual_review": "2026-10-20",
    }
    assert ws.render([ok, down], state, **run)[1] == 0

    worse = _result("https://a.test", fp="def", share=0.78)
    report, findings = ws.render([worse, down], state, **run)
    assert findings == 2  # the quote dropped below its accepted share, and the page changed
    assert "78% of the quote found (accepted: 82%)" in report

    state["sources"]["https://a.test"]["volatile"] = True
    assert ws.render([_result("https://a.test", fp="xyz", share=0.82), down], state, **run)[1] == 0

    lost = _result("https://a.test", status="HTTP 404")
    report, findings = ws.render([lost, down], state, **run)
    assert findings == 1
    assert "(readable before)" in report
    # some sites refuse cloud servers such as CI; that is a hand check, not a lost source
    assert ws.render([_result("https://a.test", status="HTTP 403"), down], state, **run)[1] == 0

    lists = [("2027-02-10", "New list"), ("2026-02-18", "List")]
    later = {**run, "today": date(2027, 1, 20), "cj_lists": lists}
    report, findings = ws.render([ok, down], state, **later)
    assert "- 2027-02-10: New list" in report
    assert findings == 2  # the new list, and three months since the last hand check


def test_eurlex_failure_is_a_finding() -> None:
    run = {"cj_lists": None, "cj_error": "URLError: down", "gazette": [], "today": date(2026, 10, 20)}
    accepted = {"sources": {"https://a.test": {"fingerprint": "abc"}}}
    report, findings = ws.render([_result("https://a.test")], accepted, **run)
    assert findings == 1
    assert "EUR-Lex query failed (URLError: down)" in report
