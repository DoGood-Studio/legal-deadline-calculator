<h1 align="center">lexdays</h1>

<p align="center">
  <b>Explainable legal deadlines and business days.</b><br>
  Every result tells you <i>why</i>, and cites the rule it applied.
</p>

<p align="center">
  <a href="https://github.com/DoGood-Studio/lexdays/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/DoGood-Studio/lexdays/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://pypi.org/project/lexdays/"><img alt="PyPI" src="https://img.shields.io/pypi/v/lexdays"></a>
  <a href="https://www.npmjs.com/package/lexdays"><img alt="npm" src="https://img.shields.io/npm/v/lexdays"></a>
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-blue"></a>
  <a href="https://scorecard.dev/viewer/?uri=github.com/DoGood-Studio/lexdays"><img alt="OpenSSF Scorecard" src="https://api.scorecard.dev/projects/github.com/DoGood-Studio/lexdays/badge"></a>
</p>

<p align="center">
  Python · TypeScript · CLI · zero runtime dependencies<br>
  <a href="README.tr.md">Türkçe</a> ·
  <a href="https://dogood-studio.github.io/lexdays/">Live demo</a> ·
  <a href="docs/rulepacks.md">Write a rule pack</a> ·
  <a href="docs/RELIABILITY.md">Reliability report</a>
</p>

---

Holiday libraries tell you **which days are holidays**. Lawyers, legal-tech teams and anyone who files, pays or serves on time need something else: **the last day to act, and the reason for it.**

```python
>>> import lexdays
>>> r = lexdays.compute("tr/hmk", "2026-07-30", "P2W")   # Turkish civil procedure, 2 weeks from service
>>> r.deadline
datetime.date(2026, 9, 8)
>>> print(r.explain("en"))
1. 2 week(s) from 2026-07-30 (Thursday) end on the same weekday of the last week: 2026-08-13 (Thursday). [HMK Art. 92]
2. 2026-08-13 (Thursday) falls within the judicial recess (2026-07-20 (Monday) – 2026-08-31 (Monday)); the period is extended by 7 day(s) counted from 2026-09-01 (Tuesday), the day after the recess ends: 2026-09-08 (Tuesday). [HMK Arts. 102 and 104]
3. 2026-09-08 (Tuesday) is a working day; no adjustment needed. [HMK Art. 93]
4. On the last day the period ends at 23:59. [HMK Art. 445/4]
Deadline: 2026-09-08 (Tuesday)
Ends at: 23:59 (Europe/Istanbul)
```

## Why lexdays

- **Real deadline rules, not just holidays.** Judicial recesses that extend or suspend periods, half-day feast eves, deemed service of electronic notifications, add-on days for service by mail, counting backwards from a hearing, "clear days", month-end clamping, last-day roll-forward. Each one is modelled with its own rules.
- **Explainable and citable.** Each step of the calculation is recorded with the article or decision it comes from, so a result can be checked and audited. The explanation is available in 12 languages (English, Turkish, German, French, Spanish, Italian, Portuguese, Dutch, Russian, Arabic, Chinese and Japanese); rule notes and citation labels are written in English and, where relevant, the court's own language.
- **Honest about uncertainty.** Where courts or practitioners disagree (e.g. 7 or 8 September after the Turkish judicial recess), the point becomes an **option** and the result carries a **notice**. The default follows settled high-court case law; where there is none, it is the earlier, safer date.
- **Refuses to guess.** Asking for a year outside a calendar's verified data raises `CoverageError` instead of silently returning a wrong date.
- **One engine, two languages, identical answers.** Python and TypeScript share the same data and test vectors, and 1,800 random cases must give byte-identical results in both.
- **Rules as data.** Jurisdictions are JSON rule packs validated by a JSON Schema. Adding one needs no engine code ([guide](docs/rulepacks.md)).

## Install

```bash
pip install lexdays          # Python 3.10+
npm install lexdays          # Node 18+, browsers, Deno, Bun (ESM and CommonJS, typed)
```

## Quick start

### Python

```python
import lexdays

# US federal court: 30 days after service by mail (FRCP 6(a) and 6(d))
lexdays.compute("us/frcp", "2025-07-31", "P30D", options={"service": "mail"}).deadline
# datetime.date(2025, 9, 5)

# Counting backwards: serve at least 3 clear days before a hearing (CPR 2.8)
lexdays.compute("gb-eaw/cpr", "2025-10-20", "P3D", direction="before").deadline
# datetime.date(2025, 10, 14)

# German court deadline: holidays at the court's seat apply (§ 222 ZPO)
lexdays.compute("de/zpo", "2025-07-15", "P1M", calendar="de-by-catholic").deadline
# datetime.date(2025, 8, 18)   (15 August is a holiday in Munich, not in Karlsruhe)

# Business days
cal = lexdays.calendar("tr")
cal.add_business_days("2026-05-22", 3)        # skips the Feast of Sacrifice
cal.is_business_day("2026-05-26")             # True: a half-day eve counts as working by default
cal.is_business_day("2026-05-26", half_days="non_working")   # False
```

### TypeScript / JavaScript

```ts
import { compute, calendar } from "lexdays";

const r = compute("eu/cj", "2025-03-14", "P2M", { options: { start: "oj_publication" } });
r.deadline;          // "2025-06-10"
r.explain("en");     // numbered explanation with citations
r.toJSON();          // same document as Python's to_dict()

calendar("gb-eaw").addBusinessDays("2025-12-24", 1);   // "2025-12-29"
calendar("us").holidays(2026).map((h) => h.date);
```

