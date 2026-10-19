# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

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

[Unreleased]: https://github.com/DoGood-Studio/legal-deadline-calculator/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/DoGood-Studio/legal-deadline-calculator/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/DoGood-Studio/legal-deadline-calculator/releases/tag/v0.1.0
