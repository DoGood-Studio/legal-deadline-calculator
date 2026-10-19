# Reliability report

A deadline calculator has to be trustworthy. This page describes what is done to keep lexdays correct, what each measure protects against, and where its limits are. The numbers are for version 0.1.0 and are recomputed by CI on every change.

No software can guarantee that it is free of errors. The goal here is that errors are **unlikely, visible and easy to report**.

## 1. Correctness of the rules

| Measure | Protects against | Evidence |
|---|---|---|
| Every step cites its statute or decision | rules that cannot be checked | 100% of `count`, `roll` and `recess` steps carry a citation (enforced by a test) |
| Test vectors from real cases | the engine diverging from how courts actually count | 31 Turkish vectors from Court of Cassation, Council of State and Constitutional Court decisions; 6 from the GİB tax calendar; the FRCP 2009 Advisory Committee Note examples; the official CPR 2.8 examples; the C-660/17 P computation |
| Disputed points as options, with a notice on the result | silently picking the wrong side of a split (the default follows settled high-court case law, otherwise the earlier date) | e.g. 8 vs 7 September (HMK 104), a holiday shift into the recess, feast eves, service during the criminal recess, the US observed Friday |
| Notices on the result | users missing a caveat | e.g. "the last day is an administrative leave day: not a holiday", "İİK periods are not extended by the judicial recess" |
| Research notes with source quality labels | unverifiable claims | statute texts read from mevzuat.gov.tr, EUR-Lex, Cornell LII and justice.gov.uk; decisions labelled by how they were verified |

**Limits.** The packs are `beta`: researched carefully, but not yet reviewed by practising lawyers in each jurisdiction. Some points are genuinely unsettled. They are flagged, not resolved.

## 2. Correctness of the data

| Measure | Protects against | Evidence |
|---|---|---|
| Explicit coverage years | silently wrong results for years without verified data | `CoverageError` outside `tr` 2000–2035, `gb-eaw` 2019–2028, `eu-cj` 2025–2026, … |
| Primary sources | data copied from unreliable lists | Turkish feast dates queried from Diyanet (82 lookups, 1995–2035); GOV.UK bank holidays feed; 5 U.S.C. § 6103; CJEU decision C/2025/1569 |
| Independent cross-check, weekly in CI | data drift and typos | `scripts/crosscheck_calendars.py`: **0 differences** for 22 calendars against python-holidays (TR 2000–2035, US 1986–2099, DE and all 16 Länder 1995–2035, GB) and the GOV.UK feed |
| Strict validation and JSON Schemas | malformed definitions | unknown fields, impossible dates, duplicate ids and contradictory conditions are rejected at load time; all 34 calendar and rule pack files validate against the schemas |

## 3. Correctness of the code

| Measure | Protects against | Evidence |
|---|---|---|
| 290 hand-derived conformance vectors | regressions in counting, rolling, recesses, observed days | run by both test-suites |
| 80 invalid-definition vectors | bad data being accepted | both languages must raise the same error class |
| Property-based tests (Hypothesis, fast-check) | edge cases nobody thought of | invariants checked on thousands of random inputs per run: business-day results land on working days; `business_days_between` inverts `add_business_days`; traces chain from trigger to deadline; rolling packs never end on a non-working day; a later trigger never gives an earlier deadline; date round trips |
| Differential testing | the two implementations drifting apart | 1,800 random computations; every TypeScript result document must be **byte-identical** to Python's (SHA-256 of canonical JSON, including every message in every language) |
| Coverage gate | untested code paths | 96.9% line and branch coverage (Python); CI fails below 95% |
| Strict typing and linting | type errors and common bugs | mypy `--strict`, TypeScript `strict` + `noUncheckedIndexedAccess`, ruff |
| Cross-platform CI | OS- and version-specific bugs | Linux, Windows and macOS; Python 3.10–3.14; Node 22/24 for the test-suite, and the built package on Node 18/20 |
| No time zones, no `Date` objects | off-by-one errors around midnight or daylight saving | all arithmetic uses civil dates; TypeScript rejects `Date` inputs with an explanation |

**A real bug found this way.** Property-based testing showed that `business_days_between` did not exactly invert `add_business_days` when counting backwards from a non-working day (e.g. from Sunday 4 February 2001). None of the hand-written vectors covered this case. The semantics were fixed and documented, and the property now runs on every change.

**A legal surprise found this way.** The property "a later trigger never gives an earlier deadline" fails at the end of a judicial recess, and that is the law, not a bug. A 2-week period served on 17 August 2026 ends on 31 August, inside the recess, so it is extended: to 8 September under HMK 104, 7 September under İYUK 8/3 and 3 September under CMK 331. The same period served one day later ends on 1 September, after the recess, and is not extended. The property is therefore checked everywhere except where a recess extension was applied, and users should know about this cliff.

## 4. Correctness of the packages

| Measure | Evidence |
|---|---|
| The wheel, the sdist and a wheel built from the sdist are installed into clean environments and run | all ship the 35 data files; CLI smoke test in CI |
| The npm tarball is installed into a fresh project | ESM `import`, CommonJS `require` and a strict TypeScript consumer all work |
| No runtime dependencies | nothing to break or compromise transitively |

## 5. Supply chain and security

- All GitHub Actions are pinned by commit SHA, and workflows have read-only default permissions.
- CodeQL (Python, TypeScript, Actions) and OpenSSF Scorecard run on every push.
- Releases use PyPI and npm Trusted Publishing (OIDC, provenance). No API tokens are stored.
- Dependabot keeps the development tools current.
- Calendar and rule pack ids are validated, which blocks path traversal when loading data.

## 6. How to report a problem

- A wrong deadline or holiday: open a **Rule correction** issue with the statute or decision.
- A bug in the library: open a **Bug report**.
- A security issue: use private vulnerability reporting (see [SECURITY.md](../SECURITY.md)).

## Reproducing these numbers

```bash
cd python && uv run pytest --cov            # tests and coverage
cd js && npm test                           # TypeScript tests, including the differential check
uv run --project python --with holidays python scripts/crosscheck_calendars.py
```
