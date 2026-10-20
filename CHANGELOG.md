# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Demo: a page for each of the 90 Turkish acts (`/tr/sureler/<pack>-<act>/`) and a list of all of them, generated from the rule packs by `scripts/build-act-pages.py`: the period and its start, the provision quoted verbatim, two worked examples computed by the engine (one ending in a recess where the pack has one), the act's notices, related acts and a form that opens the calculator with the act and a date. The pages are in the sitemap and CI checks that they match the data.

### Fixed

- Demo and act pages: notes and setting hints no longer show the library's setting names (`judicial_recess='exempt'`, `'day_after_end'`); they quote the form's own question and answer in the page's language. The library's explanations keep the exact names for developers.
- Demo: the footer's "MIT license" was in Turkish on every language page; it is now translated into all 12 languages.
- Demo, address-bar search and bookmark button: dates written with a month name ("20 Mayıs 2026", "March 20, 2026", "20. März 2026", in all 12 languages) were not read, and the number was taken as a period ("20 m…" became 20 months). They are now read as dates; a one-letter unit counts only on its own, a bare number is a period only at the end of the text, and "20.10.26" is read with a two-digit year. "05/06/2026" on the English page follows the browser's locale: 5 June for en-GB, May 6 for en-US.
- Demo, offline use: the service worker kept every address with its query, and offline it served the oldest copy of a page, which could pair an old page with newer scripts and stop the calculator; pages are now stored once, without the query, and always revalidated with the server. A page never opened on the device shows a short offline notice instead of a broken page, and only lexdays' own caches are cleared on update.
- Demo, accessibility: single-key shortcuts can be turned off in the shortcuts dialog (WCAG 2.1.4), and the start date, the business-day calendar and its start date now have accessible names.

## [0.2.0] - 2026-10-20

### Added

- Acts: a rule pack can name procedural acts (an appeal, a reply, an objection to a payment order) with the period, direction and options each one implies and the citation that fixes it. `compute(pack, trigger, act="istinaf")` (TypeScript: `compute(pack, trigger, null, { act: "istinaf" })`) needs only the date. `RulePack.acts`, `RulePack.act(id)`, and `DeadlineResult.act` with the citation in force; `explain()` names the act. An act can keep earlier versions of its period by trigger date (`earlier`) and carry a notice. Passing an option or direction the act contradicts is an error. Command line: `lexdays deadline PACK DATE --act NAME` and `lexdays acts [PACK]`.
- Catalogue of 103 acts, each quoting its provision verbatim, with a hand-derived test vector:
  - Türkiye, 90: HMK 22, İİK 32, CMK 10, İYUK 15, VUK 9, Law 6216 2. Two independent readings of the official texts agreed on the article and period of every one; notices cover the 2024 changes of Law 7499 (which apply to decisions given from 1 June 2024), starts the statute leaves open, and the fiscal recess. Where the statute does not say whether the judicial recess or the summer break extends a period, the act takes the earlier date and says so.
  - United States (FRCP 12, 59 and 6(c)), England and Wales (CPR 10.3, 15.4 and 23.7), EU (TFEU 263, Statute Art. 56) and Germany (§§ 517, 520, 339 and 548 ZPO): the demo's former presets, now with citations.
