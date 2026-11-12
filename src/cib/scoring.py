"""Independent analytic scoring, pairing, and conservative missing-loss bounds."""

from collections import Counter
import json
import math
import re
from statistics import mean

from .pipeline import source_hash, validate_raw
from .records import digest, file_hash, key, read, write_new
from .tasks import cases

SCORER_VERSION = "updating-scorer-v1"


def parse_probability(text):
    def pairs(items):
        if len(items) != len(dict(items)):
            raise ValueError("duplicate JSON key")
        return dict(items)
    try:
        result = json.loads(text, object_pairs_hook=pairs)
        if not isinstance(result, dict) or set(result) != {"probability"}:
            raise ValueError("expected exactly probability")
        value = result["probability"]
        if isinstance(value, bool) or not isinstance(value, (float, int)):
            raise ValueError("expected JSON number")
        if not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError("invalid probability")
        return float(value)
    except (ValueError, TypeError, OverflowError) as error:
        raise ValueError("malformed probability response") from error


STRICT_PARSER = "strict-probability-v1"
DIAGNOSTIC_PARSER = "outer-json-fence-v1"


def parse_diagnostic(text):
    """Exploratory: bare strict JSON or exactly one complete outer fence."""
    if isinstance(text, str):
        match = re.fullmatch(r"\s*```(?:json)?\r?\n([^`]*?)\r?\n```\s*", text)
        if match:
            text = match.group(1)
    return parse_probability(text)


def score_attempt(attempt, parser=STRICT_PARSER):
    status = attempt["status"]
    if status != "completed":
        return {"status": status, "probability": None}
    try:
        return {"status": "valid", "probability": (parse_probability if parser == STRICT_PARSER else parse_diagnostic)(attempt["text"])}
    except ValueError:
        return {"status": "malformed", "probability": None}


def paired_requests(raw, left, right):
    deployments = raw["manifest"]["deployments"]
    if left == right or left not in deployments or right not in deployments:
        raise ValueError("comparison requires two distinct declared deployments")
    indexes = []
    for deployment in (left, right):
        index = {}
        for request in raw["requests"]:
            if request["deployment_id"] == deployment:
                identity = key(request)
                if identity in index:
                    raise ValueError("duplicate pairing key")
                index[identity] = request
        indexes.append(index)
    if not indexes[0] or indexes[0].keys() != indexes[1].keys():
        raise ValueError("mismatched scenario/condition/version/variant/trial/stage set")
    pairs = []
    for identity, request in indexes[0].items():
        other = indexes[1][identity]
        if request["input"] != other["input"] or request["decoding"] != other["decoding"]:
            raise ValueError("paired inputs or decoding differ")
        if raw["schema_version"] == "cib.real-run.v1":
            latest = {a["request_id"]: a for a in raw["attempts"]}
            a, b = latest.get(request["request_id"], {}), latest.get(other["request_id"], {})
            if "actual" in a and "actual" in b and a["actual"] != b["actual"]:
                raise ValueError("paired rendered inputs or token IDs differ")
        pairs.append((request, other))
    return pairs


def complete_mean(values):
    return mean(values) if values and all(v is not None for v in values) else None


def summarize(rows):
    # Never turn an incomplete scenario into the mean of its remaining conditions.
    metrics = {}
    for metric in ("posterior_error", "prior_error", "update_error", "uninformative_drift"):
        eligible = [r for r in rows if metric != "uninformative_drift" or r["uninformative"]]
        values = [r[metric] for r in eligible]
        metrics[metric] = {"mean": complete_mean(values),
                           "scoreable": sum(v is not None for v in values), "planned": len(values)}
    losses = [r["posterior_error"] for r in rows]
    metrics["posterior_bounds"] = [mean(0 if x is None else x for x in losses),
                                    mean(1 if x is None else x for x in losses)]
    return metrics


