"""M4b fixed wording diagnostic. Targets are never part of adapter payloads."""
import argparse
import copy
from fractions import Fraction
from importlib.resources import files
import inspect
from pathlib import Path
from statistics import mean
from collections import Counter

from .records import read, digest, write_new, file_hash, observation_id, key
from .scoring import (score_attempt, complete_mean, summarize, DIAGNOSTIC_PARSER,
                      STRICT_PARSER, parse_probability, parse_diagnostic)
from .tasks import posterior

FORMAT=' Return only a JSON object with exactly the key "probability" and a numeric value in [0,1].'
METRICS=('posterior_error','prior_error','update_error','uninformative_drift')


def load_diagnostic(larger=False):
    ds=read(files('cib').joinpath('data/diagnostic-v1.json'))
    if larger:
        ds['scope']='larger_reference'
        ds['diagnostic_protocol'].update(planned_per_deployment=60,planned_total=60,max_generation_requests=100,
            max_mlx_peak_bytes=24000000000,allocation='56 identical mathematical/natural trial0 requests plus first 4 selected main repeats; one unquantized reference',repeats='first 4 selected main requests once')
    return ds


def case_values(scenario, condition, label):
    p,a,b=map(Fraction,(scenario['prior'],condition['likelihood_h'],condition['likelihood_not_h']))
    if label=='swapped':p,a,b=1-p,b,a
    return p,a,b


def render(p,a,b,label,wording,stage):
    """Semantically equivalent facts; no Bayes formula or derived posterior supplied."""
    target_label,other=('A','B') if label=='original' else ('B','A')
    def f(x):return str(float(x))
    if wording=='original':
        text=f'A packet comes from source {target_label} or source {other}. H means its source is {target_label}. The prior P(H) is {f(p)}. '
        text+= ('No signal has been observed. Report P(H).' if stage=='pre' else
                f'A single signal E has been observed. P(E|H)={f(a)}; P(E|not H)={f(b)}. There are no other observations. Report P(H|E).')
    elif wording=='mathematical':
        text=f'Binary hypotheses: H = packet from source {target_label}; not H = packet from source {other}. P(H)={f(p)} and P(not H)={f(1-p)}. '
        text+= ('No evidence is observed. Report the prior probability P(H).' if stage=='pre' else
                f'P(E|H)={f(a)} and P(E|not H)={f(b)}. Exactly one event E is observed. Report the conditional probability P(H|E).')
    elif wording=='natural':
        text=f'A packet is from one of two sources, {target_label} or {other}. Before inspecting any mark, {int(p*100)} out of every 100 packets are from {target_label}; the rest are from {other}. '
        text+= (f'No mark has been inspected. What fraction of packets are from {target_label}?' if stage=='pre' else
                f'Among packets from {target_label}, {int(a*100)} out of 100 carry a mark. Among packets from {other}, {int(b*100)} out of 100 carry a mark. This packet carries the mark; no other information is available. What fraction of marked packets are from {target_label}?')
    else:raise ValueError('unsupported wording')
    return {'messages':[{'role':'user','content':text+FORMAT}]}


def render_control(a,b,wording):
    if wording=='original':
        text=f'The signal probability given H is {float(a)}; the signal probability given not H is {float(b)}. Report P(signal|H), not P(H|signal).'
    elif wording=='mathematical':
        text=f'Given P(E|H)={float(a)} and P(E|not H)={float(b)}, report the value of P(E|H).'
    elif wording=='natural':
        text=f'Among 100 cases in which hypothesis H holds, {int(a*100)} have a signal. Among 100 cases in which H does not hold, {int(b*100)} have a signal. Within the group where H holds, what fraction have the signal?'
    else:raise ValueError('unsupported wording')
    return {'messages':[{'role':'user','content':text+FORMAT}]}


