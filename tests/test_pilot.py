"""Independent pilot arithmetic, allocation, parsing, and missingness checks."""
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest

from cib.tasks import load_pilot, cases
from cib.records import read, digest, file_hash, write_new
from cib.runner import new_run, run, snapshot, cache_identity
from cib.pilot import analyze
from cib.pilot_report import report
from cib.scoring import parse_diagnostic
from test_runner import CONFIG, PREPARED, FakeAdapter


class PilotTests(unittest.TestCase):
    def test_frozen_allocation_targets_and_visibility(self):
        ds=load_pilot()
        self.assertEqual(ds['pilot_protocol'],read(Path(__file__).resolve().parents[1]/'configs/pilot-v1.json'))
        raw=new_run(CONFIG,PREPARED,ds)
        self.assertEqual(len(raw['requests']),344)
        self.assertLessEqual(len(raw['requests'])*2,800)
        self.assertEqual(len(ds['scenarios']),12)
        self.assertEqual(len({s['cluster_id'] for s in ds['scenarios']}),3)
        # Independent normalized joint masses, calculated using Decimal rather than scorer fractions.
        expected=[Decimal(4)/13,Decimal(1)/37,Decimal('0.1'),Decimal(1)/3,Decimal(2)/11,Decimal('.25'),Decimal('.9'),Decimal('.1'),Decimal('.5'),Decimal('.9'),Decimal('.5'),Decimal('.75')]
        originals=[c for c in cases(ds) if c['label_variant']=='original']
        for i,c in enumerate(originals):
            self.assertAlmostEqual(c['posterior'],float(expected[i%12]))
            swapped=next(x for x in cases(ds) if x['scenario_id']==c['scenario_id'] and x['condition_id']==c['condition_id'] and x['label_variant']=='swapped')
            self.assertAlmostEqual(c['posterior']+swapped['posterior'],1)
        for r in raw['requests']:
            self.assertEqual(set(r['input']),{'messages'})
            self.assertEqual(set(r['input']['messages'][0]),{'role','content'})
            self.assertNotIn('target',str(r['input']))
            if r['stage']=='post': self.assertNotIn('assistant',str(r['input']))
        for d in ('reference','quantized'):
            rr=[r for r in raw['requests'] if r['deployment_id']==d]
            self.assertEqual(sum(r['trial_index']==1 for r in rr),12)
            self.assertEqual(sum(r['stage']=='control' for r in rr),16)
            for r in (r for r in rr if r['trial_index']==1):
                original=next(x for x in rr if x['trial_index']==0 and all(x[k]==r[k] for k in ('scenario_id','label_variant','condition_id','stage')))
                self.assertEqual(r['input'],original['input'])
                self.assertNotEqual(r['request_id'],original['request_id'])

    def test_saved_analysis_and_missingness(self):
        FakeAdapter.mode='stop'
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            run(CONFIG,PREPARED,root,'reference',172,FakeAdapter,dataset=load_pilot())
            run(CONFIG,PREPARED,root,'quantized',172,FakeAdapter,dataset=load_pilot())
            self.assertEqual(run(CONFIG,PREPARED,root,'reference',172,FakeAdapter,dataset=load_pilot()),0)
            snapshot(root,root/'raw.json')
            before=file_hash(root/'raw.json')
            scores=analyze(root/'raw.json',root/'scores.json')
            analyze(root/'raw.json',root/'again.json')
            report(root/'raw.json',root/'scores.json',root/'report.md')
            report(root/'raw.json',root/'scores.json',root/'regenerated.md')
            self.assertEqual((root/'report.md').read_bytes(),(root/'regenerated.md').read_bytes())
            with self.assertRaises(FileExistsError):
                report(root/'raw.json',root/'scores.json',root/'report.md')
            self.assertEqual((root/'scores.json').read_bytes(),(root/'again.json').read_bytes())
            self.assertEqual(before,file_hash(root/'raw.json'))
            self.assertAlmostEqual(scores['baselines']['unchanged-prior']['posterior_error']['mean'],(abs(4/13-.1)+abs(1/37-.1)+abs(1/3-.25)+abs(2/11-.25)+.4+.4+.15+.25)/12)
            self.assertEqual(scores['baselines']['analytic-oracle']['posterior_error']['mean'],0)
            row=next(r for r in scores['condition_scores'] if r['scenario_id']=='t1-s1' and r['condition_id']=='support' and r['label_variant']=='original')
            self.assertAlmostEqual(row['prior_error'],.15)
            self.assertAlmostEqual(row['posterior_error'],abs(.25-4/13))
            self.assertAlmostEqual(row['update_error'],4/13-.1)
            self.assertEqual(scores['paired_metrics']['posterior_error']['quantized_minus_reference'],0)
            for d in ('reference','quantized'):
                self.assertEqual(scores['deployments'][d]['coverage']['planned'],172)
                self.assertEqual(scores['deployments'][d]['coverage']['primary_scoreable'],172)
            raw=read(root/'raw.json'); raw['attempts'][1].update(status='completed',text='bad')
            write_new(root/'partial.json',raw)
            partial=analyze(root/'partial.json',root/'partial-scores.json')
            self.assertIsNone(partial['deployments']['reference']['metrics']['posterior_error']['mean'])
            self.assertIsNone(partial['paired_metrics']['posterior_error']['quantized_minus_reference'])
            self.assertEqual(partial['deployments']['reference']['coverage']['completed_eligible'],172)
            self.assertEqual(partial['deployments']['reference']['coverage']['primary_scoreable'],171)

    def test_versioned_measured_evidence(self):
        root=Path(__file__).resolve().parents[1]/'docs/evidence/m4'
        summary=read(root/'summary.json'); verification=read(root/'verification.json')
        self.assertEqual(summary['raw_sha256'],verification['raw_sha256'])
        self.assertEqual(summary['dataset_sha256'],digest(load_pilot()))
        self.assertTrue(verification['original_files_unchanged'])
        self.assertTrue(verification['rescoring_byte_identical'])
        for d in ('reference','quantized'):
            coverage=summary['deployments'][d]['coverage']
            self.assertEqual((coverage['planned'],coverage['executed'],coverage['completed_eligible'],coverage['primary_scoreable']),(172,172,172,172))
            self.assertEqual((coverage['strict_compliant'],coverage['strict_denominator']),(0,172))
        for entry in read(root/'examples.json')['examples']:
            request,attempt=entry['request'],entry['attempt']
            self.assertEqual(entry['source_raw_sha256'],summary['raw_sha256'])
            self.assertEqual(attempt['status'],'completed')
            self.assertEqual(attempt['cache_identity'],cache_identity(request,attempt['actual']))
            parse_diagnostic(attempt['text'])

    def test_additional_ambiguous_parser_boundaries(self):
        for body in ['{"probability":1e999}','{"probability":null}','[0.2]','{"probability":.2}','{"probability":0.2} trailing']:
            for text in [body,'```\n'+body+'\n```']:
                with self.assertRaises(ValueError): parse_diagnostic(text)
        for label in ['json','']:
            self.assertEqual(parse_diagnostic('```'+label+'\n{"probability":0.2}\n```'),.2)
