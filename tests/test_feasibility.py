"""Probe configuration and audit checks; no MLX import or accelerator required."""

import copy
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from types import SimpleNamespace

from cib.feasibility import cache_metadata, inventory, model_inputs, sha256, tensor_inventory, validate_config
from cib.records import digest, read
from cib.scoring import parse_probability

CONFIG = Path(__file__).resolve().parents[1] / "configs/feasibility-qwen25-1.5b.json"


class FeasibilityTests(unittest.TestCase):
    def test_source_only_request_payload(self):
        config = read(CONFIG)
        validate_config(config)
        requests = model_inputs(config)
        self.assertEqual(len(requests), 6)
        self.assertNotIn("mlx.core", sys.modules)
        self.assertNotIn("mlx_lm", sys.modules)
        for request in requests:
            self.assertEqual(set(request["input"]), {"messages"})
            self.assertEqual(set(request["input"]["messages"][0]), {"role", "content"})
            serialized = json.dumps(request["input"])
            for secret in ("posterior", "target", "annotations", "checkpoint", "reference", "quantization"):
                self.assertNotIn(secret, serialized)
            if request["stage"] == "pre":
                self.assertNotIn("P(E|H)", serialized)
            else:
                self.assertIn("prior P(H)", serialized)
                self.assertIn("P(E|H)", serialized)

    def test_config_rejects_unimplemented_controls(self):
        for section, field, value in (
            ("generation", "temperature", 0.5), ("generation", "kv_bits", 4),
            ("generation", "retries", 1), ("generation", "constrained_decoding", True),
            ("generation", "max_tokens", 0), ("quantization", "bits", 8),
            ("source", "revision", "main"), ("source", "reference_dtype", "float16"),
            ("budget", "planned_generations_per_deployment", 7),
        ):
            config = copy.deepcopy(read(CONFIG))
            config[section][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_config(config)
        config = read(CONFIG)
        config["requests"].append(config["requests"][0])
        with self.assertRaises(ValueError):
            model_inputs(config)

    def test_saved_real_feasibility_evidence(self):
        evidence = CONFIG.parents[1] / "docs/evidence/m2"
        reference, quantized = (read(evidence / f"{name}.json") for name in ("reference", "quantized"))
        prepared = read(evidence / "prepared.json")
        verification = read(evidence / "verification.json")
        self.assertEqual(prepared["config_sha256"], digest(read(CONFIG)))
        self.assertEqual(verification["config_sha256"], digest(read(CONFIG)))
        self.assertEqual(reference["template_sha256"], quantized["template_sha256"])
        self.assertEqual(reference["eos_token_ids"], quantized["eos_token_ids"])
        self.assertEqual(len(reference["attempts"]), 6)
        self.assertEqual(len(quantized["attempts"]), 6)
        self.assertEqual(reference["parameter_dtype_counts"], {"mlx.core.bfloat16": 338})
        self.assertEqual(len(quantized["quantized_modules"]), 197)
        for name, run in (("reference", reference), ("quantized", quantized)):
            self.assertEqual(sha256(evidence / f"{name}.json"), verification["checked_sha256"][name])
            self.assertEqual(run["prepared_sha256"], sha256(evidence / "prepared.json"))
        for a, b in zip(reference["attempts"], quantized["attempts"]):
            for field in ("request", "input_token_ids", "rendered_input", "input_sha256", "cache_dtypes"):
                self.assertEqual(a[field], b[field])
            self.assertEqual(a["cache_dtypes"], ["mlx.core.bfloat16"])
            for attempt in (a, b):
                self.assertEqual(attempt["status"], "completed")
                self.assertEqual(attempt["finish_reason"], "stop")
                self.assertNotIn("error", attempt)
                self.assertEqual(attempt["format_status"], "malformed")
                self.assertIsNone(attempt["parsed_probability"])
                with self.assertRaises(ValueError):
                    parse_probability(attempt["raw_text"])

    def test_cache_dtype_audit_handles_offset(self):
        cache = SimpleNamespace(state=(SimpleNamespace(dtype="bfloat16"),
                                       SimpleNamespace(dtype="bfloat16"), 173, None))
        self.assertEqual(cache_metadata([cache])["cache_dtypes"], ["bfloat16"])

    def test_artifact_identity_and_header_audit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "model.safetensors"
            header = json.dumps({"weight": {"dtype": "BF16", "shape": [2], "data_offsets": [0, 4]}}).encode()
            content = struct.pack("<Q", len(header)) + header + b"\0\0\0\0"
            path.write_bytes(content)
            self.assertEqual(sha256(path), hashlib.sha256(content).hexdigest())
            self.assertEqual(tensor_inventory(root), {"weight": {"dtype": "BF16", "shape": [2]}})
            original = inventory(root)
            path.write_bytes(content + b"changed")
            self.assertNotEqual(original, inventory(root))


if __name__ == "__main__":
    unittest.main()
