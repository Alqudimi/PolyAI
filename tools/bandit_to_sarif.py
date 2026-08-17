"""Convert Bandit JSON output to SARIF 2.1.0 for GitHub Code Scanning upload.

Minimal, dependency-free converter that maps Bandit results to the SARIF
2.1.0 schema expected by the `upload-sarif` action. Bandit's core package
does not ship a native SARIF formatter, so the CI job runs Bandit with
`-f json` and pipes the output through this converter.
"""

from __future__ import annotations

import json
import sys
from typing import Any

TOOL_NAME = "Bandit"
TOOL_VERSION = "1.7.8+"  # Bandit version series; exact version not critical
RULE_URL = "https://bandit.readthedocs.io/en/latest/plugins/index.html"

SEVERITY_MAP = {"LOW": "note", "MEDIUM": "warning", "HIGH": "error"}


def convert(bandit_results: dict[str, Any]) -> dict[str, Any]:
    """Map Bandit JSON results into a SARIF 2.1.0 report."""
    results: list[dict[str, Any]] = bandit_results.get("results", []) or []

    rule_index: dict[str, dict[str, Any]] = {}
    for result in results:
        rule_id = str(result.get("test_id") or "UNKNOWN")
        if rule_id not in rule_index:
            rule_index[rule_id] = {
                "id": rule_id,
                "shortDescription": {"text": str(result.get("test_name") or rule_id)},
                "helpUri": RULE_URL,
            }

    sarif_results: list[dict[str, Any]] = []
    for result in results:
        path = str(result.get("filename") or "")
        line = int(result.get("line_number") or 1)
        col = int(result.get("col_offset") or 0) + 1
        severity = SEVERITY_MAP.get(str(result.get("issue_severity") or "MEDIUM"), "warning")
        sarif_results.append(
            {
                "ruleId": str(result.get("test_id") or "UNKNOWN"),
                "level": severity,
                "message": {"text": str(result.get("issue_text") or "Security issue")},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": path},
                            "region": {
                                "startLine": line,
                                "startColumn": max(col, 1),
                            },
                        }
                    }
                ],
            }
        )

    runs: list[dict[str, Any]] = [
        {
            "tool": {
                "driver": {
                    "name": TOOL_NAME,
                    "informationUri": "https://bandit.readthedocs.io/",
                    "version": TOOL_VERSION,
                    "rules": sorted(rule_index.values(), key=lambda rule: rule["id"]),
                }
            },
            "results": sarif_results,
        }
    ]
    return {
        "$schema": (
            "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/main/"
            "sarif-2.1/schema/sarif-schema-2.1.0.json"
        ),
        "version": "2.1.0",
        "runs": runs,
    }


def main() -> int:
    if len(sys.argv) != 3:
        print(
            f"usage: {sys.argv[0]} <bandit.json> <output.sarif>",
            file=sys.stderr,
        )
        return 2
    bandit_json, sarif_out = sys.argv[1], sys.argv[2]
    with open(bandit_json, encoding="utf-8") as fh:
        bandit_results = json.load(fh)
    sarif = convert(bandit_results)
    with open(sarif_out, "w", encoding="utf-8") as fh:
        json.dump(sarif, fh, indent=2)
    n = len(sarif["runs"][0]["results"])
    print(f"SARIF written to {sarif_out} ({n} result(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
