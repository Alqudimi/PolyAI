# Governance

> **Repository:** https://github.com/Alqudimi/PolyAI

## Project Structure

PolyAI is a community open-source project with a **BDFL** (Benevolent Dictator For Life) governance model, common for small focused open-source projects.

### Roles

#### BDFL / Lead Maintainer

**Abdulaziz Alqudimi** ([@Alqudimi](https://github.com/Alqudimi))

Responsibilities:
- Final decision on project direction and roadmap
- Approving and merging pull requests
- Managing releases
- Enforcing the Code of Conduct
- Responding to security reports

#### Contributors

Anyone who submits accepted pull requests. Contributors are recognised in release notes and the repository's contributor graph.

Contributors who make sustained, significant contributions may be invited to become **Maintainers**.

#### Maintainers

Trusted contributors with merge access. Maintainers can:
- Review and merge pull requests (except their own)
- Triage issues
- Participate in roadmap planning

Current maintainers: *(see [MAINTAINERS.md](MAINTAINERS.md))*

---

## Decision Making

### Day-to-Day Decisions

Most decisions (bug fixes, small improvements, documentation) are made by any maintainer through normal PR review.

### Significant Decisions

For significant changes (new providers, API changes, breaking changes, architectural shifts), the process is:

1. Open a GitHub Discussion or issue proposing the change
2. Allow at least 7 days for community feedback
3. Lead maintainer makes the final decision
4. Decision is documented in the issue/discussion

### Disagreements

If contributors disagree with a decision, they should:
1. Clearly articulate their concern in the relevant issue/PR
2. Propose an alternative with reasoning
3. Accept that the lead maintainer has final say

---

## Contribution Philosophy

PolyAI follows these principles for accepting contributions:

- **Correctness over features** — a well-tested bug fix is more valuable than an untested feature
- **Simplicity over complexity** — prefer simple implementations that are easy to understand and maintain
- **Backwards compatibility** — avoid breaking changes in minor versions
- **Minimal dependencies** — new dependencies must be strongly justified

---

## Release Authority

Only the lead maintainer publishes releases to PyPI. This ensures:
- Quality control before release
- Consistent versioning
- PyPI trusted publishing (OIDC) remains controlled

---

## Changes to Governance

Governance changes require a GitHub Discussion open for at least 14 days, followed by a decision by the lead maintainer.

---

## License and IP

All contributions to PolyAI are licensed under the MIT License. By submitting a pull request, you agree that your contribution is licensed under the same MIT License that covers the project.

Copyright is retained by the original author (Abdulaziz Alqudimi) for the original work, and by respective contributors for their contributions.
