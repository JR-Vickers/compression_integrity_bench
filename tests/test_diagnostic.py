"""Offline M4b target, wording, grouping, missingness and budget regressions."""
from pathlib import Path
from fractions import Fraction as F
import tempfile
import re
import unittest
from cib.diagnostic import load_diagnostic,planned,calculate,score
from cib.records import read,file_hash,write_new,key
from cib.runner import run,snapshot,new_run,missing
from cib.diagnostic_report import report
from cib.larger_reference import validate_config as validate_larger
from test_runner import CONFIG,PREPARED,FakeAdapter


class DiagnosticTests(unittest.TestCase):
    def test_targets_wording_and_allocation(self):
        ds=load_diagnostic();rr=planned(ds,('reference','quantized'))
        self.assertEqual(len(rr),180)
        self.assertEqual(ds['diagnostic_protocol'],read(Path(__file__).resolve().parents[1]/'configs/diagnostic-v1.json'))
        self.assertEqual(len(planned(load_diagnostic(True),('reference',))),60)
        for d in ('reference','quantized'):
            selected=[r for r in rr if r['deployment_id']==d]
            self.assertEqual(len(selected),90)
            self.assertEqual(sum(r['stage']=='control' for r in selected),12)
            self.assertEqual(sum(r['trial_index']==1 for r in selected),6)
            for r in selected:
                self.assertEqual(set(r['input']),{'messages'})
                self.assertEqual(len(r['input']['messages']),1)
                self.assertNotIn('target',str(r['input']))
        # All original controls are exactly the audited message, not reverse conditionals.
        old=read(Path(__file__).resolve().parents[1]/'src/cib/data/updating-pilot-v1.json')
        for i in range(4):
            original=next(r for r in rr if r['scenario_id']==f'likelihood-l{i+1}' and r['prompt_variant']=='original')
            self.assertEqual(original['input']['messages'][0]['content'],old['controls'][4+i]['prompt']+' Return only a JSON object with exactly the key "probability" and a numeric value in [0,1].')
        for trial in [r for r in rr if r['trial_index']==1]:
            original=next(r for r in rr if r['trial_index']==0 and r['deployment_id']==trial['deployment_id'] and key(r)[:5]==key(trial)[:5] and r['stage']==trial['stage'])
            self.assertEqual(trial['input'],original['input'])
            self.assertNotEqual(trial['request_id'],original['request_id'])

    def test_rendered_wording_equivalence(self):
        rr=planned(load_diagnostic(),('reference',))
        # Recover supplied facts independently from each representation, not scorer targets.
        for r in rr:
            if r['stage']!='post' or r['trial_index']!=0:continue
            text=r['input']['messages'][0]['content'];w=r['prompt_variant']
            if w=='original':
                p=F(re.search(r'prior P\(H\) is ([0-9.]+)\.',text)[1])
                a=F(re.search(r'P\(E\|H\)=([0-9.]+);',text)[1])
                b=F(re.search(r'P\(E\|not H\)=([0-9.]+)\.',text)[1])
            elif w=='mathematical':
                p=F(re.search(r'P\(H\)=([0-9.]+) and',text)[1])
                a=F(re.search(r'P\(E\|H\)=([0-9.]+) and',text)[1])
                b=F(re.search(r'P\(E\|not H\)=([0-9.]+)\.',text)[1])
            else:
                p=F(int(re.search(r'(\d+) out of every 100',text)[1]),100)
                likes=re.findall(r'Among packets from [AB], (\d+) out of 100',text)
                a,b=[F(int(x),100) for x in likes]
            expected_p={'d1':F(1,10),'d2':F(1,2),'d3':F(3,4)}[r['scenario_id']]
            if r['label_variant']=='swapped':expected_p=1-expected_p
            self.assertEqual(p,expected_p)
            if r['condition_id']=='irrelevant':self.assertEqual(a,b)
            else:self.assertEqual(a/b,F(4) if r['label_variant']=='original' else F(1,4))
            target=p*a/(p*a+(1-p)*b)
            if r['condition_id']=='irrelevant':self.assertEqual(target,p)

    def test_independent_targets_and_incomplete_summaries(self):
        raw=new_run(CONFIG,PREPARED,load_diagnostic())
        raw['attempts']=[missing(r) for r in raw['requests']]
        s=calculate(raw)
        self.assertIsNone(s['deployments']['reference']['groups']['natural']['metrics']['posterior_error']['mean'])
        expected={'d1':4/13,'d2':4/5,'d3':12/13}
        for row in s['deployments']['reference']['condition_rows']:
            p={'d1':.1,'d2':.5,'d3':.75}[row['scenario_id']]
            if row['label_variant']=='swapped':p=1-p
            target=p if row['condition_id']=='irrelevant' else expected[row['scenario_id']]
            if row['condition_id']=='relevant' and row['label_variant']=='swapped':target=1-target
            self.assertAlmostEqual(row['posterior'],target)
            self.assertIsNone(row['posterior_error'])
        for c in s['deployments']['reference']['controls']:
            self.assertEqual(c['target'],{'l1':.1,'l2':.25,'l3':.5,'l4':.75}[c['control_id']])
        for g in s['deployments']['reference']['groups'].values():
            self.assertEqual(g['coverage']['planned'],28)
            self.assertFalse(s['deployments']['reference']['suitability_pass'])
            self.assertAlmostEqual(g['unchanged_prior_posterior_baseline'],(4/13-.1+.8-.5+12/13-.75)/6)

    def test_larger_reference_scope_and_no_quantization(self):
        root=Path(__file__).resolve().parents[1]
        config=read(root/'configs/reference-check-qwen25-7b.json')
        validate_larger(config)
        with self.assertRaises(ValueError):
            validate_larger({**config,'quantization':{'bits':4}})
        small=planned(load_diagnostic(),('reference',))
        large=planned(load_diagnostic(True),('reference',))
        self.assertEqual(len(large),60)
        self.assertEqual(sum(r['trial_index']==1 for r in large),4)
        for r in large:
            if r['trial_index']!=0:continue
            original=next(x for x in small if key(x)==key(r))
            self.assertEqual(r['input'],original['input'])
            self.assertEqual(r['decoding'],original['decoding'])
        self.assertEqual(load_diagnostic()['diagnostic_protocol']['suitability_criteria'],config['criteria'])

    def test_audited_controls_and_measured_reference_evidence(self):
        root=Path(__file__).resolve().parents[1]/'docs/evidence/m4b'
        audit=read(root/'audit.json')
        self.assertEqual(audit['defects_found'],[])
        self.assertEqual(audit['independently_checked_main_rows'],144)
        self.assertEqual(audit['paired_requests'],172)
        self.assertEqual(len(audit['control_audit']),4)
        for c,expected in zip(audit['control_audit'],[F(1,10),F(1,4),F(1,2),F(3,4)]):
            self.assertEqual(F(c['independent_target']),expected)
            for v in c['deployments'].values():
                text=v['request']['input']['messages'][0]['content']
                self.assertIn('Report P(signal|H), not P(H|signal).',text)
                self.assertEqual(F(re.search(r'given H is ([0-9.]+);',text)[1]),expected)
                from cib.scoring import parse_diagnostic
                value=parse_diagnostic(v['attempt']['text'])
                self.assertAlmostEqual(abs(value-float(expected)),v['independent_absolute_error'])
                self.assertFalse(v['correct'])
        provenance=read(root/'reference-provenance.json')
        self.assertFalse(provenance['quantization_performed'])
        self.assertEqual(provenance['saved_tensor_dtype_counts'],{'BF16':339})
        self.assertEqual(provenance['loaded_metadata']['parameter_dtype_counts'],{'mlx.core.bfloat16':339})
        self.assertEqual(provenance['loaded_metadata']['quantized_modules'],[])
        for name,official in provenance['official_weights'].items():
            self.assertEqual(provenance['reference_files'][name],official)
        summary=read(root/'summary.json')
        self.assertEqual(summary['larger_to_small_exact_rendered_token_matches'],56)
        for run in ('wording','larger_reference'):
            for d,v in summary[run]['deployments'].items():
                self.assertFalse(v['suitability_pass'])
                self.assertEqual(v['coverage']['primary_scoreable'],v['coverage']['planned'])
                for w,g in v['groups'].items():
                    self.assertEqual(g['metrics']['posterior_error']['planned'],12)

    def test_saved_journal_and_attempt_budget(self):
        FakeAdapter.mode='stop'
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            run(CONFIG,PREPARED,root,'reference',90,FakeAdapter,dataset=load_diagnostic())
            run(CONFIG,PREPARED,root,'quantized',90,FakeAdapter,dataset=load_diagnostic())
            snapshot(root,root/'raw.json');before=file_hash(root/'raw.json')
            s=score(root/'raw.json',root/'scores.json');score(root/'raw.json',root/'again.json')
            report(root/'raw.json',root/'scores.json',root/'report.md')
            report(root/'raw.json',root/'scores.json',root/'regenerated.md')
            self.assertEqual((root/'report.md').read_bytes(),(root/'regenerated.md').read_bytes())
            self.assertEqual((root/'scores.json').read_bytes(),(root/'again.json').read_bytes())
            self.assertEqual(file_hash(root/'raw.json'),before)
            self.assertEqual(s['deployments']['reference']['coverage']['primary_scoreable'],90)
            self.assertEqual(run(CONFIG,PREPARED,root,'reference',100,FakeAdapter,dataset=load_diagnostic()),0)
            # All attempted infrastructure errors exhaust the global ceiling; no extra call.
            for i in range(20):
                (root/f'budget-placeholder-{i}.start.json').write_text('{}')
            # Completed observations skipped; turn the first outcome into an infrastructure error to test retry ceiling.
            first=next(r for r in read(root/'run.json')['requests'] if r['deployment_id']=='reference')
            path=root/(first['request_id']+'-0.result.json');a=read(path);a.update(status='infrastructure_error');path.write_text(__import__('json').dumps(a))
            with self.assertRaisesRegex(ValueError,'ceiling'):
                run(CONFIG,PREPARED,root,'reference',1,FakeAdapter,dataset=load_diagnostic())
