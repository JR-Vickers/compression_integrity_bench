"""Explicitly configured MLX feasibility probe, separate from the offline runner.

Optional dependencies are imported only after starting an explicit prepare/check.
No scoring, retries, resume, or study comparison is performed here.
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import resource
import struct
import sys
import time
import traceback

from .pipeline import git_state, source_hash
from .records import digest, encode, read, write_new
from .scoring import parse_probability
from .tasks import cases, load_fixture, render


def sha256(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def inventory(directory):
    return {p.name: {"bytes": p.stat().st_size, "sha256": sha256(p)}
            for p in sorted(Path(directory).iterdir()) if p.is_file()}


def tensor_inventory(directory):
    result = {}
    for path in sorted(Path(directory).glob("*.safetensors")):
        with path.open("rb") as stream:
            size = struct.unpack("<Q", stream.read(8))[0]
            header = json.loads(stream.read(size))
        result.update({name: {"dtype": value["dtype"], "shape": value["shape"]}
                       for name, value in header.items() if name != "__metadata__"})
    if not result:
        raise ValueError("no saved tensors")
    return result


def model_inputs(config):
    dataset = load_fixture()
    if config["dataset_version"] != dataset["dataset_version"]:
        raise ValueError("unsupported task version")
    indexed = {(c["scenario_id"], c["label_variant"], c["condition_id"]): c for c in cases(dataset)}
    result = []
    for selection in config["requests"]:
        case = indexed[tuple(selection[k] for k in ("scenario_id", "label_variant", "condition_id"))]
        result.append({**selection, "task_version": dataset["task_version"],
                       "prompt_variant": dataset["prompt_variant"], "trial_index": 0,
                       "cluster_id": case["cluster_id"], "input": render(case, selection["stage"])})
    if len({digest(r) for r in result}) != len(result):
        raise ValueError("duplicate selected task")
    return result


def validate_config(config):
    # This is one deliberately narrow probe, not an unimplemented general runner.
    if config["schema_version"] != "cib.feasibility-config.v1":
        raise ValueError("unsupported config version")
    if config["source"]["reference_dtype"] != "bfloat16":
        raise ValueError("this probe requires BF16 source weights")
    if len(config["source"]["revision"]) != 40:
        raise ValueError("pin a full checkpoint commit")
    g = config["generation"]
    supported = {"temperature": 0.0, "kv_bits": None, "max_kv_size": None,
                 "logits_processors": [], "retries": 0, "constrained_decoding": False}
    if any(g[k] != value for k, value in supported.items()):
        raise ValueError("unsupported generation setting")
    if not 0 < g["max_tokens"] < g["context_limit"]:
        raise ValueError("invalid token budget")
    q = config["quantization"]
    if (q["bits"], q["group_size"], q["mode"], q["nonquantized_dtype"]) != (4, 64, "affine", "bfloat16"):
        raise ValueError("unsupported quantization settings")
    if len(model_inputs(config)) != config["budget"]["planned_generations_per_deployment"]:
        raise ValueError("generation budget mismatch")


def environment(config):
    packages = {name: version(name) for name in (
        "mlx", "mlx-metal", "mlx-lm", "transformers", "tokenizers", "huggingface-hub", "numpy")}
    for name, expected in config["backend"].items():
        if packages[name] != expected:
            raise ValueError(f"expected {name}=={expected}; found {packages[name]}")
    return {"python": platform.python_version(), "platform": platform.platform(),
            "packages": packages, "git": git_state(), "source_sha256": source_hash()}


def memory(mx):
    # Darwin ru_maxrss is bytes; peak RSS includes CPU allocations, MLX tracks its allocator.
    return {"process_peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "mlx_active_bytes": mx.get_active_memory(), "mlx_peak_bytes": mx.get_peak_memory(),
            "mlx_cache_bytes": mx.get_cache_memory()}


def cache_metadata(cache):
    # KVCache.state includes an integer offset in addition to key/value arrays.
    return {"cache_types": sorted({type(layer).__name__ for layer in cache}),
            "cache_dtypes": sorted({str(value.dtype) for layer in cache
                                    for value in layer.state if hasattr(value, "dtype")})}


def prepare(config, artifacts, output):
    import mlx.core as mx
    from huggingface_hub import HfApi, snapshot_download
    from mlx_lm import convert

    result = {"environment": environment(config), "source": config["source"]}
    source = config["source"]
    info = HfApi(token=False).model_info(source["repo_id"], revision=source["revision"], files_metadata=True)
    if info.sha != source["revision"] or info.gated:
        raise ValueError("source is not the declared freely available revision")
    source_path = Path(snapshot_download(
        source["repo_id"], revision=source["revision"], token=False,
        cache_dir=str(artifacts / "hub"),
        allow_patterns=["*.safetensors", "*.json", "*.txt", "*.jinja", "LICENSE", "README.md"],
    )).resolve()
    tensors = tensor_inventory(source_path)
    if {v["dtype"] for v in tensors.values()} != {"BF16"}:
        raise ValueError("reference tensors are not exclusively unquantized BF16")
    if any(k in read(source_path / "config.json") for k in ("quantization", "quantization_config")):
        raise ValueError("source checkpoint is already quantized")
    files = inventory(source_path)
    for sibling in info.siblings:
        if sibling.lfs and sibling.rfilename in files:
            if sibling.lfs.sha256 != files[sibling.rfilename]["sha256"]:
                raise ValueError("download differs from official LFS SHA-256")
    write_new(output / "source.json", {"path": str(source_path), "files": files,
                                       "hub_revision": info.sha, "gated": info.gated})
    quantized = (artifacts / "affine-4bit-g64").resolve()
    start = time.perf_counter()
    convert(str(source_path), mlx_path=str(quantized), quantize=True,
            q_group_size=64, q_bits=4, q_mode="affine", dtype="bfloat16",
            trust_remote_code=False)
    mx.synchronize()
    result.update({"reference": {"path": str(source_path), "files": files},
                   "quantized": {"path": str(quantized), "files": inventory(quantized)},
                   "quantization_seconds": time.perf_counter() - start,
                   "quantization_config": read(quantized / "config.json")["quantization"],
                   "tensor_dtype_counts": {"reference": dict(Counter(v["dtype"] for v in tensors.values())),
                                           "quantized": dict(Counter(v["dtype"] for v in tensor_inventory(quantized).values()))},
                   "memory": memory(mx)})
    write_new(output / "prepared.json", {"schema_version": "cib.prepared.v1",
                                         "config_sha256": digest(config), **result})
    return result


def check(config, prepared_path, deployment, output):
    # After preparation, generation must work without network access.
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    import mlx.core as mx
    from mlx.utils import tree_flatten
    from mlx_lm import stream_generate
    from mlx_lm.models.cache import make_prompt_cache
    from mlx_lm.sample_utils import make_sampler
    from mlx_lm.utils import load_model, load_tokenizer

    prepared = read(prepared_path)
    if prepared["schema_version"] != "cib.prepared.v1" or prepared["config_sha256"] != digest(config):
        raise ValueError("preparation/config identity mismatch")
    result = {"environment": environment(config), "deployment": deployment,
              "prepared_sha256": sha256(prepared_path), "attempts": []}
    source_path = Path(prepared["reference"]["path"])
    model_path = Path(prepared[deployment]["path"])
    for name in {"reference", deployment}:
        if inventory(prepared[name]["path"]) != prepared[name]["files"]:
            raise ValueError(f"{name} artifact fingerprint changed")
    mx.set_default_device(mx.gpu)
    mx.random.seed(config["generation"]["seed"])
    mx.reset_peak_memory()
    start = time.perf_counter()
    model, model_config = load_model(model_path, lazy=False, trust_remote_code=False)
    # Both deployments deliberately use the exact same pinned source tokenizer and EOS IDs.
    eos = read(source_path / "generation_config.json")["eos_token_id"]
    tokenizer = load_tokenizer(source_path, {"trust_remote_code": False, "local_files_only": True}, eos_token_ids=eos)
    mx.synchronize()
    result.update({"load_seconds": time.perf_counter() - start, "load_memory": memory(mx),
                   "device": str(mx.default_device()), "model_config": model_config,
                   "tokenizer_path": str(source_path), "template_sha256": digest(tokenizer.chat_template),
                   "chat_template": tokenizer.chat_template, "eos_token_ids": sorted(tokenizer.eos_token_ids),
                   "parameter_dtype_counts": dict(Counter(str(v.dtype) for _, v in tree_flatten(model.parameters()))),
                   "quantized_modules": [name for name, module in model.named_modules() if hasattr(module, "bits")]})
    write_new(output / "loaded.json", {k: v for k, v in result.items() if k != "attempts"})
    g = config["generation"]
    for index, request in enumerate(model_inputs(config)):
        rendered = tokenizer.apply_chat_template(request["input"]["messages"], tokenize=False, add_generation_prompt=True)
        tokens = tokenizer.encode(rendered, add_special_tokens=False)
        if len(tokens) + g["max_tokens"] > g["context_limit"]:
            raise ValueError("input plus output budget exceeds declared context limit")
        attempt = {"schema_version": "cib.feasibility-attempt.v1", "deployment": deployment,
                   "request": request, "rendered_input": rendered, "input_token_ids": tokens,
                   "input_sha256": digest(request["input"]), "attempt_index": 0,
                   "started_at": datetime.now(timezone.utc).isoformat(), "raw_text": "",
                   "status": "infrastructure_error", "finish_reason": None}
        # Save the exact request before inference, and persist every streamed segment.
        write_new(output / f"request-{index}.json", attempt)
        cache = make_prompt_cache(model)
        start = time.perf_counter()
        try:
            with (output / f"stream-{index}.jsonl").open("xb") as stream:
                for response in stream_generate(
                    model, tokenizer, prompt=tokens, max_tokens=g["max_tokens"],
                    sampler=make_sampler(temp=g["temperature"]), logits_processors=[],
                    prompt_cache=cache, kv_bits=None, max_kv_size=None,
                    prefill_step_size=g["prefill_step_size"],
                ):
                    event = {k: getattr(response, k) for k in (
                        "text", "token", "finish_reason", "prompt_tokens", "generation_tokens",
                        "prompt_tps", "generation_tps", "peak_memory")}
                    stream.write(encode(event).replace(b"\n", b"") + b"\n")
                    stream.flush()
                    attempt["raw_text"] += response.text
                    attempt["finish_reason"] = response.finish_reason
                    attempt["generation_tokens"] = response.generation_tokens
            mx.synchronize()
            attempt["status"] = "truncated" if attempt["finish_reason"] == "length" else "completed"
            try:
                attempt["parsed_probability"] = parse_probability(attempt["raw_text"])
                attempt["format_status"] = "valid"
            except ValueError:
                attempt["parsed_probability"] = None
                attempt["format_status"] = "malformed"
            attempt.update(cache_metadata(cache))
        except Exception:
            attempt["status"] = "infrastructure_error"
            attempt["error"] = traceback.format_exc()
        attempt.update(seconds=time.perf_counter() - start, memory=memory(mx))
        write_new(output / f"attempt-{index}.json", attempt)
        result["attempts"].append(attempt)
        print(f"{deployment} {index}: {attempt['status']} {attempt['raw_text']!r}", flush=True)
    result["final_memory"] = memory(mx)
    write_new(output / "checked.json", {"schema_version": "cib.feasibility-check.v1", **result})
    if any("error" in attempt for attempt in result["attempts"]):
        raise RuntimeError("probe errors retained in checked.json")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "check"))
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--artifacts", type=Path)
    parser.add_argument("--prepared", type=Path)
    parser.add_argument("--deployment", choices=("reference", "quantized"))
    args = parser.parse_args()
    config = read(args.config)
    validate_config(config)
    if args.command == "prepare" and args.artifacts is None:
        parser.error("prepare requires --artifacts")
    if args.command == "check" and (args.prepared is None or args.deployment is None):
        parser.error("check requires --prepared and --deployment")
    args.output.mkdir(parents=True, exist_ok=False)
    write_new(args.output / "invocation.json", {
        "schema_version": "cib.feasibility-invocation.v1", "argv": sys.argv,
        "config": config, "config_sha256": digest(config),
        "started_at": datetime.now(timezone.utc).isoformat(), "planned_requests": model_inputs(config),
    })
    try:
        if args.command == "prepare":
            prepare(config, args.artifacts, args.output)
        else:
            check(config, args.prepared, args.deployment, args.output)
    except Exception:
        write_new(args.output / "failure.json", {"error": traceback.format_exc()})
        raise


if __name__ == "__main__":
    main()
