# Versioning Policy

> **Repository:** https://github.com/Alqudimi/PolyAI

PolyAI follows [Semantic Versioning 2.0.0](https://semver.org/) (`MAJOR.MINOR.PATCH`).

---

## Version Number Meaning

### PATCH version (`1.0.X`)

Incremented for backwards-compatible bug fixes and maintenance changes:

- Bug fixes that don't change public API
- Documentation improvements
- CI/CD changes
- Dependency updates (non-breaking)
- Performance improvements that don't change behavior

**Users should always upgrade patch versions.**

### MINOR version (`1.X.0`)

Incremented for backwards-compatible new features:

- New providers
- New methods on `Client` or `AsyncClient`
- New optional parameters
- New exception types
- New utility functions
- New resource types

**Users can upgrade minor versions without changing their code.**

### MAJOR version (`X.0.0`)

Incremented for breaking changes:

- Removing or renaming public methods
- Changing method signatures (non-optional parameters)
- Changing the structure of response types
- Removing deprecated features
- Dropping Python version support

**Users must read the migration guide before upgrading major versions.**

---

## Pre-release Versions

| Suffix | Meaning | Example |
|---|---|---|
| `alpha` | Early development, unstable | `2.0.0-alpha1` |
| `beta` | Feature-complete, may have bugs | `2.0.0-beta1` |
| `rc` | Release candidate, near-final | `2.0.0-rc1` |

Pre-release versions are not recommended for production.

---

## Deprecation Policy

Before removing a feature:

1. **Deprecate first** — Mark with a deprecation warning (at least one minor version before removal)
2. **Document** — Add to CHANGELOG.md and the relevant docs
3. **Migration guide** — Provide the replacement API
4. **Remove** — Only in the next major version

Example deprecation warning:

```python
import warnings

def old_method(self):
    warnings.warn(
        "old_method() is deprecated and will be removed in v2.0.0. "
        "Use new_method() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return self.new_method()
```

---

## Python Version Support

| Python | Status |
|---|---|
| 3.9 | ✅ Supported |
| 3.10 | ✅ Supported |
| 3.11 | ✅ Supported (primary) |
| 3.12 | ✅ Supported |
| 3.8 and below | ❌ Not supported |

Python versions are dropped in **major** releases, with at least one **minor** release giving deprecation notice.

---

## Release Cadence

- **Patch releases:** As needed (bug fixes)
- **Minor releases:** Approximately every 1–2 months
- **Major releases:** Only when breaking changes are necessary; rare

---

## Changelog

All version changes are documented in [CHANGELOG.md](CHANGELOG.md) following the [Keep a Changelog](https://keepachangelog.com/) format.
