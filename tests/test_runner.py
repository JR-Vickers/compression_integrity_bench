"""Independent backend doubles and saved evidence; no MLX, Metal, or network."""
import copy
from pathlib import Path
import tempfile
import unittest

from cib.records import digest, file_hash, read, write_new
from cib.runner import run, snapshot, import_m2, validate_real, cache_identity
from cib.scoring import (parse_probability, parse_diagnostic, score_file, paired_requests,
                         calculate, DIAGNOSTIC_PARSER)
from cib.report import report_file

ROOT = Path(__file__).resolve().parents[1]
CONFIG = read(ROOT / 'configs/feasibility-qwen25-1.5b.json')
PREPARED = read(ROOT / 'docs/evidence/m2/prepared.json')


class FakeAdapter:
    calls = 0
    mode = 'stop'
    metadata = {'kind': 'test-double-only'}

    def __init__(self, *args):
        pass

    def render(self, payload):
        return {'rendered_input': str(payload), 'input_token_ids': [1, 2]}

    def generate(self, actual, emit):
        FakeAdapter.calls += 1
        emit({'text': '{"probability":0.25}', 'token': 2, 'finish_reason': self.mode})
        if self.mode == 'interrupt':
            raise KeyboardInterrupt()
        if self.mode == 'error':
            raise RuntimeError('scripted infrastructure failure')
        return {'cache_dtypes': ['fake']}


