"""Offline M4b audit of original M4 controls, exact prompts, targets and discrepancies."""
import argparse
from pathlib import Path
import json,re
from fractions import Fraction as F
from cib.records import read,write_new,file_hash,digest,key
from cib.runner import validate_real,cache_identity
from cib.scoring import score_attempt,paired_requests,DIAGNOSTIC_PARSER
raw=read('outputs/m4-pilot-v1/raw.json');s=read('outputs/m4-pilot-v1/scores.json')
validate_real(raw);pairs=paired_requests(raw,'reference','quantized')
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,required=True)
root=parser.parse_args().output;root.mkdir(parents=True,exist_ok=False)
files=[p for folder in ['outputs/m4-pilot-v1','docs/evidence/m4','docs/evidence/m3','docs/evidence/m2'] for p in Path(folder).rglob('*') if p.is_file() and p.name!='.lock']
write_new(root/'original-hashes.json',{str(p):file_hash(p) for p in files})
a={a['request_id']:a for a in raw['attempts']};requests={r['request_id']:r for r in raw['requests']}
controls=[]
for i in range(1,5):
 rr=[r for r in raw['requests'] if r['scenario_id']==f'control-likelihood-{i}']
 text=rr[0]['input']['messages'][0]['content']
 target=F(re.search(r'given H is ([0-9.]+);',text)[1])
 assert 'Report P(signal|H), not P(H|signal).' in text
 row=dict(control_id=f'likelihood-{i}',quantity='P(E|H), not P(H|E)',independent_target=str(target),
          interpretation='Among cases where H holds, the fraction with signal E. The other conditional is given separately; no prior is supplied or needed.',deployments={})
 for r in rr:
  attempt=a[r['request_id']];p=score_attempt(attempt,DIAGNOSTIC_PARSER)['probability']
  score=next(c for c in s['deployments'][r['deployment_id']]['controls'] if c['control_id']==row['control_id'])
  assert float(target)==score['target'] and p==score['probability']
  assert abs(p-float(target))==score['absolute_error']
  row['deployments'][r['deployment_id']]=dict(request=r,attempt=attempt,independent_absolute_error=abs(p-float(target)),correct=abs(p-float(target))<=1e-9)
 assert row['deployments']['reference']['attempt']['actual']==row['deployments']['quantized']['attempt']['actual']
 controls.append(row)
# Independently reconstruct analytic answers from the exact visible messages, without dataset target helpers.
checked=[]
for row in s['condition_scores']:
 pre,post=[requests[row[k+'_request_id']] for k in ('pre','post')]
 text=post['input']['messages'][0]['content']
 prior=F(re.search(r'prior P\(H\) is ([0-9.]+)\.',text)[1]);like=F(re.search(r'P\(E\|H\)=([0-9.]+);',text)[1]);other=F(re.search(r'P\(E\|not H\)=([0-9.]+)\.',text)[1])
 target=prior*like/(prior*like+(1-prior)*other)
 assert abs(float(target)-row['posterior'])<1e-14 and float(prior)==row['prior']
 p,q=[score_attempt(a[x['request_id']],DIAGNOSTIC_PARSER)['probability'] for x in (pre,post)]
 assert abs(abs(q-float(target))-row['posterior_error'])<1e-14
 assert abs(abs(p-float(prior))-row['prior_error'])<1e-14
 assert abs(abs((q-p)-(float(target)-float(prior)))-row['update_error'])<1e-14
 if like==other: assert abs(abs(q-p)-row['uninformative_drift'])<1e-14
 for r in (pre,post):
  attempt=a[r['request_id']];assert attempt['cache_identity']==cache_identity(r,attempt['actual'])
 checked.append(dict(row=row,pre_request=pre,post_request=post,pre_attempt=a[pre['request_id']],post_attempt=a[post['request_id']]))
quant_priors=[x for x in checked if x['row']['deployment_id']=='quantized' and x['row']['prior_error']>0]
# Three largest per deployment, retain ties by original order. Save all irrelevant rows too.
irrelevant=sorted([x for x in checked if x['row']['uninformative']],key=lambda x:-x['row']['uninformative_drift'])
prior_controls=[dict(request=r,attempt=a[r['request_id']]) for r in raw['requests'] if r['scenario_id'].startswith('control-prior-')]
result=dict(schema_version='cib.m4b-audit.v1',source_raw_sha256=file_hash('outputs/m4-pilot-v1/raw.json'),control_audit=controls,
            independently_checked_main_rows=len(checked),paired_requests=len(pairs),all_pair_messages_decoding_rendered_tokens_match=True,
            all_main_targets_and_losses_match=True,defects_found=[],quantized_prior_errors=quant_priors,irrelevant_cases=irrelevant,successful_prior_controls=prior_controls)
write_new(root/'audit.json',result)
for row in controls:
 print(row['control_id'],row['independent_target']);print(row['deployments']['reference']['attempt']['actual']['rendered_input'])
 for d,v in row['deployments'].items():print(d,repr(v['attempt']['text']),v['independent_absolute_error'])
print('largest drift')
for d in ('reference','quantized'):
 for x in [x for x in irrelevant if x['row']['deployment_id']==d][:5]:
  row=x['row']; print(d,row['scenario_id'],row['label_variant'],row['prior'],row['likelihood_h'],score_attempt(x['pre_attempt'],DIAGNOSTIC_PARSER)['probability'],score_attempt(x['post_attempt'],DIAGNOSTIC_PARSER)['probability'],row['uninformative_drift'])
print('quant priors',len(quant_priors))
for x in quant_priors:print(x['pre_request']['input'],repr(x['pre_attempt']['text']))
