"""Pinned exploratory instrument, independent controls, and saved-output analysis.

No optional inference imports. Main metrics exclude repeats and controls.
"""
import argparse
from collections import Counter
import copy
import inspect
from pathlib import Path
from statistics import mean

from .records import digest, file_hash, key, observation_id, read, write_new
from .scoring import (calculate, complete_mean, parse_diagnostic, parse_probability,
                      score_attempt, DIAGNOSTIC_PARSER, STRICT_PARSER)
from .pipeline import source_hash
from .tasks import load_pilot, cases

FORMAT = ' Return only a JSON object with exactly the key "probability" and a numeric value in [0,1].'
METRICS = ('posterior_error', 'prior_error', 'update_error', 'uninformative_drift')


def extend_plan(dataset, main, deployments):
    result = []
    for deployment in deployments:
        selected = [r for r in main if r['deployment_id'] == deployment]
        result.extend(selected)
        for c in dataset['controls']:
            r = {**selected[0], 'scenario_id': 'control-'+c['control_id'],
                 'cluster_id': 'control-'+c['kind'], 'condition_id': c['kind'],
                 'label_variant': 'original', 'stage': 'control',
                 'input': {'messages': [{'role': 'user', 'content': c['prompt']+FORMAT}]}}
            r['input_sha256'] = digest(r['input'])
            r['request_id'] = observation_id(r)
            result.append(r)
        for original in selected[:12]:
            r = {**copy.deepcopy(original), 'trial_index': 1}
            r['request_id'] = observation_id(r)
            result.append(r)
    return result


def aggregate(rows):
    result = {}
    for metric in METRICS:
        eligible = [r for r in rows if metric != 'uninformative_drift' or r['uninformative']]
        vals = [r[metric] for r in eligible]
        result[metric] = {'mean': complete_mean(vals), 'scoreable': sum(v is not None for v in vals), 'planned': len(vals)}
    return result


