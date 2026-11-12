"""Readable, escaped pilot report from immutable saved outputs."""
from pathlib import Path
from statistics import mean
from .records import read, file_hash, digest, key
from .pipeline import validate_raw
from .report import literal, number
from .pilot import METRICS
from .scoring import score_attempt


def report(raw_path, scores_path, output):
    raw,s=read(raw_path),read(scores_path)
    validate_raw(raw)
    if (s['schema_version']!='cib.pilot-scores.v1' or s['raw_sha256']!=file_hash(raw_path)
            or s['dataset_sha256']!=digest(raw['dataset']) or s['run_id']!=raw['manifest']['run_id']):
        raise ValueError('pilot score lineage mismatch')
    obs={o['request_id']:o for o in s['observations']}
    requests={r['request_id']:r for r in raw['requests']}
    latest={a['request_id']:a for a in raw['attempts']}
    ds=s['deployments']
    reference_loss = ds['reference']['metrics']['posterior_error']['mean']
    baseline_loss = s['baselines']['unchanged-prior']['posterior_error']['mean']
    assessment = (
        'The reference does not beat the unchanged-prior posterior-loss baseline on the full pilot. '
        'This pilot therefore does not establish adequate reference updating competence for a frozen study. '
        if reference_loss is not None and reference_loss >= baseline_loss else
        'Reference competence must be assessed against the unchanged-prior baseline and controls below. ')
    lines=['# CIB exploratory pilot v1','',
        'Qwen/Qwen2.5-1.5B-Instruct at `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`: original BF16 reference versus locally derived 4-bit affine/group-64, both MLX on the same 64 GiB M4 Max. This fixed development instrument measures numerical probability reporting and updating, **not empirical uncertainty calibration**. No preservation or general quantization claim follows.','',
        assessment + 'The workflow is operationally complete; instrument validation remains a substantive next dependency. Numerical variation across scenarios is useful for diagnosis, but shared numerical patterns, likelihood-control failures and irrelevant drift limit interpretation. Revise wording or reference selection only in a new exploratory version, then test fresh tasks before freezing a protocol.','',
        '## Protocol and coverage','',
        'Primary parser: `outer-json-fence-v1`, unchanged implementation from M3. Accept bare strict JSON or one complete outer triple-backtick fence, unlabeled or lowercase `json`, with newlines separating the body. Only whitespace may surround it. Exactly the `probability` field must contain a finite JSON number in [0,1]. Extra prose/answers, duplicate keys, invalid values, nested/multiple fences and repairs are rejected. Strict bare-JSON compliance is a separate diagnostic.','',
        'The allocation was recorded before generation: 12 base scenarios in three wording clusters, four shared numerical patterns, three evidence branches, complementary label variants and self-contained pre/post requests. Each branch has its own pre answer. Main metrics use trial 0 only: 144 requests per deployment. Sixteen controls and twelve fixed trial-1 repeats are separate. Templates, branches, labels and repeats do not create independent scenario samples.','',
        '| Deployment / allocation | Planned | Executed | Completed eligible | Primary scoreable / planned | Strict compliant / completed eligible |',
        '| --- | ---: | ---: | ---: | ---: | ---: |']
    for d in ds:
        for name in ('coverage','main_coverage','control_coverage','repeat_coverage'):
            c=ds[d][name]
            lines.append(f"| {d} / {name} | {c['planned']} | {c['executed']} | {c['completed_eligible']} | {c['primary_scoreable']}/{c['planned']} | {c['strict_compliant']}/{c['strict_denominator']} |")
    lines+=['', 'Completed eligible means terminal EOS completion, including malformed answers. Length stops, explicit refusals and infrastructure errors remain distinct; unexecuted work remains not_attempted. Main numerical results require complete eligible conditions within scenario and complete scenarios for a full-set point estimate. Missing scores stay null. The full-set bounds assign unknown posterior losses [0,1]; these are missing-outcome bounds, not sampling intervals. All results below use the coverage above plus their metric-specific denominators.','',
        '## Main numerical results','',
        'All four metrics are losses: lower is better. Positive paired quantized-minus-reference changes mean larger loss. Equal conditions/labels within each scenario, equal scenarios.','',
        '| Metric | BF16 mean (scoreable/planned terms) | 4-bit mean (scoreable/planned terms) | Paired change | Complete paired scenarios / planned |',
        '| --- | ---: | ---: | ---: | ---: |']
    for m in METRICS:
        a,b=[ds[d]['metrics'][m] for d in ('reference','quantized')]; p=s['paired_metrics'][m]
        lines.append(f"| {m} | {number(a['mean'])} ({a['scoreable']}/{a['planned']}) | {number(b['mean'])} ({b['scoreable']}/{b['planned']}) | {number(p['quantized_minus_reference'])} | {p['complete_paired_scenarios']}/12 |")
    lines+=['','Full planned posterior-loss contrast and missing-loss bounds: '+literal(s['comparison']),'',
        '## Condition and template diagnostics','',
        '| Group | Metric | BF16 mean (scoreable/planned) | 4-bit mean (scoreable/planned) | 4-bit minus BF16 |',
        '| --- | --- | ---: | ---: | ---: |']
    for grouping in ('by_condition','by_template'):
        for group in ds['reference'][grouping]:
            for m in METRICS:
                a,b=[ds[d][grouping][group][m] for d in ('reference','quantized')]
                if not a['planned']: continue
                delta=None if a['mean'] is None or b['mean'] is None else b['mean']-a['mean']
                lines.append(f"| {group} | {m} | {number(a['mean'])} ({a['scoreable']}/{a['planned']}) | {number(b['mean'])} ({b['scoreable']}/{b['planned']}) | {number(delta)} |")
    lines+=['','## Per-scenario results','',
        '| Scenario (template cluster) | Metric | BF16 mean (scoreable/planned) | 4-bit mean (scoreable/planned) | Paired change |',
        '| --- | --- | ---: | ---: | ---: |']
    for scenario in raw['dataset']['scenarios']:
        name=scenario['scenario_id']
        for m in METRICS:
            a,b=[s['scenario_scores'][d][name][m] for d in ('reference','quantized')]
            delta=None if a['mean'] is None or b['mean'] is None else b['mean']-a['mean']
            lines.append(f"| {name} ({scenario['cluster_id']}) | {m} | {number(a['mean'])} ({a['scoreable']}/{a['planned']}) | {number(b['mean'])} ({b['scoreable']}/{b['planned']}) | {number(delta)} |")
    lines+=['','## Controls and baselines','',
        'Controls are independently scored against supplied numerical facts or arithmetic answers. Accuracy counts correct/planned, including missing/invalid responses as unsuccessful operations, while numerical errors remain missing. Correct uses absolute error ≤1e-9 only for representation. Format-control value accuracy and strict format compliance are distinct.','',
        '| Kind | BF16 correct/planned (primary scoreable) | 4-bit correct/planned (primary scoreable) |',
        '| --- | ---: | ---: |']
    for k in ds['reference']['control_summary']:
        a,b=[ds[d]['control_summary'][k] for d in ('reference','quantized')]
        lines.append(f"| {k} | {a['correct']}/{a['planned']} ({a['scoreable']}/{a['planned']}) | {b['correct']}/{b['planned']} ({b['scoreable']}/{b['planned']}) |")
    lines+=['','Synthetic analytic baselines, **not model observations**. All 72 main condition-label pairs are defined (24 for drift); coverage is 72/72 hypothetical, no generation or parser.','',
        '| Baseline | Posterior error | Prior error | Update error | Irrelevant drift |','| --- | ---: | ---: | ---: | ---: |']
    for name,values in s['baselines'].items():
        lines.append('| '+name+' | '+' | '.join(f"{number(values[m]['mean'])} ({values[m]['scoreable']}/{values[m]['planned']})" for m in METRICS)+' |')
    lines+=['','## Measurement quality, missingness and cost','',
        'Label sensitivity is |q_original + q_swapped − 1|: zero means complement consistency, which can coexist with an incorrect answer. Because the swap complements H and changes the numerical prior, this is not an isolated test of surface-label bias. Exact answers use 1e-9 for numerical representation. Repeat comparisons cover the fixed twelve calls on t1-s1 and do not estimate population or sampling variance.','']
    for d in ds:
        v=ds[d]; repeats=v['repeats']; diffs=[r['absolute_probability_difference'] for r in repeats]
        lines += [f"### {d}", '',
            'Main primary coverage: '+str(v['main_coverage']['primary_scoreable'])+'/144. Status counts over all planned observations: '+literal(v['coverage']['statuses']),
            'Difficulty / floor and ceiling diagnostic (posterior exact count and loss ranges with explicit denominators): '+literal(v['difficulty']),
            'Complement sensitivity: '+literal(v['label_sensitivity']),
            f"Repeats: exact text agreement {sum(r['text_equal'] for r in repeats)}/{len(repeats)}; status agreement {sum(r['status_equal'] for r in repeats)}/{len(repeats)}; scoreable probability pairs {sum(x is not None for x in diffs)}/{len(diffs)}; maximum probability difference {number(max(diffs) if diffs and all(x is not None for x in diffs) else None)}.", '',
            'Cost (generation wall time includes per-call stream writing; excludes startup/hashing/loading; MLX allocator and process RSS are distinct decimal-byte counters, peaks include loading and previous calls in that process): '+literal(v['cost']), '']
    lines += ['The unchanged-prior baseline supplies a direct competence check: lower posterior loss indicates useful updating on this fixed instrument. Reading/likelihood/arithmetic controls diagnose prerequisite competence but cannot establish that deployment differences are independent of capability. Repeated numerical patterns and only three wording clusters limit useful variation and generalization. Check the per-scenario range and exact-answer frequency before treating the instrument as sensitive; no result here validates a final-study instrument.','',
        'Sequential reference-first batching, warmed file caches, normal machine activity, backend-defined accumulation and different dense/quantized kernels limit causal and performance interpretation. No textual refusal classifier is inferred: a prose refusal is malformed unless an explicit backend refusal status exists. Greedy repeats test local reproducibility only.','',
        '## Representative raw examples','',
        'Diagnostic selection fixed before generation: first exact posterior answer, largest posterior error, first strict failure, largest paired improvement and largest paired regression. These examples are not a filtered analysis set. Full observations and condition losses follow.','']
    rows=s['condition_scores']; selected=[]
    good=next((r for r in rows if r['posterior_error'] is not None and r['posterior_error']<=1e-9),None)
    if good: selected.append(('First exact posterior',good['post_request_id']))
    else: lines+=['No exact-correct posterior answer is present.','']
    valid=[r for r in rows if r['posterior_error'] is not None]
    if valid: selected.append(('Largest posterior error',max(valid,key=lambda r:r['posterior_error'])['post_request_id']))
    fail=next((r for r in requests.values() if latest[r['request_id']]['status']=='completed' and score_attempt(latest[r['request_id']])['status']=='malformed'),None)
    if fail: selected.append(('First strict-format failure',fail['request_id']))
    else: lines+=['No strict-format failure occurred.','']
    pairs=[]
    for a in rows:
        if a['deployment_id']!='reference': continue
        b=next(b for b in rows if b['deployment_id']=='quantized' and all(a[k]==b[k] for k in ('scenario_id','condition_id','label_variant')))
        if a['posterior_error'] is not None and b['posterior_error'] is not None: pairs.append((b['posterior_error']-a['posterior_error'],a,b))
    if pairs:
        for title,entry in [('Largest paired improvement',min(pairs,key=lambda x:x[0])),('Largest paired regression',max(pairs,key=lambda x:x[0]))]:
            lines += [f"### {title}",'',f"Paired posterior-loss change {number(entry[0])}; both post responses primary-scoreable (2/2). Target {entry[1]['posterior']}. Labels identify the extremum; its observed sign determines whether it is an improvement or regression.",'']
            for row in entry[1:]: selected.append((title+' / '+row['deployment_id'],row['post_request_id']))
    for title,rid in selected:
        r=requests[rid]; a=latest[rid]
        lines += [f"### {title}: {r['deployment_id']} / {r['scenario_id']} / {r['condition_id']} / {r['label_variant']}",'',
            literal(r['input']),literal(dict(request_id=rid,text=a['text'],status=a['status'],primary_score=obs[rid])), '']
    lines+=['## Complete condition losses and targets','',literal(rows),'',
        '## Independently scored controls','',literal({d:ds[d]['controls'] for d in ds}),'',
        '## Every planned request and all attempts','',
        'Exact tokenized inputs, loaded metadata, token streams and full immutable attempts remain in the raw artifact and original journal. Below are all exact model-visible inputs and all attempt outcomes.','']
    for rid,r in requests.items():
        history=[{k:a.get(k) for k in ('attempt_index','status','stop_reason','text','error','timestamp','generation_wall_seconds','cache_identity')} for a in raw['attempts'] if a['request_id']==rid]
        lines += [literal(dict(request=r,attempts=history,score=obs[rid])),'']
    lines += ['## Lineage and frozen configuration','',
        f"Raw: `{raw_path}` SHA-256 `{s['raw_sha256']}`.",
        f"Scores: `{scores_path}` SHA-256 `{file_hash(scores_path)}`.",
        f"Parser implementation SHA-256 `{s['parser_implementation_sha256']}`; scorer `{s['scorer_version']}` source SHA-256 `{s['scorer_source_sha256']}`.",'',literal(s['protocol']),literal(raw['dataset']),literal(raw['manifest']['code'])]
    with Path(output).open('x') as f: f.write('\n'.join(lines)+'\n')
