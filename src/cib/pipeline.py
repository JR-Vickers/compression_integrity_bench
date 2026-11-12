"""Deterministic response production and audit of the planned observation set."""

from datetime import datetime, timezone
from importlib.resources import files
import platform
import subprocess
import uuid
from pathlib import Path

from .records import SCHEMA, digest, observation_id, read, write_new
from .tasks import cases, load_fixture, render

DEPLOYMENTS = ("fixture-perfect", "fixture-perturbed")
DECODING = {"policy": "scripted", "seed": None, "max_output_tokens": None,
            "reasoning": "not applicable", "retry_limit": 0}


def planned_requests(dataset, deployments):
    result = []
    for deployment in deployments:
        for case in cases(dataset):
            for stage in ("pre", "post"):
                request = {
                    "schema_version": "cib.request.v1",
                    **{name: case[name] for name in (
                        "scenario_id", "cluster_id", "condition_id", "label_variant")},
                    **{name: dataset[name] for name in (
                        "task_version", "prompt_variant", "trial_index")},
                    "stage": stage, "deployment_id": deployment,
                    "input": render(case, stage), "decoding": DECODING.copy(),
                }
                request["input_sha256"] = digest(request["input"])
                request["request_id"] = observation_id(request)
                result.append(request)
    if len({r["request_id"] for r in result}) != len(result):
        raise ValueError("duplicate planned request")
    return result


def git_state():
    def run(*args):
        try:
            outcome = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
        except FileNotFoundError:
            return "unknown"
        return outcome.stdout.strip() if outcome.returncode == 0 else "unknown"
    return {"commit": run("rev-parse", "HEAD"), "working_tree": run("status", "--porcelain")}


def source_hash():
    root = Path(__file__).parent
    return digest({p.name: p.read_text() for p in sorted(root.glob("*.py"))})


def generate(output):
    dataset = load_fixture()
    script = read(files("cib").joinpath("data/provider-v1.json"))
    deployments = {
        name: {"schema_version": "cib.deployment.v1", "deployment_id": name,
               "kind": "synthetic_fixture", "provider": script["provider_version"],
               "script_sha256": digest(script), "checkpoint": "not applicable",
               "quantization": "not applicable", "tokenizer": "not applicable",
               "backend": "deterministic Python script", "precision": "not applicable"}
        for name in DEPLOYMENTS
    }
    requests = planned_requests(dataset, deployments)
    attempts = []
    for request in requests:
        s, v, c, stage = (request[x] for x in (
            "scenario_id", "label_variant", "condition_id", "stage"))
        scripted_key = "/".join((s, v, c, stage))
        value = script["perfect_probabilities"][s][v]["pre" if stage == "pre" else c]
        response = {"text": '{"probability":' + repr(value) + '}',
                    "status": "completed", "stop_reason": "stop", "error": None}
        if request["deployment_id"] == "fixture-perturbed":
            response.update(script["perturbed_overrides"].get(scripted_key, {}))
        attempts.append({"schema_version": "cib.attempt.v1",
                         "request_id": request["request_id"],
                         "deployment_id": request["deployment_id"], "attempt_index": 0,
                         "timestamp": datetime.now(timezone.utc).isoformat(), **response})
    raw = {
        "schema_version": SCHEMA,
        "manifest": {
            "schema_version": "cib.manifest.v1", "run_id": str(uuid.uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "label": script["label"], "split": dataset["split"],
            "code": git_state(), "source_sha256": source_hash(),
            "python": platform.python_version(), "hardware": platform.machine(),
            "dataset_sha256": digest(dataset), "provider_script": script,
            "deployments": deployments, "analysis": dataset["analysis"],
        },
        "dataset": dataset, "requests": requests, "attempts": attempts,
    }
    validate_raw(raw)
    write_new(output, raw)
    return raw


def validate_raw(raw):
    if raw["schema_version"] == "cib.real-run.v1":
        from .runner import validate_real
        return validate_real(raw)
    if raw["schema_version"] != SCHEMA:
        raise ValueError("unsupported raw schema")
    manifest = raw["manifest"]
    dataset = raw["dataset"]
    if dataset != load_fixture():
        raise ValueError("unsupported or changed fixture definition")
    if manifest["dataset_sha256"] != digest(dataset):
        raise ValueError("dataset fingerprint mismatch")
    if manifest["analysis"] != dataset["analysis"]:
        raise ValueError("analysis configuration mismatch")
    deployments = manifest["deployments"]
    if set(deployments) != set(DEPLOYMENTS):
        raise ValueError("unexpected deployment IDs")
    for name, deployment in deployments.items():
        if deployment["deployment_id"] != name or deployment["kind"] != "synthetic_fixture":
            raise ValueError("deployment identity mismatch")
        if deployment["script_sha256"] != digest(manifest["provider_script"]):
            raise ValueError("provider fingerprint mismatch")
    expected = {r["request_id"]: r for r in planned_requests(dataset, deployments)}
    actual = {r["request_id"]: r for r in raw["requests"]}
    if len(actual) != len(raw["requests"]) or actual != expected:
        raise ValueError("requests differ from full planned set, inputs, or pairing identities")
    attempts = raw["attempts"]
    if len(attempts) != len(expected) or {a["request_id"] for a in attempts} != set(expected):
        raise ValueError("attempts do not cover planned requests exactly once")
    for attempt in attempts:
        if attempt["deployment_id"] != expected[attempt["request_id"]]["deployment_id"]:
            raise ValueError("attempt deployment mismatch")
        if attempt["attempt_index"] != 0:
            raise ValueError("fixture protocol permits one attempt only")
        if attempt["status"] not in {"completed", "refusal", "truncated", "infrastructure_error"}:
            raise ValueError("unknown attempt status")
        if attempt["text"] is not None and not isinstance(attempt["text"], str):
            raise ValueError("raw output must be text or null")
        if attempt["status"] == "completed" and attempt["text"] is None:
            raise ValueError("completed attempt must retain text")
