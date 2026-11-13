"""Independent offline checks; simulated responses are never human/model evidence."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from cib import source_pilot as sp, source_fidelity as sf, review
from cib.records import digest, file_hash, read
from cib.runner import write_new


class PilotTests(unittest.TestCase):
    def prepare(self,root,cap=None):
        # No downloaded preparation/model files are needed in the default suite.
        protocol=read(sp.CONFIG);base=read(protocol['pair_config'])
        if cap is not None: protocol['max_attempts']=cap
        prepared=dict(config_sha256=digest(base),reference=dict(path='SYNTHETIC-OFFLINE',files={}),
                      quantized=dict(path='SYNTHETIC-OFFLINE',files={}))
        prep_path=root.parent/'synthetic-prepared.json';config_path=root.parent/'test-protocol.json'
        write_new(prep_path,prepared);protocol['pair_prepared']=str(prep_path)
        write_new(config_path,protocol)
        return sp.prepare(root,config_path)

    def raw(self,root):
        p=self.prepare(root)
        attempts={m:{} for m in sp.MODELS}
        for m in sp.MODELS:
            for slot in p['allocation']:
                s=next(s for s in p['dataset']['scenarios'] if s['scenario_id']==slot['scenario_id'])
                attempts[m][slot['slot']]=dict(**slot,model=m,messages=sf.messages(s),
                    deployment_sha256=digest(p['models'][m]),decoding=p['models'][m]['config']['generation'],
                    text='{"abstain":false,"claims":[]}',status='completed',stop_reason='stop')
        return dict(schema_version='cib.source-fidelity-raw.v1',plan=p,plan_sha256=digest(p),attempts=attempts)

    def test_separation_allocation_pairing_and_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw=self.raw(Path(tmp)/'run');p=raw['plan']
            self.assertEqual(len(p['allocation']),10)
            self.assertEqual(p['protocol']['review']['second_reviewer_scenarios'],['sf101','sf103','sf104','sf107'])
            for s in p['dataset']['scenarios']:
                changed=copy.deepcopy(s);changed['annotations']={'secret':'SCORER_SENTINEL'}
                self.assertEqual(sf.messages(s),sf.messages(changed))
                self.assertNotIn('SCORER_SENTINEL',str(sf.messages(changed)))
                self.assertNotIn('quote_required',str(sf.messages(s)))
            r=sp.calculate(raw)
            self.assertEqual(r['summary']['reference']['empty_answers'],8)
            self.assertIsNone(r['summary']['reference']['provisional_full_set_success'])
            raw['attempts']['reference'].pop('sf107-main')
            self.assertEqual(sp.calculate(raw)['summary']['reference']['attempted_main'],7)
            broken=copy.deepcopy(raw);broken['attempts']['quantized']['sf101-main']['messages']=[]
            with self.assertRaises(ValueError): sp.validate(broken)
            for m in sp.MODELS: raw['attempts'][m]['sf101-main']['actual']={'input_token_ids':[1]}
            raw['attempts']['quantized']['sf101-main']['actual']['input_token_ids']=[2]
            with self.assertRaises(ValueError): sp.validate(raw)

    def test_citations_quotes_empty_and_extractability(self):
        s={'sources':{'D1':'The seal is amber.','D2':'The seal is blue.'},'annotations':{'answerable':True}}
        def response(claim):return json.dumps({'abstain':False,'claims':[claim]})
        claim=dict(text='The seal is green.',citations=['D1'],quotes=[dict(source_id='D1',text='The seal is amber.')])
        # Mechanically perfect despite incorrect semantics.
        text=response(claim);r=sf.score(s,text)
        self.assertEqual(r['mechanical']['citation_id_precision'],1)
        self.assertEqual(r['mechanical']['quote_exactness'],1)
        self.assertIsNone(r['semantic_support'])
        claim['citations']=['unknown'];claim['quotes'][0]['source_id']='D2'
        r=sf.score(s,response(claim));self.assertEqual(r['mechanical']['valid_citation_ids'],0);self.assertEqual(r['mechanical']['accurate_quote_spans'],0)
        claim['quotes']=[dict(source_id='D1',text='')]
        self.assertEqual(sf.score(s,response(claim))['mechanical']['accurate_quote_spans'],0)
        a=dict(status='completed',text='```json\n'+text+'\n```')
        r=sp.mechanical(s,a);self.assertFalse(r['strict_compliance']);self.assertTrue(r['mechanically_extractable'])
        a['text']='The seal is amber.';r=sp.mechanical(s,a)
        self.assertFalse(r['mechanically_extractable']);self.assertTrue(r['raw_content_available']);self.assertIsNone(r['human_assessability'])
        a['text']='';self.assertFalse(sp.mechanical(s,a)['raw_content_available'])
        a.update(status='truncated',text=text);self.assertFalse(sp.mechanical(s,a)['mechanically_extractable'])

    def test_review_versions_human_gate_and_regeneration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw=self.raw(root/'run');write_new(root/'raw.json',raw)
            public=sp.export_review(root/'raw.json',root/'review');template=read(root/'review/reviewer-1.json')
            self.assertEqual(len(template['ratings']),16);self.assertEqual(len(read(root/'review/reviewer-2.json')['ratings']),8)
            self.assertNotIn('model',str(public));self.assertNotIn('reference',json.dumps(public))
            template.update(kind='synthetic_test',reviewer_id='offline-test-only',timestamp='2026-11-12T12:00:00Z')
            for row in template['ratings']: row['ratings']['task_success']='pass'
            result=sp.calculate(raw,public,[template]);self.assertEqual(result['summary']['reference']['provisional_success_coverage'],0)
            # Test human gating only; temporary simulated data is never exported as validation.
            template['kind']='human';result=sp.calculate(raw,public,[template]);self.assertEqual(result['summary']['reference']['provisional_success_coverage'],8)
            bad=copy.deepcopy(template);bad['schema_version']=review.VERSION
            with self.assertRaises(ValueError):review.validate_submission(public,bad)
            bad=copy.deepcopy(public);bad['rubric']['task_success']['definition']='changed'
            with self.assertRaises(ValueError): review.validate_submission(bad,template)
            old=file_hash(root/'raw.json')
            for n in (1,2):
                sp.score_file(root/'raw.json',root/f's{n}.json');sp.report_file(root/'raw.json',root/f's{n}.json',root/f'r{n}.md')
            self.assertEqual((root/'s1.json').read_bytes(),(root/'s2.json').read_bytes());self.assertEqual((root/'r1.md').read_bytes(),(root/'r2.md').read_bytes());self.assertEqual(file_hash(root/'raw.json'),old)
            with self.assertRaises(FileExistsError):sp.score_file(root/'raw.json',root/'s1.json')

    def test_real_attempt_bound_and_no_malformed_retry(self):
        class Fake:
            metadata={'label':'SYNTHETIC OFFLINE ADAPTER'}
            def __init__(self,*args):pass
            def render(self,payload):return {'rendered_input':str(payload),'input_token_ids':[1]}
            def generate(self,actual,emit):emit(dict(text='malformed',finish_reason='stop',token=1,generation_tokens=1));return {}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'run';self.prepare(root)
            self.assertEqual(sp.run(root,'reference',10,Fake),10)
            self.assertEqual(sp.run(root,'reference',10,Fake),0)
            raw=sp.snapshot(root,root/'raw.json');self.assertEqual(len(raw['attempts']['reference']),10)
            self.assertEqual(sp.calculate(raw)['summary']['reference']['mechanically_extractable'],0)
            with self.assertRaises(ValueError):sp.run(root,'reference',-1,Fake)


    def test_infrastructure_start_counts_and_global_ceiling(self):
        class Failing:
            metadata={'label':'SYNTHETIC OFFLINE ADAPTER'}
            def __init__(self,*args):pass
            def render(self,payload):raise RuntimeError('SYNTHETIC render failure')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'run';self.prepare(root,cap=1)
            self.assertEqual(sp.run(root,'reference',10,Failing),1)
            self.assertEqual(len(sp.histories(root,'reference')),1)
            self.assertEqual(next(iter(sp.histories(root,'reference').values()))['status'],'infrastructure_error')
            with self.assertRaisesRegex(ValueError,'attempt ceiling'):sp.run(root,'quantized',10,Failing)
            self.assertEqual(len(list(root.glob('*/*.start.json'))),1)


if __name__=='__main__':unittest.main()