def planned(dataset,deployments):
    result=[]
    wordings=dataset['wordings'] if dataset['scope']=='pair' else ['mathematical','natural']
    for d in deployments:
        main=[]; controls=[]
        def request(sid,cluster,condition,label,wording,stage,payload,trial=0):
            r=dict(schema_version='cib.request.v1',scenario_id=sid,cluster_id=cluster,condition_id=condition,
                label_variant=label,prompt_variant=wording,stage=stage,task_version=dataset['task_version'],trial_index=trial,
                deployment_id=d,input=payload,decoding=dataset['diagnostic_protocol']['generation'])
            r['input_sha256']=digest(payload);r['request_id']=observation_id(r)
            return r
        for scenario in dataset['scenarios']:
            for label in dataset['label_variants']:
                for wording in wordings:
                    for c in scenario['conditions']:
                        p,a,b=case_values(scenario,c,label)
                        for stage in ('pre','post'):
                            main.append(request(scenario['scenario_id'],scenario['cluster_id'],c['condition_id'],label,wording,stage,render(p,a,b,label,wording,stage)))
        for c in dataset['controls']:
            for wording in wordings:
                controls.append(request('likelihood-'+c['control_id'],'likelihood-reading','likelihood','original',wording,'control',render_control(Fraction(c['likelihood_h']),Fraction(c['likelihood_not_h']),wording)))
        repeats=[]
        for r in main[:6 if dataset['scope']=='pair' else 4]:
            rr={**copy.deepcopy(r),'trial_index':1};rr['request_id']=observation_id(rr);repeats.append(rr)
        result.extend(main+controls+repeats)
    if len({r['request_id'] for r in result})!=len(result):raise ValueError('duplicate diagnostic request')
    return result


def coverage(requests,latest,observations):
    completed=sum(latest[r['request_id']]['status']=='completed' for r in requests)
    return dict(planned=len(requests),executed=sum(latest[r['request_id']]['status']!='not_attempted' for r in requests),
        completed_eligible=completed,primary_scoreable=sum(observations[r['request_id']]['status']=='valid' for r in requests),
        strict_compliant=sum(score_attempt(latest[r['request_id']],STRICT_PARSER)['status']=='valid' for r in requests),
        strict_denominator=completed,statuses=dict(Counter(observations[r['request_id']]['status'] for r in requests)))


