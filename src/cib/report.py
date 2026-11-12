"""Static, escaped report generated only from saved run and score records."""

import html
import json
from pathlib import Path

from .pipeline import validate_raw
from .records import digest, file_hash, read


def number(value):
    return "missing / withheld" if value is None else f"{value:.8g}"


def literal(value):
    text = value if isinstance(value, str) else json.dumps(value, indent=2, sort_keys=True)
    return "<pre>" + html.escape(text) + "</pre>"


def report_file(raw_path, scores_path, output):
    raw, scores = read(raw_path), read(scores_path)
    if raw.get('dataset', {}).get('split') == 'exploratory_pilot':
        raise ValueError('use python -m cib.pilot report with pilot scores for the pilot policy and denominators')
    validate_raw(raw)
    if (scores["schema_version"] != "cib.scores.v1"
            or scores["raw_sha256"] != file_hash(raw_path)
            or scores["run_id"] != raw["manifest"]["run_id"]
            or scores["dataset_sha256"] != digest(raw["dataset"])
            or scores["analysis"] != raw["manifest"]["analysis"]):
        raise ValueError("scores do not belong to this saved raw run")
    if ({o["request_id"] for o in scores["observations"]}
            != {r["request_id"] for r in raw["requests"]}):
        raise ValueError("score observation set mismatch")
    comparison = scores["comparison"]
    real = raw["schema_version"] == "cib.real-run.v1"
    lines = [("# EXPLORATORY ENGINEERING CHECK — real local CIB report" if real else
              "# SYNTHETIC DEVELOPMENT FIXTURES — offline CIB report"), "",
             ("**Development tasks only; no held-out, compression, or preservation conclusion.**" if real else
              "**No models were run. These scripted responses are not measured model performance "
              "and support no claims about compression effects.**"), "",
             "These hand-authored English urn cases measure controlled probability reporting. "
             "They share one template cluster and are not independent research samples.", "",
             "## Configuration and lineage", "",
             f"Raw artifact: `{Path(raw_path).resolve()}`; SHA-256 `{scores['raw_sha256']}`.", "",
             f"Scores: `{Path(scores_path).resolve()}`; SHA-256 `{file_hash(scores_path)}`.", "",
             f"Scorer `{scores['scorer_version']}`; source SHA-256 `{scores['scorer_source_sha256']}`.", "",
             literal(raw["manifest"]), "",
             "Pre and post are independent self-contained requests. Each condition/label variant "
             "has its own pre request. Label swaps remain in their base scenario. "
             "Conditions and variants receive equal weight, then scenarios receive equal weight. "
             "A scenario metric is withheld if any of its eligible conditions is missing. "
             "Direction and stability diagnostics are disabled: tolerances remain unresolved.", "",
             "## Coverage", "", literal(scores["coverage"]), "",
             literal(scores.get("format_coverage", {})), "",
             "Parser: `" + scores.get("parser_version", "strict-probability-v1") + "`. "
             "The primary policy remains strict JSON; fence diagnostics are exploratory.", "",
             "Completed generations count returned outputs, including refusals and truncations; "
             "normal completions exclude those stop statuses. Valid means scoreable under the named parser. "
             "Malformed, refusal, truncation, and infrastructure failures have missing scores, never zero error.", "",
             "## Paired posterior-loss comparison", "", literal(comparison), "",
             "The complete-scenario change describes only fully observed scenarios. The full-set "
             "contrast is withheld when any scenario is incomplete. Missing-loss bounds assign each "
             "unknown posterior loss 0 or 1 over the full planned set, retaining every observed loss. "
             "They are conservative bounds, not sampling confidence intervals. " +
             ("Positive change means greater loss for the quantized deployment." if real else
              "Positive change means greater loss for fixture-perturbed; neither fixture is a real deployment."), "",
             "## Per-scenario metrics", "",
             "| Deployment | Scenario | Metric | Scoreable / planned | Mean |", "| --- | --- | --- | --- | --- |"]
    for deployment, scenarios in scores["scenario_scores"].items():
        for scenario, metrics in scenarios.items():
            for metric, summary in metrics.items():
                if metric == "posterior_bounds":
                    continue
                lines.append(f"| {deployment} | {scenario} | {metric} | "
                             f"{summary['scoreable']} / {summary['planned']} | {number(summary['mean'])} |")
    lines += ["", "## Condition metrics and independent targets", "", literal(scores["condition_scores"]), "",
              "## Per-observation status and probability", "", literal(scores["observations"]), "",
              "## All paired inputs, raw responses, and failures", "",
              "All planned cases are shown, including unchanged responses, valid incorrect answers, "
              "missing observations, and every failure. Examples are exhaustive rather than selected by outcome.", ""]
    requests = {r["request_id"]: r for r in raw["requests"]}
    attempts = {}
    for attempt in raw["attempts"]:
        attempts.setdefault(attempt["request_id"], []).append(attempt)
    indexed = {}
    for request in raw["requests"]:
        identity = (request["scenario_id"], request["label_variant"], request["condition_id"], request["stage"])
        indexed.setdefault(identity, []).append(request["request_id"])
    for identity, ids in indexed.items():
        lines += ["### " + " / ".join(identity), "", literal(requests[ids[0]]["input"]), ""]
        for request_id in ids:
            request = requests[request_id]
            lines += [f"**{request['deployment_id']}** — request `{request_id}`", "",
                      literal(attempts[request_id]), ""]
    with Path(output).open("x") as stream:
        stream.write("\n".join(lines) + "\n")
