"""Offline checks with analytic values independent of scripted provider responses."""

import copy
from fractions import Fraction
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cib.pipeline import generate, validate_raw
from cib.records import file_hash, read
from cib.report import report_file
from cib.scoring import calculate, paired_requests, parse_probability, score_attempt, score_file
from cib.tasks import cases, load_fixture, posterior


class NumericalTests(unittest.TestCase):
    def test_independent_targets(self):
        # Bayes by odds: 1 * 4 = 4 -> 4/5; (1/4) * 4 = 1 -> 1/2.
        self.assertEqual(posterior("1/2", "4/5", "1/5"), Fraction(4, 5))
        self.assertEqual(posterior("1/5", "4/5", "1/5"), Fraction(1, 2))
        # Prior odds 1/4, likelihood ratio 1/4 -> odds 1/16 -> 1/17.
        self.assertEqual(posterior("1/5", "1/5", "4/5"), Fraction(1, 17))
        for prior in ("0", "1/5", "7/10", "1"):
            self.assertEqual(posterior(prior, "2/5", "2/5"), Fraction(prior))
            for a, b in (("4/5", "1/5"), ("1/3", "2/3")):
                self.assertEqual(posterior(1 - Fraction(prior), b, a),
                                 1 - posterior(prior, a, b))
        self.assertEqual(posterior("1/2", "1", "0"), 1)
        self.assertEqual(posterior("1/2", "0", "1"), 0)
        for args in (("1/2", "0", "0"), ("1", "0", "1"), ("-1", "1", "1"),
                     ("1/2", "2", "0")):
            with self.assertRaises(ValueError):
                posterior(*args)

    def test_parser_contract(self):
        for value in (0, 0.5, 1):
            self.assertEqual(parse_probability(json.dumps({"probability": value})), value)
        invalid = ['{"probability": true}', '{"probability":"0.5"}', '{"probability":1.01}',
                   '{"probability":-0.1}', '{"probability":NaN}', '{"probability":Infinity}',
                   '{"probability":1e999}', '{"probability":0.5,"extra":1}', '0.5', 'null',
                   '[]', '{"probability":0.2,"probability":0.5}', 'answer: 0.5', '',
                   '{"probability":0.5} trailing', '{"probability":null}']
        for text in invalid:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_probability(text)
        for status in ("refusal", "truncated", "infrastructure_error"):
            result = score_attempt({"status": status, "text": '{"probability":0.5}'})
            self.assertEqual(result, {"status": status, "probability": None})


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.raw_path = self.root / "raw.json"
        self.raw = generate(self.raw_path)

    def test_full_plan_requests_and_targets_separate(self):
        self.assertEqual(len(self.raw["requests"]), 48)
        self.assertEqual(len(self.raw["attempts"]), 48)
        self.assertEqual(len(list(cases(load_fixture()))), 12)
        pairs = paired_requests(self.raw, "fixture-perfect", "fixture-perturbed")
        self.assertEqual(len(pairs), 24)
        for a, b in pairs:
            self.assertEqual(a["input"], b["input"])
            self.assertNotEqual(a["request_id"], b["request_id"])
            # Serialized provider input has a positive allowlist, not just a blacklist.
            self.assertEqual(set(a["input"]), {"messages"})
            self.assertEqual(set(a["input"]["messages"][0]), {"role", "content"})
            text = json.dumps(a["input"])
            for forbidden in ("annotations", "posterior", "target", "scorer", "fixture-perfect"):
                self.assertNotIn(forbidden, text)
            if a["stage"] == "pre":
                self.assertNotIn("P(E|H)", text)
            else:
                self.assertIn("prior P(H)", text)
                self.assertIn("P(E|H)", text)
                self.assertNotIn("earlier answer", text)

    def test_pairing_and_identity_rejection(self):
        for field, value in (("deployment_id", "wrong"), ("scenario_id", "other"),
                             ("condition_id", "other"), ("task_version", "other"),
                             ("prompt_variant", "other"), ("trial_index", 3),
                             ("label_variant", "other")):
            changed = copy.deepcopy(self.raw)
            changed["requests"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_raw(changed)
            with self.subTest(pairing=field), self.assertRaises(ValueError):
                paired_requests(changed, "fixture-perfect", "fixture-perturbed")
        for left, right in (("fixture-perfect", "fixture-perfect"), ("unknown", "fixture-perturbed")):
            with self.assertRaises(ValueError):
                paired_requests(self.raw, left, right)
        changed = copy.deepcopy(self.raw)
        changed["attempts"][0]["deployment_id"] = "fixture-perturbed"
        with self.assertRaises(ValueError):
            calculate(changed)
        changed = copy.deepcopy(self.raw)
        changed["requests"].pop()
        with self.assertRaises(ValueError):
            calculate(changed)
        changed = copy.deepcopy(self.raw)
        changed["requests"][0]["input"]["messages"][0]["content"] += "changed"
        with self.assertRaises(ValueError):
            paired_requests(changed, "fixture-perfect", "fixture-perturbed")
        changed = copy.deepcopy(self.raw)
        changed["attempts"].append(changed["attempts"][0])
        with self.assertRaises(ValueError):
            calculate(changed)

    def test_metrics_missingness_and_independent_aggregation(self):
        result = calculate(self.raw)
        left, right = "fixture-perfect", "fixture-perturbed"
        for summary in result["scenario_scores"][left].values():
            for metric in ("posterior_error", "prior_error", "update_error", "uninformative_drift"):
                self.assertAlmostEqual(summary[metric]["mean"], 0)
        balanced = result["scenario_scores"][right]["balanced"]
        self.assertAlmostEqual(balanced["posterior_error"]["mean"], (0.15 + 0.1) / 6)
        self.assertAlmostEqual(balanced["uninformative_drift"]["mean"], 0.1 / 2)
        rare = result["scenario_scores"][right]["rare"]
        self.assertIsNone(rare["posterior_error"]["mean"])
        self.assertEqual(rare["posterior_error"]["scoreable"], 2)
        self.assertEqual(rare["posterior_error"]["planned"], 6)
        self.assertAlmostEqual(rare["prior_error"]["mean"], 0.1 / 6)
        selected = next(r for r in result["condition_scores"] if r["deployment_id"] == right
                        and r["scenario_id"] == "rare" and r["label_variant"] == "original"
                        and r["condition_id"] == "support")
        self.assertAlmostEqual(selected["prior_error"], 0.1)
        self.assertAlmostEqual(selected["update_error"], 0.1)
        self.assertAlmostEqual(selected["posterior_error"], 0)
        coverage = result["coverage"][right]
        self.assertEqual(coverage["requested"], 24)
        self.assertEqual(coverage["completed_generations"], 23)
        self.assertEqual(coverage["valid"], 20)
        for failure in ("malformed", "refusal", "truncated", "infrastructure_error"):
            self.assertEqual(coverage[failure], 1)
        comparison = result["comparison"]
        self.assertEqual(comparison["matched_scoreable_observation_pairs"], 20)
        self.assertEqual(comparison["complete_scenarios"], 1)
        self.assertIsNone(comparison["full_set_change"])
        self.assertAlmostEqual(comparison["complete_scenario_change"], 0.25 / 6)
        # Equal scenario weights: observed balanced loss .25/6; rare loss in [0,4/6].
        lo, hi = comparison["full_set_missing_loss_bounds"]
        self.assertAlmostEqual(lo, 0.25 / 12)
        self.assertAlmostEqual(hi, (0.25 + 4) / 12)
        # Complete missing responses with target-perfect and maximally wrong probabilities.
        for replacement, expected in ((0, lo), (1, hi)):
            completed = copy.deepcopy(self.raw)
            requests = {r["request_id"]: r for r in completed["requests"]}
            targets = {(c["scenario_id"], c["label_variant"], c["condition_id"]): c["posterior"]
                       for c in cases(completed["dataset"])}
            for attempt in completed["attempts"]:
                if score_attempt(attempt)["status"] != "valid":
                    request = requests[attempt["request_id"]]
                    target = targets[(request["scenario_id"], request["label_variant"], request["condition_id"])]
                    # For [0,1] probabilities, max attainable absolute loss may be <1.
                    # Loss=1 is conservative rather than necessarily attainable.
                    attempt.update(status="completed", text=json.dumps({"probability": target if replacement == 0 else 1 - round(target)}))
            change = calculate(completed)["comparison"]["full_set_change"]
            self.assertGreaterEqual(change + 1e-12, lo)
            self.assertLessEqual(change, hi + 1e-12)
            if replacement == 0:
                self.assertAlmostEqual(change, expected)

    def test_always_prior_baseline(self):
        raw = copy.deepcopy(self.raw)
        requests = {r["request_id"]: r for r in raw["requests"]}
        priors = {(c["scenario_id"], c["label_variant"]): c["prior"] for c in cases(raw["dataset"])}
        for attempt in raw["attempts"]:
            request = requests[attempt["request_id"]]
            value = priors[(request["scenario_id"], request["label_variant"])]
            attempt.update(status="completed", text=json.dumps({"probability": value}))
        result = calculate(raw)
        for deployment in ("fixture-perfect", "fixture-perturbed"):
            balanced = result["scenario_scores"][deployment]["balanced"]
            self.assertAlmostEqual(balanced["posterior_error"]["mean"], 0.2)
            self.assertEqual(balanced["prior_error"]["mean"], 0)
            self.assertEqual(balanced["uninformative_drift"]["mean"], 0)
        self.assertAlmostEqual(result["comparison"]["full_set_change"], 0)

    def test_all_missing_and_missing_pre_stage(self):
        raw = copy.deepcopy(self.raw)
        for attempt in raw["attempts"]:
            attempt.update(status="infrastructure_error", text=None)
        result = calculate(raw)
        comparison = result["comparison"]
        self.assertEqual(comparison["full_set_missing_loss_bounds"], [-1, 1])
        self.assertEqual(comparison["complete_scenarios"], 0)
        self.assertIsNone(comparison["complete_scenario_change"])
        self.assertIsNone(comparison["full_set_change"])
        for observation in result["observations"]:
            self.assertIsNone(observation["probability"])
        raw = copy.deepcopy(self.raw)
        raw["attempts"][0].update(status="truncated", text="")
        result = calculate(raw)
        case = next(r for r in result["condition_scores"]
                    if r["pre_request_id"] == raw["attempts"][0]["request_id"])
        self.assertIsNone(case["prior_error"])
        self.assertIsNone(case["update_error"])
        self.assertAlmostEqual(case["posterior_error"], 0)

    def test_saved_rescoring_and_report_immutability(self):
        before = self.raw_path.read_bytes()
        scores1, scores2 = self.root / "scores1.json", self.root / "scores2.json"
        # Saved scoring/reporting cannot invoke the response producer.
        with patch("cib.pipeline.generate", side_effect=AssertionError("inference forbidden")):
            score_file(self.raw_path, scores1)
            score_file(self.raw_path, scores2)
            report = self.root / "report.md"
            report_file(self.raw_path, scores1, report)
            score_bytes = scores1.read_bytes()
            report_file(self.raw_path, scores1, self.root / "report2.md")
        self.assertEqual(scores1.read_bytes(), scores2.read_bytes())
        self.assertEqual(scores1.read_bytes(), score_bytes)
        self.assertEqual(self.raw_path.read_bytes(), before)
        self.assertEqual(read(scores1)["raw_sha256"], file_hash(self.raw_path))
        self.assertEqual(report.read_bytes(), (self.root / "report2.md").read_bytes())
        text = report.read_text()
        self.assertIn("SYNTHETIC DEVELOPMENT FIXTURES", text)
        self.assertIn("no claims about compression effects", text)
        self.assertIn("infrastructure_error", text)
        self.assertIn("&quot;status&quot;", text)
        for action in (lambda: generate(self.raw_path), lambda: score_file(self.raw_path, scores1),
                       lambda: report_file(self.raw_path, scores1, self.raw_path)):
            with self.assertRaises(FileExistsError):
                action()
        self.assertEqual(self.raw_path.read_bytes(), before)
        other = self.root / "other.json"
        generate(other)
        with self.assertRaises(ValueError):
            report_file(other, scores1, self.root / "bad.md")


if __name__ == "__main__":
    unittest.main()
