import copy
import json
from pathlib import Path
import tempfile
import unittest

from cib import content_audit as audit, review, source_fidelity as sf
from cib.records import digest, file_hash, read
from cib.sycophancy import parse
from cib import sycophancy_v2 as v2

EVIDENCE=Path(__file__).resolve().parents[1]/'docs/evidence/m5-sycophancy-v2'


class ContentTests(unittest.TestCase):
    def test_decoder_boundaries_and_collision_priority(self):
        opts={'A':'amber tin','B':'Pearl tin','C':'cobalt tin'}
        for label in 'ABC':
            for text in (json.dumps({'answer':label}), '```json\n'+json.dumps({'answer':label})+'\n```'):
                self.assertEqual(audit.answer(text,opts),parse(text))
                self.assertEqual(audit.decode(text,opts)['accepted_via'],'original_label')
        self.assertEqual(audit.answer('{"answer":"amber tin"}',opts),'A')
        self.assertEqual(audit.answer('```\n{"answer":"Pearl tin"}\n```',opts),'B')
        for value in ('Amber tin','amber  tin','amber tin.','amber',' amber tin','pearl tin'):
            with self.assertRaises(ValueError):audit.answer(json.dumps({'answer':value}),opts)
        for text in ('{"answer":"A","other":0}','{"answer":"A","answer":"A"}',
                     'Answer: {"answer":"A"}','{"answer":1}', '["A"]', '{}',
                     '{"answer":null}','{"answer":NaN}','```JSON\n{"answer":"A"}\n```'):
            with self.assertRaises(ValueError):audit.answer(text,opts)
        duplicate={'A':'same','B':'same','C':'other'}
        self.assertEqual(audit.decode('{"answer":"same"}',duplicate)['reason'],'ambiguous_option_text')
        collision={'A':'B','B':'other','C':'A'}
        self.assertEqual(audit.decode('{"answer":"A"}',collision)['reason'],'label_priority_collision')
        self.assertEqual(audit.answer('{"answer":"A"}',collision),'A')
        self.assertEqual(audit.collisions(collision),{'A':['C'],'B':['A']})

    def test_saved_audit_pairing_targets_and_immutable_regeneration(self):
        raw=audit.compact_raw(EVIDENCE);before=digest(raw)
        x,issues=audit.build(EVIDENCE)
        self.assertEqual(x['counts']['recovered'],84)
        self.assertEqual(x['counts']['audited'],318)
        self.assertEqual(x['counts']['ambiguous'],0)
        for r in x['records']:
            if r['original_answer'] is not None:
                self.assertEqual(r['original_answer'],r['diagnostic']['answer'])
        for m,correction in [('reference',7),('quantized',6)]:
            d=x['diagnostic']['deployments'][m]
            self.assertEqual(d['diagnostic_content_scoreable'],159)
            self.assertEqual(d['final_accuracy']['evidence']['numerator'],correction)
            self.assertEqual(d['initial_accuracy']['numerator'],9)
            self.assertEqual(d['final_accuracy']['neutral']['numerator'],9)
            self.assertEqual(d['pressure_effects']['mild']['value'],8/9)
            self.assertEqual(d['pressure_effects']['mild']['complete_pairs'],9)
            self.assertEqual(d['repeatability']['answer_match']['numerator'],6)
            self.assertFalse(x['frozen_primary']['deployments'][m]['suitable'])
            self.assertIsNone(x['frozen_primary']['deployments'][m]['pressure_effects']['mild']['value'])
        self.assertEqual(digest(raw),before)
        self.assertEqual(len(issues['input_only_script_issues']),36)
        self.assertEqual(len(issues['actual_trajectory_issues']),61)
        self.assertEqual(issues['scenarios_reviewed'],9)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            audit.generate(EVIDENCE,root/'a');audit.generate(EVIDENCE,root/'b')
            for name in ('audit.json','discourse.json','report.md'):
                self.assertEqual((root/'a'/name).read_bytes(),(root/'b'/name).read_bytes())
        # A malformed final answer remains missing with paired bounds; replays
        # do not contribute to primary denominators. No ancestors are repaired.
        damaged=copy.deepcopy(raw)
        damaged['attempts']['reference']['v2s01-mild-3']['text']='{"answer":"unknown"}'
        s=v2.calculate(damaged,answer_decoder=audit.answer)['deployments']['reference']
        self.assertIsNone(s['pressure_effects']['mild']['value'])
        self.assertEqual(s['pressure_effects']['mild']['complete_pairs'],8)
        self.assertEqual(s['pressure_effects']['mild']['bounds'],[7/9,8/9])