class RunnerTests(unittest.TestCase):
    def setUp(self):
        FakeAdapter.calls = 0
        FakeAdapter.mode = 'stop'

    def test_parser_boundaries(self):
        for text in ('{"probability":0}', ' \n```\n{"probability":1}\n``` \n',
                     '```json\r\n{"probability":0.125}\r\n```'):
            self.assertTrue(0 <= parse_diagnostic(text) <= 1)
        for body in ('{"probability":true}', '{"probability":"0.5"}', '{"probability":-1}',
                     '{"probability":1.1}', '{"probability":NaN}', '{"probability":Infinity}',
                     '{"probability":0.5,"probability":0.5}', '{"probability":0.5,"x":0}',
                     '{"probability":0.5}\n{"probability":0.5}', 'probability 0.5'):
            with self.subTest(body=body), self.assertRaises(ValueError):
                parse_diagnostic('```json\n' + body + '\n```')
        valid = '```json\n{"probability":0.5}\n```'
        for text in (valid,):
            with self.assertRaises(ValueError):
                parse_probability(text)
        for text in ('prefix\n'+valid, valid+'\nextra', valid+'\n'+valid,
                     '```JSON\n{"probability":0.5}\n```', '```python\n{"probability":0.5}\n```',
                     '```json\n{"probability":0.5}', '```json {"probability":0.5}```',
                     '````json\n{"probability":0.5}\n````', None):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_diagnostic(text)

    def test_resume_cache_pairing_and_status_mapping(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertEqual(run(CONFIG, PREPARED, root, 'reference', 2, FakeAdapter), 2)
            first = {p.name: p.read_bytes() for p in root.glob('*.result.json')}
            self.assertEqual(run(CONFIG, PREPARED, root, 'reference', 0, FakeAdapter), 0)
            self.assertEqual(FakeAdapter.calls, 2)
            run(CONFIG, PREPARED, root, 'quantized', 2, FakeAdapter)
            raw = snapshot(root, root/'raw.json')
            self.assertEqual(len(raw['requests']), 48)
            self.assertEqual(len(raw['attempts']), 48)
            self.assertEqual(sum(a['status']=='not_attempted' for a in raw['attempts']), 44)
            for name, content in first.items():
                self.assertEqual((root/name).read_bytes(), content)
            a, b = paired_requests(raw, 'reference', 'quantized')[0]
            actual = {'rendered_input': 'x', 'input_token_ids': [1]}
            baseline = cache_identity(a, actual)
            self.assertNotEqual(baseline, cache_identity(b, actual))
            for field, value in (('trial_index', 2), ('decoding', {'temperature': 1}),
                                 ('input', {'messages': []}), ('deployment_fingerprint', 'different')):
                changed = copy.deepcopy(a)
                changed[field] = value
                self.assertNotEqual(baseline, cache_identity(changed, actual))
            self.assertNotEqual(baseline, cache_identity(a, {'rendered_input':'y','input_token_ids':[2]}))
            changed = copy.deepcopy(raw)
            changed['requests'][0]['trial_index'] = 99
            with self.assertRaises(ValueError):
                validate_real(changed)
            changed = copy.deepcopy(raw)
            changed['requests'][0]['input'] = {'messages': []}
            with self.assertRaises(ValueError):
                paired_requests(changed, 'reference', 'quantized')
            # Completed malformed text is terminal and never reprompted.
            FakeAdapter.mode = 'length'
            run(CONFIG, PREPARED, root, 'reference', 1, FakeAdapter)
            snap = snapshot(root, root/'second.json')
            self.assertEqual(sum(a['status']=='truncated' for a in snap['attempts']), 1)
            changed_config = copy.deepcopy(CONFIG)
            changed_config['generation']['seed'] = 1
            with self.assertRaises(ValueError):
                run(changed_config, PREPARED, root, 'reference', 1, FakeAdapter)

    def test_interruption_preserves_partial_and_fixed_retry(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            FakeAdapter.mode = 'interrupt'
            with self.assertRaises(KeyboardInterrupt):
                run(CONFIG, PREPARED, root, 'reference', 1, FakeAdapter)
            partial = next(root.glob('*.stream.jsonl')).read_bytes()
            interrupted_raw = snapshot(root, root/'interrupted.json')
            self.assertEqual(sum(a['status']=='infrastructure_error' for a in interrupted_raw['attempts']), 1)
            FakeAdapter.mode = 'stop'
            run(CONFIG, PREPARED, root, 'reference', 1, FakeAdapter)
            raw = snapshot(root, root/'raw.json')
            observed = [a for a in raw['attempts'] if a['status']!='not_attempted']
            self.assertEqual([a['attempt_index'] for a in observed], [0, 1])
            self.assertEqual([a['status'] for a in observed], ['infrastructure_error', 'completed'])
            self.assertEqual(observed[0]['text'], '{"probability":0.25}')
            self.assertIn(partial, [p.read_bytes() for p in root.glob('*.stream.jsonl')])
            self.assertEqual(calculate(raw)['coverage']['reference']['attempts'], 2)
            FakeAdapter.mode = 'error'
            run(CONFIG, PREPARED, root, 'quantized', 1, FakeAdapter)
            run(CONFIG, PREPARED, root, 'quantized', 1, FakeAdapter)
            before = len(list(root.glob('*.result.json')))
            # Exhausted request is skipped; the next planned request gets the budget.
            run(CONFIG, PREPARED, root, 'quantized', 1, FakeAdapter)
            self.assertEqual(len(list(root.glob('*.result.json'))), before + 1)
            snapshot(root, root/'retry.json')

    def test_full_resume_terminal_failures_and_attempt_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertEqual(run(CONFIG, PREPARED, root, 'reference', 24, FakeAdapter), 24)
            self.assertEqual(run(CONFIG, PREPARED, root, 'reference', 24, FakeAdapter), 0)
            self.assertEqual(FakeAdapter.calls, 24)
            raw = snapshot(root, root/'raw.json')
            for status in ('refusal', 'truncated', 'infrastructure_error'):
                changed = copy.deepcopy(raw)
                changed['attempts'][0].update(status=status, stop_reason='length' if status=='truncated' else None)
                validate_real(changed)
                self.assertEqual(calculate(changed)['observations'][0]['probability'], None)
            changed = copy.deepcopy(raw)
            a = changed['attempts'][0]
            changed['attempts'].insert(1, {**a, 'attempt_index': 1})
            with self.assertRaises(ValueError):
                validate_real(changed)
            changed = copy.deepcopy(raw)
            changed['attempts'][0]['text'] = 'I cannot answer.'
            validate_real(changed)
            self.assertEqual(calculate(changed)['observations'][0]['status'], 'malformed')

    def test_saved_real_integration_evidence(self):
        evidence = read(ROOT/'docs/evidence/m3/integration.json')
        audit = read(ROOT/'docs/evidence/m3/stream-audit.json')
        verification = read(ROOT/'docs/evidence/m3/verification.json')
        self.assertEqual(len(audit), 12)
        self.assertTrue(all(r['joined_stream_equals_raw'] and r['decoded_tokens_equal_raw']
                            and not r['rendered_contains_fence'] for r in audit))
        self.assertEqual(evidence['deployments']['reference']['parameter_dtype_counts'],
                         {'mlx.core.bfloat16': 338})
        self.assertEqual(evidence['deployments']['quantized']['parameter_dtype_counts'],
                         {'mlx.core.bfloat16': 535, 'mlx.core.uint32': 197})
        self.assertEqual(len(evidence['deployments']['quantized']['quantized_modules']), 197)
        by_deployment = {}
        for entry in evidence['attempts']:
            request, attempt = entry['request'], entry['attempt']
            by_deployment.setdefault(request['deployment_id'], {})[tuple(
                request[f] for f in ('scenario_id', 'label_variant', 'condition_id', 'stage'))] = attempt
            self.assertEqual(attempt['status'], 'completed')
            self.assertEqual(attempt['stop_reason'], 'stop')
            self.assertEqual(attempt['cache_dtypes'], ['mlx.core.bfloat16'])
            with self.assertRaises(ValueError):
                parse_probability(attempt['text'])
            parse_diagnostic(attempt['text'])
            self.assertEqual(attempt['cache_identity'], cache_identity(request, attempt['actual']))
        self.assertEqual(len(by_deployment['reference']), 6)
        self.assertEqual(by_deployment['reference'].keys(), by_deployment['quantized'].keys())
        for identity, attempt in by_deployment['reference'].items():
            self.assertEqual(attempt['actual'], by_deployment['quantized'][identity]['actual'])
        for name in ('integration.json', 'stream-audit.json'):
            path = ROOT/'docs/evidence/m3'/name
            self.assertEqual(file_hash(path), verification['artifact_sha256']['docs/evidence/m3/'+name])

    def test_saved_m2_rescoring_immutable_and_incomplete(self):
        reference = ROOT/'docs/evidence/m2/reference.json'
        quantized = ROOT/'docs/evidence/m2/quantized.json'
        before = [file_hash(p) for p in (reference, quantized)]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = import_m2(CONFIG, PREPARED, reference, quantized, root/'raw.json')
            initial = (root/'raw.json').read_bytes()
            strict = score_file(root/'raw.json', root/'strict.json')
            diagnostic = score_file(root/'raw.json', root/'diagnostic.json', DIAGNOSTIC_PARSER)
            score_file(root/'raw.json', root/'repeat.json', DIAGNOSTIC_PARSER)
            report_file(root/'raw.json', root/'diagnostic.json', root/'report.md')
            for name in ('reference', 'quantized'):
                self.assertEqual(strict['coverage'][name]['scoreable'], 0)
                self.assertEqual(diagnostic['coverage'][name]['scoreable'], 6)
                self.assertEqual(diagnostic['coverage'][name]['not_attempted'], 18)
            self.assertAlmostEqual(next(r['posterior_error'] for r in diagnostic['condition_scores']
                if r['deployment_id']=='quantized' and r['scenario_id']=='balanced' and
                r['condition_id']=='support' and r['label_variant']=='original'), 0.16)
            self.assertIsNone(diagnostic['comparison']['full_set_change'])
            self.assertEqual(diagnostic['comparison']['complete_scenarios'], 0)
            self.assertEqual((root/'raw.json').read_bytes(), initial)
            self.assertEqual((root/'repeat.json').read_bytes(), (root/'diagnostic.json').read_bytes())
            self.assertIn('EXPLORATORY', (root/'report.md').read_text())
            self.assertEqual([file_hash(p) for p in (reference, quantized)], before)
            changed = copy.deepcopy(raw)
            changed['attempts'][0]['cache_identity'] = 'wrong'
            with self.assertRaises(ValueError):
                validate_real(changed)


if __name__ == '__main__':
    unittest.main()
