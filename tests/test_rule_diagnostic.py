"""Offline synthetic fixtures only; independent numerical and failure examples."""
import copy
from fractions import Fraction as F
from pathlib import Path
import sys
import tempfile
import unittest

from cib.records import read, file_hash
from cib.runner import run, snapshot, new_run
from cib.rule_diagnostic import load, planned, target, calculate, score, report
from test_runner import FakeAdapter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from verify_m4c import instrument_audit
CONFIG=read(ROOT/'configs/reference-check-qwen25-7b.json')
PREPARED=read(ROOT/'docs/evidence/m4c/prepared.json')


class RuleDiagnosticTests(unittest.TestCase):
    def setUp(self):
        FakeAdapter.calls=0; FakeAdapter.mode='stop'

    def test_independent_targets_prompts_freshness_and_allocation(self):
        ds=load(); rr=planned(ds,('reference',))
        expected=[F(7,10),F(7,20),F(1,2),F(42,127),F(14,79),F(13,20),F(2,3),F(1,5),F(1,2),F(221,242),F(1,7),F(7,10)]
        self.assertEqual([target(s) for s in ds['scenarios']],expected)
        self.assertEqual(len(instrument_audit(rr)),12)
        self.assertEqual(ds['diagnostic_protocol'],read(ROOT/'configs/rule-diagnostic-v1.json'))
        self.assertEqual(len(rr),42); self.assertEqual(len({r['scenario_id'] for r in rr}),12)
        self.assertEqual(sum(r['trial_index']==1 for r in rr),6)
        self.assertTrue(all(r['stage']=='evaluation' for r in rr))
        old=read(ROOT/'src/cib/data/diagnostic-v1.json')
        old_values=set()
        for s in old['scenarios']:
            for c in s['conditions']:
                p,a,b=map(F,(s['prior'],c['likelihood_h'],c['likelihood_not_h']))
                old_values.update([(p,a,b),(1-p,b,a)])
        for s in ds['scenarios']:
            self.assertNotIn(tuple(F(s[k]) for k in ('prior','likelihood_h','likelihood_not_h')),old_values)
        for r in rr[36:]:
            original=next(q for q in rr[:36] if q['scenario_id']==r['scenario_id'] and q['prompt_variant']==r['prompt_variant'])
            self.assertEqual(r['input'],original['input'])
            self.assertNotEqual(r['request_id'],original['request_id'])
        with self.assertRaises(ValueError):planned(ds,('reference','quantized'))
        changed=copy.deepcopy(PREPARED); changed['preparation_seconds']=0
        with self.assertRaises(ValueError):new_run(CONFIG,changed,ds)

    def test_missingness_pairing_regeneration_and_failures(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            run(CONFIG,PREPARED,root,'reference',1,FakeAdapter,load())
            raw=snapshot(root,root/'partial.json'); s=calculate(raw)
            self.assertEqual(s['coverage']['primary_scoreable'],1)
            self.assertIsNone(s['groups']['A']['mean_absolute_error'])
            self.assertIsNone(s['paired_differences']['B-A']['mean'])
            self.assertFalse(s['groups']['A']['screen_pass'])
            run(CONFIG,PREPARED,root,'reference',42,FakeAdapter,load())
            raw=snapshot(root,root/'raw.json'); original=file_hash(root/'raw.json')
            s=score(root/'raw.json',root/'scores.json'); score(root/'raw.json',root/'repeat.json')
            report(root/'raw.json',root/'scores.json',root/'report.md'); report(root/'raw.json',root/'scores.json',root/'report2.md')
            self.assertEqual((root/'scores.json').read_bytes(),(root/'repeat.json').read_bytes())
            self.assertEqual((root/'report.md').read_bytes(),(root/'report2.md').read_bytes())
            self.assertEqual(file_hash(root/'raw.json'),original)
            self.assertEqual(s['coverage']['primary_scoreable'],42)
            self.assertEqual(s['independent_scenarios'],12)
            self.assertAlmostEqual(s['rows'][0]['absolute_error'],.45)
            self.assertEqual(s['paired_differences']['B-A']['mean'],0)
            self.assertTrue(all(r['probability_difference']==0 for r in s['repeats']))
            self.assertEqual(run(CONFIG,PREPARED,root,'reference',42,FakeAdapter,load()),0)
            for status in ('truncated','refusal','infrastructure_error','completed'):
                changed=copy.deepcopy(raw); a=changed['attempts'][0]
                a.update(status=status,stop_reason='length' if status=='truncated' else 'stop' if status=='completed' else None,text='invalid')
                scored=calculate(changed)
                self.assertIsNone(scored['rows'][0]['absolute_error'])
                self.assertIsNone(scored['groups']['A']['mean_absolute_error'])
                self.assertIsNone(scored['paired_differences']['B-A']['mean'])
                self.assertEqual(scored['observations'][a['request_id']]['status'],'malformed' if status=='completed' else status)

    def test_saved_measured_evidence_and_independent_losses(self):
        evidence=read(ROOT/'docs/evidence/m4c/observations.json')
        scores=read(ROOT/'docs/evidence/m4c/summary.json')
        verification=read(ROOT/'docs/evidence/m4c/verification.json')
        from cib.scoring import parse_diagnostic, parse_probability
        attempts={r['request']['request_id']:r for r in evidence['observations']}
        self.assertEqual(len(attempts),42)
        self.assertEqual(scores['attempt_count'],42)
        self.assertEqual(scores['recommendation'],'park')
        self.assertEqual(scores['coverage']['strict_compliant'],0)
        expected={'A':0.0910524349704787,'B':0.09317427631395146,'C':0.18463727287942602}
        for form,loss in expected.items():
            self.assertAlmostEqual(scores['groups'][form]['mean_absolute_error'],loss)
            rows=[r for r in scores['rows'] if r['form']==form]
            losses=[]
            for row in rows:
                a=attempts[row['request_id']]['attempt']
                self.assertEqual(a['status'],'completed')
                self.assertEqual(a['cache_dtypes'],['mlx.core.bfloat16'])
                q=parse_diagnostic(a['text'])
                with self.assertRaises(ValueError):parse_probability(a['text'])
                independent=float(F(row['exact_target']))
                losses.append(abs(q-independent))
                self.assertEqual(row['absolute_error'],losses[-1])
            self.assertAlmostEqual(sum(losses)/12,loss)
        self.assertEqual(verification['raw_sha256'],evidence['raw_sha256'])
        self.assertTrue(verification['run_files_unchanged'])
        self.assertTrue(verification['historical_files_unchanged'])
        self.assertEqual(evidence['loaded_metadata']['parameter_dtype_counts'],{'mlx.core.bfloat16':339})
        self.assertEqual(evidence['loaded_metadata']['quantized_modules'],[])

    def test_global_attempt_ceiling_including_retries(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); FakeAdapter.mode='error'
            self.assertEqual(run(CONFIG,PREPARED,root,'reference',42,FakeAdapter,load()),42)
            with self.assertRaisesRegex(ValueError,'ceiling'):
                run(CONFIG,PREPARED,root,'reference',100,FakeAdapter,load())
            self.assertEqual(FakeAdapter.calls,60)
            raw=snapshot(root,root/'raw.json')
            s=calculate(raw)
            self.assertEqual(s['attempt_count'],60)
            self.assertEqual(s['coverage']['primary_scoreable'],0)
            self.assertEqual(s['recommendation'],'park')


if __name__=='__main__':unittest.main()
