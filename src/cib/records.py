"""Versioned JSON records and canonical content identities."""

import hashlib
import json
from pathlib import Path

SCHEMA = "cib.run.v1"


def encode(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def digest(value):
    return hashlib.sha256(encode(value)).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write_new(path, value):
    # Exclusive creation also prevents score/report commands overwriting raw data.
    with Path(path).open("xb") as stream:
        stream.write(encode(value))


def key(request):
    return tuple(request[field] for field in (
        "scenario_id", "task_version", "condition_id", "label_variant",
        "prompt_variant", "trial_index", "stage",
    ))


def observation_id(request):
    return digest({"deployment_id": request["deployment_id"], "key": key(request),
                   "input": request["input"], "decoding": request["decoding"]})