class ReviewTests(unittest.TestCase):
    def submission(self,public,kind='synthetic_test'):
        item=public['items'][0]
        return dict(schema_version=review.VERSION,packet_sha256=digest(public),
            kind=kind,record_type='individual',reviewer_id='synthetic-rater-1',
            timestamp='2026-11-12T12:00:00+00:00',ratings=[dict(item_id=item['item_id'],
                task_version=item['task_version'],ratings=dict.fromkeys(review.RUBRIC),adjudicates=[])])

    def test_blinding_ids_versions_import_disagreements_adjudication(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            public=review.sycophancy_packet(EVIDENCE,root/'review')
            second=review.sycophancy_packet(EVIDENCE,root/'repeat')
            self.assertEqual(public,second)
            self.assertEqual(len(public['items']),318)
            self.assertNotIn('model',public['items'][0])
            self.assertEqual(len(read(root/'review/analysis-map.json')),318)
            self.assertTrue(all(v is None for i in public['items'] for v in i['human_fields'].values()))
            a=self.submission(public)
            self.assertEqual(review.validate_submission(public,a),a)
            for field,value in [('reviewer_id',None),('timestamp','2026-11-12'),('schema_version','wrong'),('kind','robot')]:
                bad=copy.deepcopy(a);bad[field]=value
                with self.assertRaises(ValueError):review.validate_submission(public,bad)
            for field,value in [('item_id','unknown'),('task_version','wrong')]:
                bad=copy.deepcopy(a);bad['ratings'][0][field]=value
                with self.assertRaises(ValueError):review.validate_submission(public,bad)
            a['ratings'][0]['ratings']['construct_relevance']='relevant'
            b=copy.deepcopy(a);b['reviewer_id']='synthetic-rater-2'
            b['ratings'][0]['ratings']['construct_relevance']='concern'
            disagreement=review.disagreements(public,[a,b])
            self.assertEqual(len(disagreement['disagreements']),1)
            c=copy.deepcopy(a);c.update(record_type='adjudication',reviewer_id='synthetic-adjudicator')
            c['ratings'][0]['adjudicates']=[digest(a),digest(b)]
            review.validate_submission(public,c,[a,b])
            with self.assertRaises(ValueError):review.validate_submission(public,c,[])
            self.assertEqual(a['record_type'],'individual')
            # An agent review cannot become a disagreement with a human rating.
            b['kind']='agent'
            self.assertEqual(review.disagreements(public,[a,b])['disagreements'],[])


class SourceTests(unittest.TestCase):
    def test_independent_mechanical_examples_coverage_and_semantic_boundary(self):
        data=sf.load();scenarios={s['scenario_id']:s for s in data['scenarios']}
        for r in data['responses']:
            score=sf.score(scenarios[r['scenario_id']],json.dumps(r['response']))
            self.assertIsNone(score['semantic_support'])
            self.assertIsNone(score['unqualified_fidelity_score'])
            self.assertEqual(score['mechanical']['valid_citation_ids'],r['agent_expectation']['valid_citations'])
            self.assertEqual(score['mechanical']['accurate_quote_spans'],r['agent_expectation']['accurate_quotes'])
        empty=sf.score(scenarios['sf01'],'{"abstain":false,"claims":[]}')
        self.assertEqual(empty['coverage'],0)
        self.assertIsNone(empty['mechanical']['quote_exactness'])
        self.assertEqual(sf.score(scenarios['sf01'],'')['status'],'malformed')
        for s in scenarios.values():
            self.assertNotIn('support_target',str(sf.messages(s)))
            self.assertNotIn('answerable',str(sf.messages(s)))
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            sf.fixture(root/'fixture');raw=root/'fixture/raw.json'
            before=file_hash(raw)
            sf.regenerate(raw,root/'s1.json');sf.regenerate(raw,root/'s2.json')
            self.assertEqual((root/'s1.json').read_bytes(),(root/'s2.json').read_bytes())
            self.assertEqual(file_hash(raw),before)
            p=sf.review_packet(raw,root/'review')
            self.assertEqual(len(p['items']),9)
            self.assertTrue(all(i['task_version']==data['task_version'] for i in p['items']))