def analyze(raw_path, output):
    raw = read(raw_path)
    if raw['dataset'] != load_pilot():
        raise ValueError('not the pinned pilot instrument')
    result = calculate(raw, DIAGNOSTIC_PARSER)
    strict = calculate(raw, STRICT_PARSER)
    requests = {r['request_id']: r for r in raw['requests']}
    latest = {a['request_id']: a for a in raw['attempts']}
    obs = {o['request_id']: o for o in result['observations']}
    result.update(schema_version='cib.pilot-scores.v1', scorer_version='updating-pilot-scorer-v1',
                  raw_sha256=file_hash(raw_path), dataset_sha256=digest(raw['dataset']),
                  run_id=raw['manifest']['run_id'], primary_parser=DIAGNOSTIC_PARSER,
                  parser_implementation_sha256=digest(inspect.getsource(parse_diagnostic)+inspect.getsource(parse_probability)),
                  scorer_source_sha256=source_hash(), protocol=raw['dataset']['pilot_protocol'])
    result['deployments'] = {}
    controls = {'control-'+c['control_id']: c for c in raw['dataset']['controls']}
    for d in ('reference','quantized'):
        rr = [r for r in requests.values() if r['deployment_id'] == d]
        rows = [r for r in result['condition_scores'] if r['deployment_id'] == d]
        summaries = result['scenario_scores'][d]
        def coverage(group):
            statuses = Counter(obs[r['request_id']]['status'] for r in group)
            completed = sum(latest[r['request_id']]['status']=='completed' for r in group)
            return dict(planned=len(group), executed=sum(latest[r['request_id']]['status']!='not_attempted' for r in group),
                        completed_eligible=completed, primary_scoreable=statuses['valid'],
                        strict_compliant=sum(score_attempt(latest[r['request_id']], STRICT_PARSER)['status']=='valid' for r in group),
                        strict_denominator=completed, primary_coverage_denominator=len(group), statuses=dict(statuses))
        controls_scored = []
        for r in rr:
            if r['stage']!='control': continue
            c=controls[r['scenario_id']]; p=obs[r['request_id']]['probability']
            controls_scored.append(dict(control_id=c['control_id'],kind=c['kind'],target=float(c['target']),
                                       probability=p,absolute_error=None if p is None else abs(p-float(c['target'])),
                                       correct=p is not None and abs(p-float(c['target']))<=1e-9))
        control_summary={k: dict(correct=sum(c['correct'] for c in controls_scored if c['kind']==k),planned=4,
                                scoreable=sum(c['probability'] is not None for c in controls_scored if c['kind']==k))
                         for k in ('prior','likelihood','arithmetic','format')}
        index={key(r):r for r in rr}
        repeats=[]
        for r in rr:
            if r['trial_index']!=1: continue
            original=index[(*key(r)[:5],0,r['stage'])]
            a,b=latest[original['request_id']],latest[r['request_id']]
            p,q=obs[original['request_id']]['probability'],obs[r['request_id']]['probability']
            repeats.append(dict(request_id=r['request_id'],original_request_id=original['request_id'],
                                text_equal=a['text']==b['text'],status_equal=a['status']==b['status'],
                                absolute_probability_difference=None if p is None or q is None else abs(p-q)))
        label_differences=[]
        for row in rows:
            if row['label_variant']!='original': continue
            other=next(x for x in rows if x['scenario_id']==row['scenario_id'] and x['condition_id']==row['condition_id'] and x['label_variant']=='swapped')
            p,q=obs[row['post_request_id']]['probability'],obs[other['post_request_id']]['probability']
            label_differences.append(None if p is None or q is None else abs(p+q-1))
        attempts=[a for a in raw['attempts'] if a['deployment_id']==d and a['status']!='not_attempted']
        post_losses=[r['posterior_error'] for r in rows]
        result['deployments'][d] = dict(
            coverage=coverage(rr),main_coverage=coverage([r for r in rr if r['stage']!='control' and r['trial_index']==0]),
            control_coverage=coverage([r for r in rr if r['stage']=='control']),repeat_coverage=coverage([r for r in rr if r['trial_index']==1]),
            metrics={m:dict(mean=complete_mean([s[m]['mean'] for s in summaries.values()]),
                            complete_scenarios=sum(s[m]['mean'] is not None for s in summaries.values()),planned_scenarios=12,
                            scoreable=sum(s[m]['scoreable'] for s in summaries.values()),planned=sum(s[m]['planned'] for s in summaries.values())) for m in METRICS},
            by_condition={c:aggregate([r for r in rows if r['condition_id']==c]) for c in ('support','oppose','irrelevant')},
            by_template={t:aggregate([r for r in rows if r['cluster_id']==t]) for t in sorted({r['cluster_id'] for r in rows})},
            controls=controls_scored,control_summary=control_summary,repeats=repeats,
            label_sensitivity=dict(mean_complement_error=complete_mean(label_differences),scoreable=sum(x is not None for x in label_differences),planned=36),
            difficulty=dict(exact_posterior_answers=sum(x is not None and x<=1e-9 for x in post_losses),scoreable=sum(x is not None for x in post_losses),planned=72,
                            posterior_loss_range=[min((x for x in post_losses if x is not None),default=None),max((x for x in post_losses if x is not None),default=None)],
                            scenario_loss_range=[min((s['posterior_error']['mean'] for s in summaries.values() if s['posterior_error']['mean'] is not None),default=None),max((s['posterior_error']['mean'] for s in summaries.values() if s['posterior_error']['mean'] is not None),default=None)]),
            cost=dict(attempts=len(attempts),generation_wall_seconds=sum(a.get('generation_wall_seconds',0) for a in attempts),
                      mlx_peak_bytes=max((a.get('mlx_peak_bytes',0) for a in attempts),default=0),
                      process_peak_rss_bytes=max((a.get('process_peak_rss_bytes',0) for a in attempts),default=0)))
    result['paired_metrics']={}
    for m in METRICS:
        a,b=[result['deployments'][d]['metrics'][m]['mean'] for d in ('reference','quantized')]
        result['paired_metrics'][m]=dict(quantized_minus_reference=None if a is None or b is None else b-a,direction='positive = larger loss; lower is better',planned_scenarios=12,
            complete_paired_scenarios=sum(result['scenario_scores']['reference'][s][m]['mean'] is not None and result['scenario_scores']['quantized'][s][m]['mean'] is not None for s in result['scenario_scores']['reference']))
    cc=list(cases(raw['dataset']))
    result['baselines']={}
    for name in ('unchanged-prior','constant-half','analytic-oracle'):
        rows=[]
        for c in cc:
            p=0.5 if name=='constant-half' else c['prior']
            q=c['posterior'] if name=='analytic-oracle' else p
            rows.append(dict(posterior_error=abs(q-c['posterior']),prior_error=abs(p-c['prior']),update_error=abs(q-p-c['posterior']+c['prior']),uninformative_drift=abs(q-p) if c['uninformative'] else None,uninformative=c['uninformative']))
        result['baselines'][name]=aggregate(rows)
    result['strict_format_coverage']=strict['coverage']
    write_new(output,result)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['score','report'])
    p.add_argument('--raw',type=Path,required=True)
    p.add_argument('--scores',type=Path)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.command=='score': analyze(a.raw,a.output)
    else:
        from .pilot_report import report
        report(a.raw,a.scores,a.output)
    print(a.output)


if __name__=='__main__': main()
