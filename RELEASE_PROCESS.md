# Release Process

> **Repository:** https://github.com/Alqudimi/PolyAI
> **Maintainer:** Abdulaziz Alqudimi

This document describes how PolyAI releases are prepared and published.

---

## Release Checklist

### Pre-release

- [ ] All CI checks pass on `main`
- [ ] Nightly integration tests pass
- [ ] `CHANGELOG.md` updated — move items from `[Unreleased]` to the new version section
- [ ] `polyai/_version.py` version bumped
- [ ] `pyproject.toml` version bumped (must match `_version.py`)
- [ ] All deprecation warnings updated for the new version reference
- [ ] Migration guide written if this is a major release

### Bump Version

```bash
# Edit these two files:
# polyai/_version.py   → __version__ = "1.1.0"
# pyproject.toml       → version = "1.1.0"

# Verify they match
python -c "import polyai; print(polyai.__version__)"
```

### Update CHANGELOG

```markdown
## [1.1.0] — 2026-07-01

### Added
- ...

### Fixed
- ...

### Changed
- ...

[1.1.0]: https://github.com/Alqudimi/PolyAI/compare/v1.0.0...v1.1.0
```

### Create the Release

```bash
# Commit the version bump
git add polyai/_version.py pyproject.toml CHANGELOG.md
git commit -m "chore(release): v1.1.0"
git push origin main

# Create and push the tag
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin v1.1.0
```

Pushing the tag triggers the [release workflow](.github/workflows/release.yml) automatically.

---

## Automated Release Pipeline

When a version tag (`v*.*.*`) is pushed, the pipeline runs 8 jobs:

```
validate-version
      │
test-before-release
      │
    build
      │
publish-testpypi
      │
verify-testpypi
      │
  publish-pypi ────────────────────────┐
      │                                │
github-release                post-release-verify
```

### Job Details

| Job | What it does |
|---|---|
| `validate-version` | Checks tag matches `pyproject.toml` version |
| `test-before-release` | Runs full unit test suite |
| `build` | Builds wheel + sdist, verifies contents |
| `publish-testpypi` | Publishes to TestPyPI first (safety check) |
| `verify-testpypi` | Installs from TestPyPI and smoke-tests |
| `publish-pypi` | Publishes to production PyPI via OIDC |
| `github-release` | Creates GitHub Release with changelog + checksums |
| `post-release-verify` | Installs from production PyPI and verifies version |

### PyPI Authentication

PolyAI uses [Trusted Publishing (OIDC)](https://docs.pypi.org/trusted-publishers/) — no `PYPI_TOKEN` secret needed. The GitHub Actions environment is pre-configured as a trusted publisher in the PyPI project settings.

---

## Post-release Steps

After the pipeline completes:

1. **Announce** — Post in GitHub Discussions
2. **Update Wiki** — If any documentation changed significantly
3. **Close milestone** — Close the GitHub milestone for this release
4. **Prepare next** — Open `[Unreleased]` section in CHANGELOG.md

---

## Hotfix Releases

For critical bugs that need to be fixed immediately:

```bash
# Create a hotfix branch from the release tag
git checkout -b hotfix/critical-fix v1.1.0

# Make the fix
# ...

# Bump patch version
# polyai/_version.py: 1.1.0 → 1.1.1
# pyproject.toml: 1.1.0 → 1.1.1

git commit -m "fix(transport): handle malformed SSE frame"
git tag -a v1.1.1 -m "Hotfix v1.1.1"
git push origin hotfix/critical-fix v1.1.1

# Merge back to main
git checkout main
git merge hotfix/critical-fix
git push origin main
```

---

## Rolling Back a Release

If a critical issue is discovered post-release:

1. **Yank** the PyPI release:
   ```bash
   pip install twine
   twine yank polyai==1.1.0 --reason "Critical bug in streaming"
   ```
   Yanked versions are still installable if pinned, but pip won't install them automatically.

2. **Release a patch** with the fix (don't delete releases — it breaks pinned installs).

3. **Post an advisory** in GitHub Security Advisories if it's a security issue.
