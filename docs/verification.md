# Verification report

Pre-release audit of every rule pack, calendar, translation, the demo page and the release pipeline, completed on 19 October 2026. It records what was checked against which source, what was wrong, how it was fixed, and what still needs a lawyer.

This is not legal advice and not a substitute for review by a practitioner in each jurisdiction.

## Method

- **Rules.** Every step, option default, notice and citation of each rule pack was compared with the primary source: statute texts (mevzuat.gov.tr, justice.gov.uk, law.cornell.edu, eur-lex.europa.eu, curia.europa.eu, gesetze-bayern.de, revosax.sachsen.de) and court decisions. Each existing test vector was recomputed by hand. New vectors were written for gaps, each with a verifiable source.
- **Where official sources were unreachable**, decisions were read through secondary copies, and this is noted below. Unreachable sites included Yargıtay and Danıştay search, and gesetze-im-internet.de (the buzer.de mirror was used instead).
- **Translations.** All ten translated languages were reviewed for legal terminology, grammar with one-unit periods, register, and placeholders.
- **Automated checks.**
  - Test suites in Python and TypeScript.
  - The Python/TypeScript differential test.
  - Calendar cross-check against python-holidays: 0 differences.
  - The demo page in Chromium, Firefox and WebKit, in 12 languages, at desktop and phone widths.
  - A release rehearsal: `twine check --strict`, a clean wheel install, `publint`, `@arethetypeswrong/cli`, `actionlint`, existence of every pinned action commit, and the demo served under `/lexdays/` as on GitHub Pages.

## Results

| Pack | Critical | Major | Minor | Vectors added |
|---|---|---|---|---|
| `tr/iyuk` | 1 | 1 | 4 | 4 |
| `tr/hmk` (and `tr/iik`) | 0 | 2 | 6 | 5 |
| `tr/cmk`, `tr/vuk`, `tr/aym` | 0 | 1 | 7 | 4 |
| `gb-eaw/cpr` | 1 | 5 | 3 | 6 |
| `us/frcp` | 0 | 2 | 5 | 8 |
| `eu/cj` | 0 | 2 | 4 | 6 |
| `de/zpo` | 0 | 2 | 7 | 8 |

### Critical defects (fixed)

- **`tr/iyuk`: the seven-day break extension was lost when the raw last day fell on a weekend or holiday at the end of August.** The holiday roll ran before the break check. Service one day later could produce a deadline a week earlier (e.g. 2024-07-01 + 60 days gave 2024-09-02; correct is 2024-09-09).
  - The break is now checked on the raw last day first (İYUK m.8/3), then the roll applies (m.8/2).
  - The same ordering defect existed in `tr/hmk` behind the non-default option `recess_after_holiday_shift="yes"`; it is fixed the same way.
- **`gb-eaw/cpr`: counting back from a hearing with service by first class post gave a date two days too late.** The posting rule treated the hearing as a posting date. Example: 3 days before 20 October 2025 must be posted by Sunday 12 October, not 16 October. Posting is now handled separately for backward periods (CPR 2.8(4), 6.26).

### Other fixes

- **Türkiye**
  - İYUK: when m.8/2 moves the last day into the break, the default is now the earlier date. A new option `break_after_holiday_shift` and a notice cover this; it is unsettled.
  - İYUK: a new notice for places with a single administrative or tax court (m.61/1).
  - HMK: a notice that m.104 extends only HMK periods in matters subject to the recess.
  - HMK: the corrected m.103 description.
  - CMK: the Criminal General Assembly decision E.2019/16-292 K.2021/275 is cited for service during the recess.
  - CMK: a notice when m.39/4 moves the last day into the recess, and a pre-2012 warning.
  - Administrative leave days added to the calendar (2014-10-03, 2016-07-08), so the existing notices can fire.
  - AYM: corrected quote and decision URLs, and an office-hours notice.
  - İİK: a physical filing notice.
  - VUK: a notice on the basis for 23:59.
- **England and Wales**
  - The further Christmas closure day of PD 2A for acts at the court office.
  - Backward periods end on a business day.
  - Claim forms (CPR 6.14) and the 4.30pm rule (CPR 6.26).
  - Cut-off notices (4.30pm service, 4pm e-mail filing).
  - Citations for week counts.
  - The acknowledgment and defence presets in the demo now count as acts at the court office.
- **United States**
  - Backward periods reaching a Friday observed for a Saturday holiday now take the earlier date (new default `observed_friday="safe"`).
  - A notice that the three added days of Rule 6(d) do not apply to periods from entry of judgment, Rule 4 service or one's own service.
  - Executive-order closure days (E.O. 14371) for backward periods.
  - Suffolk County observances with a notice.
  - Corrected legal sources in the calendar description.
- **EU Court of Justice**
  - Corrected case-law pin cite (C-660/17 P, EU:C:2019:509, para. 12).
  - The e-Curia option is ignored, with a notice, for time limits running from publication.
  - A new option for time limits where the Rules exclude the distance extension.
  - The Court of Justice e-Curia decision cited.
  - Calendar sources completed.