Dates are plain `YYYY-MM-DD` strings in TypeScript. JavaScript `Date` objects are rejected on purpose, because which calendar day a moment belongs to depends on a time zone.

### Command line

```bash
lexdays deadline tr/hmk 2026-07-30 P2W --lang tr
lexdays deadline us/frcp 2025-09-15 P14D --before --json
lexdays holidays de-by 2026
lexdays add tr 2026-05-22 3
lexdays list
```

Periods can be written `P10D`, `P2W`, `P1M`, `P1Y`, `10d`, `5bd` (business days), `2 weeks` or `10 gün`.

## Jurisdictions

| Rule pack | Covers | Default calendar |
|---|---|---|
| `tr/hmk` | Türkiye: civil procedure (HMK 92–93, 102–104, 445) | `tr` |
| `tr/iik` | Türkiye: enforcement and bankruptcy (İİK 19, 8/a) | `tr` |
| `tr/cmk` | Türkiye: criminal procedure (CMK 39, 331) | `tr` |
| `tr/iyuk` | Türkiye: administrative and tax courts (İYUK 8, 61) | `tr` |
| `tr/vuk` | Türkiye: tax procedure (VUK 18, 107/A) | `tr` |
| `tr/aym` | Türkiye: individual application to the Constitutional Court | `tr` |
| `us/frcp` | US federal civil procedure (FRCP 6(a), 6(d)); state holidays via `calendar="us-<state>"` | `us` |
| `gb-eaw/cpr` | England and Wales Civil Procedure Rules (CPR 2.8, 6.26) | `gb-eaw` |
| `eu/cj` | EU Court of Justice and General Court time limits (RP 49–51) | `eu-cj` |
| `de/zpo` | German civil procedure (§ 222 ZPO, §§ 187–188 BGB); court seat via `calendar="de-<Land>"` | `de` |

**Calendars:** `tr` (2000–2035, Diyanet feast dates), `us`, `us-ma`, `gb-eaw` (2019–2028, GOV.UK), `eu-cj` (2025–2026), `de` and all 16 Länder (`de-bw` … `de-th`, plus `de-by-catholic` and `de-by-augsburg`).

Every pack is marked `beta`: researched from the statute text and case law, with tests taken from court decisions and official examples, but not yet reviewed by practising lawyers in each jurisdiction. Reviews are very welcome.

## How it works

A rule pack is an ordered list of steps. Each step can be conditional on the options, the period or the dates, and can cite its legal source:

```jsonc
// excerpt of data/rulepacks/tr/hmk.json
{ "type": "shift_trigger", "days": 5, "cite": "tk_7a",
  "when": { "option": "service", "equals": "e_notification_delivery" } },
{ "type": "count", "cite": "hmk_92" },
{ "type": "recess", "cite": "hmk_104", "name": { "en": "judicial recess", "tr": "adli tatil" },
  "periods": [ { "start": "07-20", "end": "08-31", "since": 2012 } ],
  "mode": "extend", "extension_days": 7, "count_from": { "$option": "recess_extension_from" } },
{ "type": "roll", "cite": "hmk_93" }
```

The engine runs the matching steps and records each one in the trace. Calendars use the same approach: fixed dates, nth weekdays, Easter offsets, explicit dates (e.g. lunar feasts), substitute days, half days, holiday kinds and inheritance (`de-by-catholic` extends `de-by`, which extends `de`).

## Reliability

Details are in [docs/RELIABILITY.md](docs/RELIABILITY.md). In short:

- **290 hand-checked test vectors.** Dozens are taken from court decisions (Turkish Court of Cassation, Council of State and Constitutional Court) and from official worked examples (FRCP 2009 Advisory Committee Note, CPR 2.8, CJEU C-660/17 P).
- **Property-based tests** (Hypothesis, fast-check) check invariants across thousands of random inputs. Examples: a later trigger never gives an earlier deadline, and rolling packs never end on a non-working day. These tests have already caught a real bug.
- **Differential testing:** 1,800 random computations must produce byte-identical result documents in Python and TypeScript.
- **Independent cross-checks:** calendars are compared weekly with python-holidays and the GOV.UK feed. There are currently no differences across 22 calendars.
- **97% test coverage**, strict typing (mypy strict and TypeScript strict), CI on Linux, Windows and macOS with Python 3.10–3.14 and Node 18–24, CodeQL and OpenSSF Scorecard.

## Compared with holiday libraries

| | lexdays | python-holidays | date-holidays | workalendar |
|---|---|---|---|---|
| Countries covered | 5 jurisdictions | 250 | 200+ | many (no release since 2023) |
| Legal deadline rules | yes | – | – | – |
| Explanation with citations | yes | – | – | – |
| Business-day arithmetic | yes | partial | – | yes |
| Half days with clock time | yes | tag only | yes | – |
| Refuses years without verified data | yes | – | – | – |
| Python and TypeScript | both, identical | Python | JS | Python |

If you only need a holiday list for many countries, python-holidays and date-holidays cover far more countries. lexdays is for when the **deadline** matters.

## Contributing

New jurisdictions, corrections and reviews by lawyers are the most valuable contributions. A rule pack is a JSON file plus test vectors with sources. See [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/rulepacks.md](docs/rulepacks.md).

## Disclaimer

lexdays is an informational tool and does not give legal advice. Statutes, case law, court orders and local practice take precedence. Always check a deadline that matters.

## License

[MIT](LICENSE)
