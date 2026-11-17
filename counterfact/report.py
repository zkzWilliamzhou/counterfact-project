"""Renderers. Every emitted string is redacted and control-character free."""

from __future__ import annotations

import json
from typing import Dict, Sequence

from . import __version__
from .safety import redact
from .types import Finding, SCOPE_NOTICE

RULE_ID = "CF001"


def _factor_lines(finding: Finding, factors: Sequence) -> str:
    by_name = {f.name: f for f in factors}
    lines = []
    for name in finding.factors:
        factor = by_name.get(name)
        if factor is None:
            lines.append("  - %s" % redact(name))
            continue
        good = redact(factor.good, name)
        bad = redact(factor.bad, name)
        lines.append(
            "  - %-24s %-10s  %s  ->  %s"
            % (redact(name)[:24], factor.kind, good[:28] or "(unset)", bad[:28] or "(unset)")
        )
    return "\n".join(lines) or "  (none)"


def render_text(finding: Finding, plan: Dict, factors: Sequence) -> str:
    lines = [
        "counterfact %s  |  counterfactual environment debugger" % __version__,
        "=" * 72,
        "STATUS      : %s" % finding.status,
        "EXPERIMENTS : %d logged (%d actual executions)"
        % (len(finding.experiments), sum(1 for e in finding.experiments if not e.cache_hit)),
        "REPLICATION : %d / %d independent checks behaved as expected"
        % (finding.replication[0], finding.replication[1]),
        "ORACLE      : %s" % json.dumps(
            {key: redact(value, key) for key, value in finding.oracle.items()},
            sort_keys=True,
        ),
        "-" * 72,
        "Smallest tested causal set (%d factor(s)):" % len(finding.factors),
        _factor_lines(finding, factors),
        "-" * 72,
    ]
    if finding.warnings:
        lines.append("WARNINGS")
        for warning in finding.warnings:
            lines.append("  ! %s" % redact(warning))
        lines.append("-" * 72)
    lines.append("SCOPE")
    lines.append("  " + SCOPE_NOTICE)
    lines.append("")
    lines.append(
        "counterfact proved an intervention under these conditions; it did not "
        "identify the underlying defect. Verify the fix yourself."
    )
    return "\n".join(lines) + "\n"


def render_json(finding: Finding, plan: Dict) -> str:
    return json.dumps(finding.to_dict(plan), indent=2, sort_keys=True) + "\n"


def render_sarif(finding: Finding) -> str:
    names = ", ".join(redact(n) for n in finding.factors) or "none"
    level = "warning" if finding.status in ("CONFIRMED", "PROBABLE") else "note"
    message = (
        "counterfact %s: smallest tested causal set = [%s]; replication %d/%d. %s"
        % (
            finding.status,
            names,
            finding.replication[0],
            finding.replication[1],
            SCOPE_NOTICE,
        )
    )
    sarif = {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "counterfact",
                        "version": __version__,
                        "informationUri": "https://github.com/counterfact/counterfact",
                        "rules": [
                            {
                                "id": RULE_ID,
                                "name": "MinimalTestedCausalSet",
                                "shortDescription": {
                                    "text": "A 1-minimal tested causal set was found."
                                },
                                "defaultConfiguration": {"level": "warning"},
                            }
                        ],
                    }
                },
                "results": [
                    {
                        "ruleId": RULE_ID,
                        "level": level,
                        "message": {"text": redact(message)},
                        "properties": {
                            "status": finding.status,
                            "factors": [redact(n) for n in finding.factors],
                            "replication": {
                                "successes": finding.replication[0],
                                "trials": finding.replication[1],
                            },
                            "experimentCount": len(finding.experiments),
                            "scopeNotice": SCOPE_NOTICE,
                        },
                    }
                ],
            }
        ],
    }
    return json.dumps(sarif, indent=2, sort_keys=True) + "\n"


def render_github(finding: Finding) -> str:
    names = ", ".join(redact(n) for n in finding.factors) or "none"
    lines = [
        "::notice title=counterfact::status=%s factors=%s replication=%d/%d"
        % (
            finding.status,
            names,
            finding.replication[0],
            finding.replication[1],
        )
    ]
    for warning in finding.warnings:
        lines.append("::warning title=counterfact::%s" % redact(warning).replace("\n", " "))
    return "\n".join(lines) + "\n"
