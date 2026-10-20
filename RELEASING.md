# Releasing

Releases are published to PyPI and npm by `.github/workflows/release.yml` using **Trusted Publishing** (OpenID Connect). No long-lived API tokens are stored in the repository.

## One-time setup

1. **GitHub environments.** In *Settings → Environments*, create `pypi` and `npm`. Optionally require a reviewer before deployment.
2. **PyPI.** At https://pypi.org/manage/account/publishing/ add a *pending publisher*:
   - project name `lexdays`, owner `DoGood-Studio`, repository `legal-deadline-calculator`, workflow `release.yml`, environment `pypi`.
   - The repository and the packages have different names on purpose: the repository is named after what people search for, the packages keep the short name.
3. **npm.** The first version has to be published manually. Trusted publishing can only be configured for a package that already exists.
   ```bash
   cd js && npm ci && npm run build && npm publish --access public
   ```
   The release workflow skips a version that is already on npm, so the GitHub Release for this first version only publishes to PyPI.
   Then, in the package settings on npmjs.com, add a trusted publisher: GitHub Actions, repository `DoGood-Studio/legal-deadline-calculator`, workflow `release.yml`, environment `npm`. Finally, disallow token-based publishing.
   An npm trusted publisher that has not published anything expires 48 hours after it is created, so add it shortly before the first automated release (or recreate it then).
4. **Repository settings.** Enable private vulnerability reporting (*Security → Settings*), GitHub Pages from GitHub Actions, and a ruleset on `main` that blocks force pushes and deletion and requires pull requests and passing CI.

## Every release

1. Update the version in `python/pyproject.toml`, `python/src/lexdays/_version.py`, `js/package.json`, `js/src/version.ts` and `CITATION.cff`, and set `date-released` in `CITATION.cff` to the release date. Then run `uv lock` in `python/` and `npm install --package-lock-only` in `js/`, so the lockfiles carry the new version (CI runs `uv sync --locked`). `python/tests/test_metadata.py` fails if any of these disagree.
2. Move the `Unreleased` notes in `CHANGELOG.md` under the new version and date. If the release fixes a publicly known vulnerability, list it under a `### Security` heading with its advisory or CVE id.
3. Open a pull request, wait for CI, merge.
4. Create a GitHub Release with the tag `vX.Y.Z` and the changelog notes. The workflow checks that the tag matches both package versions, runs the tests, and publishes to PyPI and npm with provenance.