def calculate(raw, parser=STRICT_PARSER):
    validate_raw(raw)
    left, right = (("reference", "quantized") if raw["schema_version"] == "cib.real-run.v1"
                   else ("fixture-perfect", "fixture-perturbed"))
    pairs = paired_requests(raw, left, right)
    observations = []
    attempts = {a["request_id"]: a for a in raw["attempts"]}
    by_identity = {}
    for request in raw["requests"]:
        scored = {"schema_version": "cib.score.v1", "request_id": request["request_id"],
                  "deployment_id": request["deployment_id"], **score_attempt(attempts[request["request_id"]], parser)}
        observations.append(scored)
        by_identity[(request["deployment_id"], *key(request))] = scored
    rows = []
    dataset = raw["dataset"]
    for deployment in raw["manifest"]["deployments"]:
        for case in cases(dataset):
            def lookup(stage):
                return by_identity[(deployment, case["scenario_id"], dataset["task_version"],
                                    case["condition_id"], case["label_variant"],
                                    dataset["prompt_variant"], dataset["trial_index"], stage)]
            pre, post = lookup("pre"), lookup("post")
            p, q = pre["probability"], post["probability"]
            rows.append({"schema_version": "cib.condition-score.v1", **case,
                         "deployment_id": deployment,
                         "pre_request_id": pre["request_id"], "post_request_id": post["request_id"],
                         "pre_status": pre["status"], "post_status": post["status"],
                         "prior_error": None if p is None else abs(p - case["prior"]),
                         "posterior_error": None if q is None else abs(q - case["posterior"]),
                         "update_error": None if p is None or q is None else
                         abs((q - p) - (case["posterior"] - case["prior"])),
                         "uninformative_drift": None if not case["uninformative"] or p is None or q is None
                         else abs(q - p)})
    summaries = {}
    coverage = {}
    for deployment in raw["manifest"]["deployments"]:
        selected = [r for r in rows if r["deployment_id"] == deployment]
        summaries[deployment] = {
            scenario["scenario_id"]: summarize([r for r in selected if r["scenario_id"] == scenario["scenario_id"]])
            for scenario in dataset["scenarios"]}
        selected_observations = [o for o in observations if o["deployment_id"] == deployment]
        counts = Counter(o["status"] for o in selected_observations)
        selected_attempts = [a for a in raw["attempts"] if a["deployment_id"] == deployment and a["status"] != "not_attempted"]
        coverage[deployment] = {
            "requested": len(selected_observations), "attempts": len(selected_attempts),
            "executed_observations": len({a["request_id"] for a in selected_attempts}),
            "attempt_status_counts": dict(Counter(a["status"] for a in selected_attempts)),
            "completed_generations": sum(a["status"] in {"completed", "refusal", "truncated"} for a in selected_attempts),
            "normal_completions": sum(a["status"] == "completed" for a in selected_attempts),
            "valid": counts["valid"], "scoreable": counts["valid"],
            "not_attempted": counts["not_attempted"],
            "malformed": counts["malformed"], "refusal": counts["refusal"],
            "truncated": counts["truncated"], "infrastructure_error": counts["infrastructure_error"],
        }
    changes, bounds = [], []
    for scenario in dataset["scenarios"]:
        s = scenario["scenario_id"]
        a, b = summaries[left][s], summaries[right][s]
        x, y = a["posterior_error"]["mean"], b["posterior_error"]["mean"]
        if x is not None and y is not None:
            changes.append(y - x)
        bounds.append([b["posterior_bounds"][0] - a["posterior_bounds"][1],
                       b["posterior_bounds"][1] - a["posterior_bounds"][0]])
    scored_index = {o["request_id"]: o for o in observations}
    return {
        "observations": observations, "condition_scores": rows, "scenario_scores": summaries,
        "coverage": coverage,
        "comparison": {
            "left": left, "right": right, "direction": "right minus left posterior loss; positive = larger loss",
            "planned_scenarios": len(bounds), "complete_scenarios": len(changes),
            "complete_scenario_change": mean(changes) if changes else None,
            "full_set_change": mean(changes) if len(changes) == len(bounds) else None,
            "full_set_missing_loss_bounds": [mean(b[0] for b in bounds), mean(b[1] for b in bounds)],
            "planned_observation_pairs": len(pairs),
            "matched_scoreable_observation_pairs": sum(
                scored_index[a["request_id"]]["status"] == scored_index[b["request_id"]]["status"] == "valid"
                for a, b in pairs),
        },
    }


def score_file(raw_path, output, parser=STRICT_PARSER):
    if parser not in {STRICT_PARSER, DIAGNOSTIC_PARSER}:
        raise ValueError("unsupported parser")
    raw = read(raw_path)
    scores = {"schema_version": "cib.scores.v1", "raw_sha256": file_hash(raw_path),
              "run_id": raw["manifest"]["run_id"], "dataset_sha256": digest(raw["dataset"]),
              "scorer_version": SCORER_VERSION if parser == STRICT_PARSER else "updating-diagnostic-v1",
              "parser_version": parser, "scorer_source_sha256": source_hash(),
              "analysis": raw["manifest"]["analysis"], **calculate(raw, parser)}
    if raw["schema_version"] == "cib.real-run.v1":
        strict = calculate(raw, STRICT_PARSER)["coverage"]
        diagnostic = calculate(raw, DIAGNOSTIC_PARSER)["coverage"]
        scores["format_coverage"] = {name: {
            "planned": strict[name]["requested"],
            "normal_completions": strict[name]["normal_completions"],
            "strict_format_compliant": strict[name]["valid"],
            "diagnostic_scoreable": diagnostic[name]["valid"],
            "not_attempted": strict[name]["not_attempted"]} for name in strict}
    write_new(output, scores)
    return scores
