# Releasing

Releases are published to PyPI and npm by `.github/workflows/release.yml` using **Trusted Publishing** (OpenID Connect). No long-lived API tokens are stored in the repository.

## One-time setup

1. **GitHub environments.** In *Settings → Environments*, create `pypi` and `npm`. Optionally require a reviewer before deployment.
2. **PyPI.** At https://pypi.org/manage/account/publishing/ add a *pending publisher*:
   - project name `lexdays`, owner `DoGood-Studio`, repository `lexdays`, workflow `release.yml`, environment `pypi`.
3. **npm.** The first version has to be published manually. Trusted publishing can only be configured for a package that already exists.
   ```bash
   cd js && npm ci && npm run build && npm publish --access public
   ```
   Then, in the package settings on npmjs.com, add a trusted publisher: GitHub Actions, repository `DoGood-Studio/lexdays`, workflow `release.yml`, environment `npm`. Finally, disallow token-based publishing.
4. **Repository settings.** Enable private vulnerability reporting (*Security → Settings*), GitHub Pages from GitHub Actions, and a ruleset on `main` that blocks force pushes and deletion and requires pull requests and passing CI.

## Every release

1. Update the version in `python/pyproject.toml`, `python/src/lexdays/__init__.py`, `js/package.json`, `js/src/index.ts` and `CITATION.cff`.
2. Move the `Unreleased` notes in `CHANGELOG.md` under the new version.
3. Open a pull request, wait for CI, merge.
4. Create a GitHub Release with the tag `vX.Y.Z` and the changelog notes. The workflow checks that the tag matches both package versions, runs the tests, and publishes to PyPI and npm with provenance.
