"""Pinned M4c single-answer conditional/rule/numerical diagnostic, offline analysis."""
import argparse
import copy
import inspect
import json
from fractions import Fraction as F
from importlib.resources import files
from pathlib import Path
from statistics import mean

from .diagnostic import FORMAT, coverage, render as conditional
from .records import read, digest, observation_id, file_hash, write_new
from .scoring import (score_attempt, complete_mean, DIAGNOSTIC_PARSER,
                      parse_probability, parse_diagnostic)

FORMULA = (' Use the Bayes normalization formula: P(H|E) = '
           '(P(H)*P(E|H)) / (P(H)*P(E|H) + P(not H)*P(E|not H)).')


def load():
    return read(files('cib').joinpath('data/rule-diagnostic-v1.json'))


def values(s):
    return tuple(F(s[k]) for k in ('prior', 'likelihood_h', 'likelihood_not_h'))


def target(s):
    p, a, b = values(s)
    return p*a / (p*a + (1-p)*b)


def render(s, form):
    p, a, b = values(s)
    if form in ('A', 'B'):
        text = conditional(p, a, b, 'original', 'mathematical', 'post')['messages'][0]['content']
        if form == 'B':
            text = text.removesuffix(FORMAT) + FORMULA + FORMAT
    elif form == 'C':
        p, a, b = (s[k] for k in ('prior', 'likelihood_h', 'likelihood_not_h'))
        text = f'Evaluate the numerical expression ({p}*{a}) / ({p}*{a} + (1-{p})*{b}).' + FORMAT
    else:
        raise ValueError('unsupported form')
    return {'messages': [{'role': 'user', 'content': text}]}


def planned(ds, deployments):
    if set(deployments) != {'reference'}:
        raise ValueError('M4c permits only the existing unquantized reference')
    result = []
    for i, s in enumerate(ds['scenarios']):
        forms = ds['forms'][i % 3:] + ds['forms'][:i % 3]
        for form in forms:
            r = dict(schema_version='cib.request.v1', scenario_id=s['scenario_id'],
                     cluster_id=ds['cluster_id'], condition_id='numerical', label_variant='original',
                     prompt_variant=form, stage='evaluation', task_version=ds['task_version'],
                     trial_index=0, deployment_id='reference', input=render(s, form),
                     decoding=ds['diagnostic_protocol']['generation'])
            r['input_sha256'] = digest(r['input'])
            r['request_id'] = observation_id(r)
            result.append(r)
    for sid, form in ds['diagnostic_protocol']['repeat_selection']:
        r = copy.deepcopy(next(r for r in result if r['scenario_id'] == sid and r['prompt_variant'] == form))
        r['trial_index'] = 1
        r['request_id'] = observation_id(r)
        result.append(r)
    return result


def summary(rows):
    errors = [r['absolute_error'] for r in rows]
    return dict(planned=len(rows), scoreable=sum(e is not None for e in errors),
                mean_absolute_error=complete_mean(errors),
                unchanged_prior_baseline=mean(r['baseline_loss'] for r in rows),
                loss_bounds=[mean((e if e is not None else bound) for e in errors) for bound in (0, 1)])