- Demo: a "What do you need to do?" search over all acts, ignoring case and accents, with `/` as a shortcut. Picking an act fills in the pack, period, direction and options; the result shows the act with the wording of its provision and the other deadlines that run from the same event. Act chips replace the presets.
- Demo: the page opens in a lighter look, with a switch for a dark theme that the browser remembers.
- Results carry the version of lexdays that computed them: `to_dict()["version"]` in Python, `toJSON().version` in TypeScript.
- Demo page: works offline and can be installed as an app; single-key shortcuts (`?` lists them); an address-bar search and a bookmark button that open the calculator with a date and period taken from free text (`?q=20.10.2026 2 weeks`); copied results and calendar entries name the lexdays version.
- Releases: the built packages are signed with Sigstore and attached, with their signatures, to the GitHub release.
- CI: a weekly source watch (`scripts/watch_sources.py`, workflow `Source watch`). It reads every source the rule packs and calendars cite, checks that the quoted rule text is still there (for Constitutional Court decisions through the court's public decision search), lists new acts amending a cited EU act, asks EUR-Lex for a new Court of Justice holiday list and scans the Resmî Gazete for laws, decrees and holiday decisions that touch the Turkish packs. Findings open or update an issue labelled `source-watch`; the watcher never changes data.

### Changed

- `compute()`: `period` is optional when `act` is given, and `direction` defaults to the act's direction (otherwise `after`). `DeadlineResult.to_dict()` has a new `act` key (`null` without an act).

### Fixed

- Demo presets that gave a wrong or incomplete answer:
  - CPR 15.4 offered only the 28 days that apply after an acknowledgment of service; the 14 days without one are now a separate act.
  - FRCP 12(a)(1)(A)(i) and 59(b) added Rule 6(d)'s 3 days when mail service was chosen; the acts now fix the service option.
  - § 339 ZPO did not mention the one month for service abroad; the act carries a notice.

## [0.1.1] - 2026-10-20

### Fixed

- `eu/cj`: deadlines reaching 2027 no longer fail. The `eu-cj` calendar now covers the Court's list C/2026/1114 up to 31 October 2027; later dates still raise `CoverageError`.
- `tr/*`: periods that touch the 2020 suspension (Law No. 7226 and Presidential Decision No. 2480) or the 2023 earthquake suspension (Presidential Decree No. 120) now carry a notice; the calculation itself does not apply the suspension.

### Added

- Calendars: `coverage.until` ends verified data on a given day.
- Rule packs: the notice and step conditions `date_from` and `date_before` compare the computed date with absolute dates.
- CI: `scripts/check_coverage.py` fails when a calendar's verified data ends within six months.

## [0.1.0] - 2026-10-19

First public release.

### Added

- Jurisdiction-agnostic deadline engine driven by JSON rule packs. Steps: deemed service, counting (days, weeks, months, years, business days, clear days), judicial recess (extend, suspend, defer start), roll to a working day, add-on days, end time and notices. Each executed step is recorded in an explanation trace with its citation, rendered in 12 languages (English, Turkish, German, French, Spanish, Italian, Portuguese, Dutch, Russian, Arabic, Chinese and Japanese).
- Holiday calendars as data: fixed dates, nth weekdays, Easter offsets (Western and Orthodox), explicit dates, weekday-relative dates, observed and substitute days, half days with a clock time, holiday kinds, inheritance, and explicit coverage years. Queries outside the coverage raise `CoverageError`.
- Business-day functions: `is_business_day`, `add_business_days`, `business_days_between`, `next_business_day`, `previous_business_day`, `holidays`.
- Rule packs: `tr/hmk`, `tr/iik`, `tr/cmk`, `tr/iyuk`, `tr/vuk`, `tr/aym`, `us/frcp`, `gb-eaw/cpr`, `eu/cj`, `de/zpo`.
- Calendars: `tr` (2000–2035), `us`, `us-ma`, `gb-eaw` (2019–2028), `eu-cj` (2025–2026), `de` and all 16 Länder, `de-by-catholic`, `de-by-augsburg`.
- Python package with a command-line interface, and a typed TypeScript package (ESM and CommonJS) with identical behaviour.
- JSON Schemas for calendars and rule packs.
- Demo page on GitHub Pages with a deadline calculator and a business-day tool, in the same 12 languages, including a right-to-left layout for Arabic. Shareable links keep the language and every input. An "Add to calendar" menu saves the last day as an iCalendar file with reminders three days and one day before, or opens it in Google Calendar.
- Shared conformance vectors, property-based tests, a Python/TypeScript differential test, and calendar cross-checks against python-holidays and the GOV.UK bank holidays feed.
- A pre-release verification report (docs/verification.md): every rule pack checked against primary sources, 41 new test vectors, translations reviewed in all languages, and the demo tested in Chromium, Firefox and WebKit.

[Unreleased]: https://github.com/DoGood-Studio/legal-deadline-calculator/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/DoGood-Studio/legal-deadline-calculator/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/DoGood-Studio/legal-deadline-calculator/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/DoGood-Studio/legal-deadline-calculator/releases/tag/v0.1.0
