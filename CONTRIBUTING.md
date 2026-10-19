# Contributing to lexdays

Thank you for helping. The most valuable contributions are, in order:

1. **Rule corrections and reviews by lawyers.** If a result is wrong, or a disputed point is presented unfairly, open a *Rule correction* issue with the statute article or decision that supports your view.
2. **New jurisdictions** as rule packs (JSON plus test vectors with sources).
3. **Calendar data**: new years, confirmed feast dates, one-off holidays, court closures.
4. Code, documentation and the demo page.

*Türkçe:* Kural hatası bildirmek için "Kural düzeltmesi" şablonunu kullanın ve dayanak kanun maddesini veya kararı ekleyin. Katkılar Türkçe de yazılabilir.

## Ground rules

- **Every rule needs a source.** A step in a rule pack should `cite` the article or decision it implements. A test vector should name its `source`.
- **Prefer real cases.** The best test vectors come from court decisions, official worked examples or official calendars. Derived vectors are fine, but say so.
- **Disputed points become options.** If courts or practitioners disagree, add an option plus a `notice` that explains the disagreement. The default follows settled high-court case law; where there is none, it is the **earlier, safer** date. Never silently pick one side.
- **Never guess data.** If holiday data for a year is not verified, keep it outside the calendar's `coverage`.
- **Python and TypeScript must agree.** Any engine change goes into both `python/src/lexdays` and `js/src`, and both test suites must pass.

## Development setup

```bash
# Python (uses uv: https://docs.astral.sh/uv/)
cd python
uv sync
uv run pytest            # all tests, including the shared vectors
uv run ruff check . && uv run mypy

# TypeScript (Node 22+ for the dev toolchain)
cd js
npm ci
npm test && npm run typecheck && npm run build
```

After changing the engine or any data file, regenerate the differential vectors and commit them:

```bash
uv run --project python python scripts/gen_differential.py
```

To cross-check calendars against python-holidays and the GOV.UK feed:

```bash
curl -fsSL https://www.gov.uk/bank-holidays.json -o /tmp/bank-holidays.json
uv run --project python --with holidays python scripts/crosscheck_calendars.py --govuk /tmp/bank-holidays.json
```

## Adding a jurisdiction

1. Add or reuse a calendar in `data/calendars/<id>.json` (schema: `spec/calendar.schema.json`).
2. Write the rule pack in `data/rulepacks/<country>/<name>.json` (schema: `spec/rulepack.schema.json`). See [docs/rulepacks.md](docs/rulepacks.md).
3. Add vectors in `vectors/<country>/deadline.json`, each with a `source`.
4. Run both test suites and regenerate the differential vectors.
5. Mention the pack in `README.md` and `CHANGELOG.md`.

## Tests are required

Every new feature, rule pack, calendar change and bug fix comes with tests in the same pull request:

- engine changes: tests in both `python/tests` and `js/test`, or shared vectors in `vectors/` that both suites run;
- rule packs and calendars: vectors with a `source`;
- bug fixes: a test that fails without the fix.

A pull request without tests for new behaviour is not merged.

## Coding standards

- **Python:** must pass `ruff check` with the rule set in `python/pyproject.toml` and `mypy` in strict mode. All code is typed. Give new public functions a docstring.
- **TypeScript:** must pass `tsc` with `strict` and `noImplicitOverride` (`js/tsconfig.json`). Give new public functions a TSDoc comment.
- **Data:** calendars and rule packs must validate against the JSON Schemas in `spec/` (checked by `python/tests/test_schemas.py`).
- **Dependencies:** the libraries have no runtime dependencies. Do not add one without opening an issue first.
- Match the style of the surrounding code, and keep the Python and TypeScript implementations structurally parallel so they are easy to compare.

## Commits and pull requests

To propose a change:

1. Fork the repository and create a branch from `main`.
2. Make the change with tests (see above) and run both test suites locally.
3. Open a pull request against `main` and fill in the template. CI runs automatically.
4. A maintainer reviews it; rule changes are checked against the cited source. Changes are merged after review and green CI.

- Keep pull requests focused. Describe what changed and why, and link the legal source for rule changes.
- CI must be green: tests on Linux, Windows and macOS, coverage ≥ 95%, strict type checks, and the cross-checks.
- By contributing you agree that your contribution is licensed under the MIT License.

## Code of conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md).