def calculate(raw):
    from .runner import validate_real
    from .pipeline import source_hash
    validate_real(raw)
    ds = raw['dataset']
    if ds != load():
        raise ValueError('unsupported M4c dataset')
    latest = {a['request_id']: a for a in raw['attempts']}
    obs = {r['request_id']: score_attempt(latest[r['request_id']], DIAGNOSTIC_PARSER) for r in raw['requests']}
    rows = []
    lookup = {(r['scenario_id'], r['prompt_variant'], r['trial_index']): r for r in raw['requests']}
    for s in ds['scenarios']:
        p, a, b = values(s)
        for form in ds['forms']:
            r = lookup[s['scenario_id'], form, 0]
            q = obs[r['request_id']]['probability']
            rows.append(dict(scenario_id=s['scenario_id'], form=form, request_id=r['request_id'],
                             prior=float(p), likelihood_h=float(a), likelihood_not_h=float(b),
                             target=float(target(s)), exact_target=str(target(s)), probability=q,
                             prior_type='balanced' if p == F(1, 2) else 'unequal',
                             evidence_type='uninformative' if a == b else 'favors_h' if a > b else 'favors_not_h',
                             absolute_error=None if q is None else abs(q-float(target(s))),
                             uninformative_prior_error=None if a != b or q is None else abs(q-float(p)),
                             baseline_loss=abs(float(p-target(s)))))
    groups = {}
    for form in ds['forms']:
        selected = [r for r in rows if r['form'] == form]
        types = {}
        for name in ('prior_type', 'evidence_type'):
            for value in sorted({r[name] for r in selected}):
                types[value] = summary([r for r in selected if r[name] == value])
        for prior in ('balanced', 'unequal'):
            for evidence in ('favors_h', 'favors_not_h', 'uninformative'):
                types[prior+'/'+evidence] = summary([r for r in selected if r['prior_type'] == prior and r['evidence_type'] == evidence])
        uninf = [r['uninformative_prior_error'] for r in selected if r['evidence_type'] == 'uninformative']
        g = dict(**summary(selected), by_type=types,
                 coverage=coverage([r for r in raw['requests'] if r['prompt_variant'] == form and r['trial_index'] == 0], latest, obs),
                 uninformative_prior_error=dict(planned=len(uninf), scoreable=sum(e is not None for e in uninf), mean=complete_mean(uninf)))
        c = ds['diagnostic_protocol']['criteria']
        mae = g['mean_absolute_error']
        g['screen'] = dict(full_coverage=g['scoreable'] == g['planned'],
                           absolute_error=mae is not None and mae <= c['mean_absolute_error_at_most'],
                           relative_error=mae is not None and mae <= c['baseline_ratio_at_most']*g['unchanged_prior_baseline'],
                           uninformative_prior_error=complete_mean(uninf) is not None and complete_mean(uninf) <= c['uninformative_prior_error_at_most'])
        g['screen_pass'] = all(g['screen'].values())
        groups[form] = g
    pairs = {}
    for left, right in (('B', 'A'), ('C', 'A'), ('C', 'B')):
        differences = []
        for s in ds['scenarios']:
            errors = {r['form']: r['absolute_error'] for r in rows if r['scenario_id'] == s['scenario_id']}
            differences.append(dict(scenario_id=s['scenario_id'], difference=None if errors[left] is None or errors[right] is None else errors[left]-errors[right]))
        pairs[left+'-'+right] = dict(planned=len(differences), scoreable=sum(r['difference'] is not None for r in differences),
                                    mean=complete_mean([r['difference'] for r in differences]), rows=differences)
    repeats = []
    for r in raw['requests']:
        if r['trial_index'] != 1:
            continue
        original = lookup[r['scenario_id'], r['prompt_variant'], 0]
        x, y = (obs[q['request_id']]['probability'] for q in (original, r))
        repeats.append(dict(scenario_id=r['scenario_id'], form=r['prompt_variant'], request_id=r['request_id'],
                            original_request_id=original['request_id'], probability=y,
                            text_equal=latest[r['request_id']]['text'] == latest[original['request_id']]['text'],
                            status_equal=latest[r['request_id']]['status'] == latest[original['request_id']]['status'],
                            probability_difference=None if x is None or y is None else abs(y-x)))
    attempts = [a for a in raw['attempts'] if a['status'] != 'not_attempted']
    recommendation = ('retain' if groups['A']['screen_pass'] else 'revise' if groups['B']['screen_pass'] or groups['C']['screen_pass'] else 'park')
    return dict(schema_version='cib.rule-scores.v1', scorer_version='m4c-scorer-v1', source_sha256=source_hash(),
                parser_implementation_sha256=digest(inspect.getsource(parse_diagnostic)+inspect.getsource(parse_probability)),
                primary_parser=DIAGNOSTIC_PARSER, dataset_sha256=digest(ds), run_id=raw['manifest']['run_id'],
                coverage=coverage(raw['requests'], latest, obs), attempt_count=len(attempts),
                independent_scenarios=12, template_clusters=1, observations=obs, rows=rows, groups=groups,
                paired_differences=pairs, repeats=repeats, recommendation=recommendation,
                cost=dict(generation_wall_seconds=sum(a.get('generation_wall_seconds', 0) for a in attempts),
                          mlx_peak_bytes=max((a.get('mlx_peak_bytes', 0) for a in attempts), default=0)))


def score(raw_path, output):
    result = calculate(read(raw_path))
    result['raw_sha256'] = file_hash(raw_path)
    write_new(output, result)
    return result


def report(raw_path, scores_path, output):
    raw, scores = read(raw_path), read(scores_path)
    expected = calculate(raw)
    if scores != dict(expected, raw_sha256=file_hash(raw_path)):
        raise ValueError('scores/raw/source lineage mismatch')
    lines = ['# M4c exploratory instrument diagnostic', '',
             'One existing unquantized 7B reference; 12 numerical problems in one template cluster. '
             'B supplies a symbolic rule; C supplies numerical substitution. These are task interventions. '
             'No observed pre-response and no drift metric. Repeats are excluded from main means.', '',
             'Primary parser: outer-json-fence-v1; strict compliance reported separately.', '',
             f'Raw SHA256: `{scores["raw_sha256"]}`; scorer: `{scores["scorer_version"]}`.', '',
             'Coverage, continuous aggregate errors, types, missing-loss bounds and prespecified screens:', '',
             '```json', json.dumps({k:scores[k] for k in ('coverage','attempt_count','groups','paired_differences','repeats','cost','recommendation')}, indent=2), '```', '',
             '| Case | Form | Prior | P(E\u007cH) | P(E\u007cnot H) | Exact target | Response | Absolute error |',
             '| --- | --- | ---: | ---: | ---: | --- | ---: | ---: |']
    for r in scores['rows']:
        lines.append('| '+' | '.join(str(r[k]) for k in ('scenario_id','form','prior','likelihood_h','likelihood_not_h','exact_target','probability','absolute_error'))+' |')
    lines += ['', '## Exact inputs and all attempt histories', '']
    for r in raw['requests']:
        lines += [f'### {r["scenario_id"]} / {r["prompt_variant"]} / trial {r["trial_index"]}', '', '```json', json.dumps(r, indent=2), '```', '']
        for a in raw['attempts']:
            if a['request_id'] == r['request_id']:
                # JSON encoding keeps arbitrary output from escaping a Markdown block.
                lines += ['```json', json.dumps(a, indent=2).replace('`', '\\u0060'), '```', '']
    lines += ['## Frozen dataset and settings', '', '```json', json.dumps(raw['dataset'], indent=2), '```', '',
              '```json', json.dumps(raw['manifest'], indent=2), '```', '']
    with Path(output).open('x') as stream:
        stream.write('\n'.join(lines))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=('score', 'report'))
    p.add_argument('--raw', type=Path, required=True)
    p.add_argument('--scores', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.command == 'score':
        score(a.raw, a.output)
    else:
        report(a.raw, a.scores, a.output)
    print(a.output)


if __name__ == '__main__':
    main()