- **Germany**
  - A notice on the five-month limit of §§ 517, 520(2), 548 and 551(2) ZPO.
  - The court-seat notice now names the court of filing (BGH VI ZA 27/11, now with date, URL and quote).
  - Citations for § 130a(5) ZPO and § 188(2) BGB.
  - German names for eight Land calendars.
  - The one-off Berlin holiday on 17 June 2028.
  - Official sources added to the calendars.

### Defects found after release (fixed on 20 October 2026)

- **`eu/cj`: every Court of Justice deadline that reached 2027 failed with `CoverageError`.** The `eu-cj` calendar stopped at 2026, so two-month time limits from about 22 October 2026 could not be computed.
  - The Court's list C/2026/1114 (OJ C, 18.2.2026), already among the sources, sets the official holidays for **1 November 2026 to 31 October 2027**.
  - Calendars can now end their verified data on a given day (`coverage.until`). `eu-cj` now runs to 31 October 2027; later dates still raise `CoverageError` until the next list is added.
  - Example: 25 October 2026 + 2 months = 25 December 2026, + 10 days for distance = Monday 4 January 2027.
  - A new CI check (`scripts/check_coverage.py`) fails when any calendar's verified data ends within six months, so the next list is added in time.
- **`tr/*`: periods running through the 2020 and 2023 extraordinary suspensions were computed without any warning.**
  - Law No. 7226 provisional Art. 1 (RG 26.03.2020, 31080 bis), read in the Official Gazette, stopped periods from 13 March 2020 (enforcement and bankruptcy periods from 22 March 2020) to 30 April 2020. Presidential Decision No. 2480 (RG 30.04.2020, 31114) extended this to 15 June 2020. Periods with 15 days or less left were extended by 15 days.
  - Presidential Decree No. 120 (RG 11.02.2023, 32101 bis) stopped periods from 6 February to 6 April 2023 for the state-of-emergency provinces, and was later extended in some places. The decree's text in the Gazette is an image, so the dates and scope were taken from the Ankara Bar Association bulletin of 20 February 2023 that quotes it.
  - The packs do not apply these suspensions, because who is covered depends on the person, the place and the type of period. They now add a notice (`suspension-2020-covid`, `suspension-2023-earthquake`) whenever the period touches those dates. Notices can now test the computed date against absolute dates (`date_from`, `date_before`).
  - Vector `hmk-v04-three-months-sacrifice-feast` (trigger 28 March 2023) now expects the earthquake notice.

### Findings not changed

- `de/zpo`: the shared German roll message keeps "Arbeitstag"; overriding it with the statute's "Werktag" would have left the other ten languages in English. The statute text stays in the § 222(2) citation.
- `de/zpo`: § 339(2) ZPO (one month for service abroad) is not modelled; the § 339 preset assumes service in Germany.
- `tr/aym`: the roll step still cites only the Turgut Tayyar decision, not 6216 m.49/7.
- Explanations defined only in English inside a rule pack still show in English in the other languages; a translated fallback needs an engine change.

### Translations, demo and tooling

- **Translations.** Wrong legal terms and plural agreement were fixed in all ten languages, for example:
  - German Werktag (includes Saturday) → Arbeitstag;
  - Arabic number agreement;
  - Portuguese "meios-dias" (noon);
  - Japanese 起算日.
- **Demo.** One defect: WebKit sized native selects by their longest option, overflowing phone layouts. Fixed.
- **Release rehearsal.**
  - The CLI lacked `--calendar` for `deadline`.
  - `lexdays check` answered in Turkish for every non-English language.
  - The npm and PyPI READMEs were one-line stubs.

  All three are fixed.

## Open questions for a lawyer

1. **Türkiye.**
   - Is 8 September (HGK method) settled for HMK m.104? The 11th Civil Chamber stated 7 September in passing.
   - CMK m.331/4 for service during the recess: does the Criminal General Assembly decision of 2021 settle `defer_start`? The default stays on the earlier date until confirmed.
   - A last day moved into the recess or break by the holiday rule: no decision either way.
   - Does m.104 or m.8/3 reach periods set by other laws or by the judge?
   - AYM: does an electronic application count until 23:59?
2. **England and Wales.**
   - Does CPR 2.8(5) apply to CE-File and e-mail filing?
   - When does a backward period end on a non-business day?
   - Which cut-off time should be shown?
3. **United States.**
   - Is the observed Friday a "legal holiday" under Rule 6(a)(6)?
   - Are executive-order closures holidays "declared by the President"?
   - Are Suffolk County days holidays for the Boston courthouse?
4. **EU.** Is the seventh e-Curia day extended when it falls on a holiday? Does the distance extension apply to time limits set by the Court?
5. **Germany.**
   - How should the five-month limit be computed together with the appeal period?
   - Extensions of the grounds period (BGH IX ZB 198/04).
   - Fronleichnam municipalities in Thuringia; Niedersachsen and Schleswig-Holstein Reformation Day and the Mecklenburg-Vorpommern Women's Day confirmed only from secondary sources.

Reports and corrections are welcome through the "Rule correction" issue form.
