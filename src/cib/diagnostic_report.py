"""Saved-output report for M4b wording diagnostics and the single reference check."""
from pathlib import Path
from .records import read,file_hash,digest
from .runner import validate_real
from .report import literal,number
from .diagnostic import METRICS


def report(raw_path,scores_path,output):
    raw,s=read(raw_path),read(scores_path);validate_real(raw)
    if s['raw_sha256']!=file_hash(raw_path) or s['run_id']!=raw['manifest']['run_id'] or s['dataset_sha256']!=digest(raw['dataset']):
        raise ValueError('diagnostic report lineage mismatch')
    lines=['# CIB M4b exploratory wording diagnostic','',
        'Main means use all planned branches/labels within each scenario and equal scenarios, separately by wording. Controls and repeats are separate. Missing scores remain missing. Lower losses are better; positive quantized-minus-reference change means larger loss. Wordings and labels remain related observations, not independent scenario samples.','',
        'Primary parser outer-json-fence-v1 accepts bare strict JSON or exactly one complete outer unlabeled/lowercase-json triple-backtick fence with newlines around the body; exactly probability must contain a finite JSON number in [0,1]. No prose extraction, repairs, duplicate keys, extra fields or multiple answers. Strict compliance is separately measured over all eligible EOS completions, including malformed text.','',
        '## Coverage','',
        '| Deployment / wording (trial0) | Planned | Executed | Completed eligible | Primary scoreable/planned | Strict compliant/completed |',
        '| --- | ---: | ---: | ---: | ---: | ---: |']
    for d,v in s['deployments'].items():
        for w,c in [('all incl repeats',v['coverage'])]+[(w,g['coverage']) for w,g in v['groups'].items()]:
            lines.append(f"| {d} / {w} | {c['planned']} | {c['executed']} | {c['completed_eligible']} | {c['primary_scoreable']}/{c['planned']} | {c['strict_compliant']}/{c['strict_denominator']} |")
    lines+=['','## Numerical results','',
        '| Deployment | Wording | Metric | Mean | Scoreable/planned terms | Complete/planned scenarios |','| --- | --- | --- | ---: | ---: | ---: |']
    for d,v in s['deployments'].items():
        for w,g in v['groups'].items():
            for m,values in g['metrics'].items():
                lines.append(f"| {d} | {w} | {m} | {number(values['mean'])} | {values['scoreable']}/{values['planned']} | {values['complete_scenarios']}/3 |")
    lines+=['','## Likelihood controls and baselines','',
        '| Deployment | Wording | Correct/planned | Primary scoreable/planned | Mean absolute error | Unchanged-prior posterior loss (12/12 analytic targets) |',
        '| --- | --- | ---: | ---: | ---: | ---: |']
    for d,v in s['deployments'].items():
        for w,g in v['groups'].items():
            c=g['likelihood'];lines.append(f"| {d} | {w} | {c['correct']}/{c['planned']} | {c['scoreable']}/{c['planned']} | {number(c['absolute_error'])} | {number(g['unchanged_prior_posterior_baseline'])} |")
    lines+=['','Correct uses 1e-6 representation tolerance, not a behavioral updating margin. Analytic baselines are hypothetical, not model responses. Their coverage is 12/12 post targets per wording. Full planned-set posterior loss bounds, metric-specific denominators and scenario/condition diagnostics follow; bounds concern missing outcomes, not sampling uncertainty.','',
        '## Paired deployment changes','',literal(s.get('paired_changes','Single larger reference only; no quantization comparison.')),'',
        '## Competence screens and grouped diagnostics','']
    for d,v in s['deployments'].items():
        lines += [f'### {d}','',f"Exploratory suitability screen passes: **{v['suitability_pass']}**.",'',literal(v['suitability_checks']),
            literal({w:{k:g[k] for k in ('scenario_scores','condition_scores','posterior_loss_bounds')} for w,g in v['groups'].items()}),'',
            'Status counts: '+literal(v['coverage']['statuses']),'Repeat comparisons: '+literal(v['repeats']),'Cost: '+literal(v['cost']),'',
            'Every main condition and all controls: '+literal(v['condition_rows'])+literal(v['controls']),'']
    lines+=['## Exact saved inputs and all attempt histories','',
        'Each request includes grouping and trial identity. Raw text is escaped. Original token streams and loaded metadata remain in the run journal; raw snapshots retain exact rendered text and token IDs.','']
    for r in raw['requests']:
        attempts=[{k:a.get(k) for k in ('attempt_index','timestamp','text','status','stop_reason','error','actual','cache_identity','generation_wall_seconds')} for a in raw['attempts'] if a['request_id']==r['request_id']]
        lines += [literal(dict(request=r,attempts=attempts,score=s['observations'][r['request_id']])),'']
    lines+=['## Configuration and lineage','',f"Raw `{raw_path}` SHA-256 `{s['raw_sha256']}`; scores `{scores_path}` SHA-256 `{file_hash(scores_path)}`.",
        f"Scorer `{s['scorer_version']}` source `{s['source_sha256']}`; parser implementation `{s['parser_implementation_sha256']}`.",
        literal(raw['dataset']),literal(raw['manifest']['config']),literal(raw['manifest']['code'])]
    with Path(output).open('x') as f:f.write('\n'.join(lines)+'\n')