def calculate(raw):
    from .runner import validate_real
    from .pipeline import source_hash
    validate_real(raw)
    ds=raw['dataset'];req=raw['requests'];latest={a['request_id']:a for a in raw['attempts']}
    observations={r['request_id']:score_attempt(latest[r['request_id']],DIAGNOSTIC_PARSER) for r in req}
    result=dict(schema_version='cib.diagnostic-scores.v1',scorer_version='m4b-scorer-v1',dataset_sha256=digest(ds),run_id=raw['manifest']['run_id'],
        source_sha256=source_hash(),parser_implementation_sha256=digest(inspect.getsource(parse_diagnostic)+inspect.getsource(parse_probability)),primary_parser=DIAGNOSTIC_PARSER,
        observations=observations,deployments={})
    wordings=ds['wordings'] if ds['scope']=='pair' else ['mathematical','natural']
    for d in raw['manifest']['deployments']:
        rr=[r for r in req if r['deployment_id']==d];index={key(r):r for r in rr};groups={};rows=[]
        def probability(r):return observations[r['request_id']]['probability']
        for scenario in ds['scenarios']:
            for label in ds['label_variants']:
                for wording in wordings:
                    for c in scenario['conditions']:
                        p,a,b=case_values(scenario,c,label);target=float(posterior(p,a,b))
                        def lookup(stage):return index[(scenario['scenario_id'],ds['task_version'],c['condition_id'],label,wording,0,stage)]
                        pre,post=lookup('pre'),lookup('post');x,y=probability(pre),probability(post)
                        rows.append(dict(scenario_id=scenario['scenario_id'],condition_id=c['condition_id'],label_variant=label,wording=wording,prior=float(p),posterior=target,
                            pre_request_id=pre['request_id'],post_request_id=post['request_id'],pre_probability=x,post_probability=y,uninformative=a==b,
                            prior_error=None if x is None else abs(x-float(p)),posterior_error=None if y is None else abs(y-target),
                            update_error=None if x is None or y is None else abs(y-x-target+float(p)),
                            uninformative_drift=None if a!=b or x is None or y is None else abs(y-x)))
        controls=[]
        for c in ds['controls']:
            for w in wordings:
                r=index[('likelihood-'+c['control_id'],ds['task_version'],'likelihood','original',w,0,'control')];p=probability(r);target=float(Fraction(c['likelihood_h']))
                controls.append(dict(control_id=c['control_id'],wording=w,request_id=r['request_id'],target=target,probability=p,
                    absolute_error=None if p is None else abs(p-target),correct=p is not None and abs(p-target)<=1e-6))
        for w in wordings:
            chosen=[r for r in rows if r['wording']==w]
            scenario_scores={s['scenario_id']:summarize([r for r in chosen if r['scenario_id']==s['scenario_id']]) for s in ds['scenarios']}
            metrics={m:dict(mean=complete_mean([v[m]['mean'] for v in scenario_scores.values()]),scoreable=sum(v[m]['scoreable'] for v in scenario_scores.values()),planned=sum(v[m]['planned'] for v in scenario_scores.values()),complete_scenarios=sum(v[m]['mean'] is not None for v in scenario_scores.values())) for m in METRICS}
            cc=[c for c in controls if c['wording']==w]
            baseline=mean(abs(r['prior']-r['posterior']) for r in chosen)
            groups[w]=dict(coverage=coverage([r for r in rr if r['prompt_variant']==w and r['trial_index']==0],latest,observations),metrics=metrics,scenario_scores=scenario_scores,
                condition_scores={c:summarize([r for r in chosen if r['condition_id']==c]) for c in ('irrelevant','relevant')},
                likelihood=dict(correct=sum(c['correct'] for c in cc),planned=len(cc),scoreable=sum(c['probability'] is not None for c in cc),absolute_error=complete_mean([c['absolute_error'] for c in cc])),unchanged_prior_posterior_baseline=baseline,
                posterior_loss_bounds=[mean(s['posterior_bounds'][i] for s in scenario_scores.values()) for i in (0,1)])
        repeats=[]
        for r in rr:
            if r['trial_index']!=1:continue
            original=index[(*key(r)[:5],0,r['stage'])];p,q=probability(original),probability(r)
            repeats.append(dict(request_id=r['request_id'],original_request_id=original['request_id'],text_equal=latest[r['request_id']]['text']==latest[original['request_id']]['text'],
                status_equal=latest[r['request_id']]['status']==latest[original['request_id']]['status'],probability_difference=None if p is None or q is None else abs(p-q)))
        result['deployments'][d]=dict(coverage=coverage(rr,latest,observations),groups=groups,condition_rows=rows,controls=controls,repeats=repeats,
            cost=dict(attempts=sum(a['deployment_id']==d and a['status']!='not_attempted' for a in raw['attempts']),generation_wall_seconds=sum(a.get('generation_wall_seconds',0) for a in raw['attempts'] if a['deployment_id']==d),
                mlx_peak_bytes=max((a.get('mlx_peak_bytes',0) for a in raw['attempts'] if a['deployment_id']==d),default=0)))
        criterion=ds['diagnostic_protocol']['suitability_criteria']; checks={}
        for w in ('mathematical','natural'):
            g=groups[w];m=g['metrics'];p=m['posterior_error']['mean']
            checks[w]=dict(full_coverage=g['coverage']['primary_scoreable']==g['coverage']['planned'],likelihood=g['likelihood']['correct']>=criterion['likelihood_correct_at_least'],
                prior=m['prior_error']['mean'] is not None and m['prior_error']['mean']<=criterion['prior_mean_error_at_most'],
                drift=m['uninformative_drift']['mean'] is not None and m['uninformative_drift']['mean']<=criterion['irrelevant_mean_drift_at_most'],
                posterior=p is not None and p<=criterion['posterior_mean_error_at_most'] and p<=criterion['posterior_baseline_ratio_at_most']*g['unchanged_prior_posterior_baseline'])
        result['deployments'][d]['suitability_checks']=checks
        result['deployments'][d]['suitability_pass']=all(all(v.values()) for v in checks.values())
    if len(raw['manifest']['deployments'])==2:
        from .scoring import paired_requests
        paired_requests(raw,'reference','quantized')
        result['paired_changes']={w:{m:None if any(result['deployments'][d]['groups'][w]['metrics'][m]['mean'] is None for d in ('reference','quantized')) else result['deployments']['quantized']['groups'][w]['metrics'][m]['mean']-result['deployments']['reference']['groups'][w]['metrics'][m]['mean'] for m in METRICS} for w in wordings}
    return result


def score(raw_path,output):
    result=calculate(read(raw_path));result['raw_sha256']=file_hash(raw_path);write_new(output,result);return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['score','report']);p.add_argument('--raw',type=Path,required=True);p.add_argument('--scores',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.command=='score':score(a.raw,a.output)
    else:
        from .diagnostic_report import report
        report(a.raw,a.scores,a.output)
    print(a.output)


if __name__=='__main__':main()
