## What and why

<!-- What does this change, and why? Link the issue if there is one. -->

## Legal source (for rule or data changes)

<!-- Statute article, decision (court, case number, date) or official calendar. -->

## Checklist

- [ ] Python and TypeScript behave identically (engine changes are in both `python/src` and `js/src`)
- [ ] Tests added or updated; new vectors name their `source`
- [ ] `uv run pytest`, `npm test` and the type checks pass
- [ ] Differential vectors regenerated (`scripts/gen_differential.py`) if the engine or data changed
- [ ] Disputed points are options with the safer default and a notice
- [ ] `CHANGELOG.md` updated
