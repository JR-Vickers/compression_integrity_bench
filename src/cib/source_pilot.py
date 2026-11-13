"""Frozen bounded source-fidelity pilot; saved-output analysis never loads MLX."""
import argparse
import copy
import fcntl
import json
from pathlib import Path
import time
import traceback

from . import source_fidelity as sf, review
from .records import digest, file_hash, read
from .runner import write_new, interrupted, now, deployment_registry, validate_run_config
from .pipeline import source_hash, git_state

CONFIG = Path('configs/source-fidelity-pilot-v1.json')
MODELS = ('reference', 'quantized')
VERSION = 'source-fidelity-pilot-scorer-v1'


def allocation(data, protocol):
    return [dict(slot=s['scenario_id']+'-main', scenario_id=s['scenario_id'], trial=0) for s in data['scenarios']] + [
        dict(slot=s+'-repeat', scenario_id=s, trial=1) for s in protocol['repeat_scenarios']]


def prepare(root, config=CONFIG):
    p=read(config);data=read(p['dataset'])
    if digest(data)!=p['dataset_sha256'] or data['task_version']!=p['task_version']:
        raise ValueError('dataset/protocol version mismatch')
    if len(data['scenarios'])!=8 or sum(s['annotations']['answerable'] for s in data['scenarios'])!=6:
        raise ValueError('incorrect scenario allocation')
    base=read(p['pair_config']);prepared=read(p['pair_prepared'])
    validate_run_config(base)
    if prepared['config_sha256']!=digest(base):
        raise ValueError('preparation mismatch')
    config=copy.deepcopy(base);config['generation']['max_tokens']=p['max_tokens']
    models={m:dict(config=config, prepared=prepared, deployment=m,
                  registry=deployment_registry(base,prepared)[m]) for m in MODELS}
    frozen=dict(schema_version='cib.source-fidelity-plan.v1',created_at=now(),dataset=data,
        protocol=p,models=models,allocation=allocation(data,p),source_sha256=source_hash(),git=git_state())
    root.mkdir(parents=True,exist_ok=False)
    write_new(root/'protocol.json',frozen)
    write_new(root/'protocol-sha256.json',digest(frozen))
    return frozen


def plan(root):
    p=read(root/'protocol.json')
    if digest(p)!=read(root/'protocol-sha256.json') or p['allocation']!=allocation(p['dataset'],p['protocol']):
        raise ValueError('frozen plan changed')
    return p


def histories(root, model):
    result={}
    for start in sorted((root/model).glob('*.start.json')):
        end=start.with_name(start.name.replace('.start.json','.result.json'))
        a=read(end) if end.exists() else interrupted(start)
        result[a['slot']]=a
    return result


def run(root, model, limit, factory=None):
    if limit<0: raise ValueError('negative limit')
    with (root/'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        p=plan(root)
        if p['source_sha256']!=source_hash(): raise ValueError('code changed since freeze')
        folder=root/model;folder.mkdir(exist_ok=True)
        attempts=histories(root,model);spec=p['models'][model];adapter=None;executed=0
        scenarios={s['scenario_id']:s for s in p['dataset']['scenarios']}
        started=time.monotonic()
        for slot in p['allocation']:
            if slot['slot'] in attempts: continue
            if executed>=limit: break
            all_attempts=[a for m in MODELS for a in histories(root,m).values()]
            if len(all_attempts)>=p['protocol']['max_attempts']: raise ValueError('attempt ceiling')
            if sum(a.get('generation_wall_seconds',0) for a in all_attempts)+time.monotonic()-started>p['protocol']['max_wall_seconds']: raise ValueError('wall ceiling')
            if sum(f.stat().st_size for f in root.rglob('*') if f.is_file())>p['protocol']['max_disk_bytes']: raise ValueError('disk ceiling')
            if any(a.get('mlx_peak_bytes',0)>p['protocol']['max_mlx_peak_bytes'] for a in all_attempts): raise ValueError('memory ceiling')
            a=dict(**slot,model=model,timestamp=now(),messages=sf.messages(scenarios[slot['scenario_id']]),
                   deployment_sha256=digest(spec),decoding=spec['config']['generation'],
                   status='infrastructure_error',text='',stop_reason=None,error=None)
            base=folder/slot['slot']
            # Setup/render failures count against the global ceiling and are never retried.
            write_new(str(base)+'.start.json',a);tick=time.monotonic()
            try:
                if adapter is None:
                    if factory is None:
                        from .mlx_adapter import MLXAdapter
                        factory=MLXAdapter
                    adapter=factory(spec['config'],spec['prepared'],model)
                    if not (folder/'loaded.json').exists():
                        write_new(folder/'loaded.json',adapter.metadata)
                    elif read(folder/'loaded.json')!=adapter.metadata:
                        raise ValueError('loaded metadata changed')
                a['actual']=adapter.render({'messages':a['messages']})
                write_new(str(base)+'.input.json',a['actual'])
                with Path(str(base)+'.stream.jsonl').open('xb') as stream:
                    def emit(event):
                        stream.write((json.dumps(event)+'\n').encode());stream.flush()
                        a['text']+=event['text'];a['stop_reason']=event['finish_reason']
                    a.update(adapter.generate(a['actual'],emit))
                if a['stop_reason'] not in ('stop','length'): raise ValueError('unknown stop reason')
                a['status']='completed' if a['stop_reason']=='stop' else 'truncated'
            except Exception:
                a['error']=traceback.format_exc()
            a['generation_wall_seconds']=time.monotonic()-tick
            write_new(str(base)+'.result.json',a);attempts[a['slot']]=a;executed+=1
            if a['status']=='infrastructure_error': break
        return executed


def validate(raw):
    p=raw['plan']
    if raw['schema_version']!='cib.source-fidelity-raw.v1' or raw['plan_sha256']!=digest(p):
        raise ValueError('raw plan mismatch')
    if p['allocation']!=allocation(p['dataset'],p['protocol']) or digest(p['dataset'])!=p['protocol']['dataset_sha256']:
        raise ValueError('allocation/dataset mismatch')
    scenarios={s['scenario_id']:s for s in p['dataset']['scenarios']}
    slots={s['slot']:s for s in p['allocation']}
    if set(raw['attempts'])!=set(MODELS): raise ValueError('deployment mismatch')
    for m,attempts in raw['attempts'].items():
        for slot,a in attempts.items():
            if slot not in slots or any(a[k]!=v for k,v in slots[slot].items()): raise ValueError('slot mismatch')
            if a['model']!=m or a['deployment_sha256']!=digest(p['models'][m]): raise ValueError('deployment mismatch')
            if a['status'] not in ('completed','truncated','infrastructure_error'):
                raise ValueError('unknown inference status')
            if a['status']=='completed' and a['stop_reason']!='stop' or a['status']=='truncated' and a['stop_reason']!='length':
                raise ValueError('status/stop mismatch')
            if a['messages']!=sf.messages(scenarios[a['scenario_id']]) or a['decoding']!=p['models'][m]['config']['generation']:
                raise ValueError('input ownership mismatch')
    if sum(map(len,raw['attempts'].values()))>p['protocol']['max_attempts']: raise ValueError('budget exceeded')
    for slot in slots:
        a=raw['attempts']['reference'].get(slot);b=raw['attempts']['quantized'].get(slot)
        if a and b and a.get('actual') and b.get('actual') and a['actual']!=b['actual']:
            raise ValueError('rendered/tokenized pairing mismatch')
    return raw


def snapshot(root, output):
    p=plan(root)
    with (root/'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        raw=dict(schema_version='cib.source-fidelity-raw.v1',label='REAL exploratory source-fidelity pilot; human validation pending',
                 plan=p,plan_sha256=digest(p),attempts={m:histories(root,m) for m in MODELS})
        validate(raw);write_new(output,raw)
    return raw


def extract(text):
    """Prespecified diagnostic wrapper only. Never infer or repair answer content."""
    stripped=text.strip()
    for opener in ('```json\n','```\n'):
        if stripped.startswith(opener) and stripped.endswith('\n```'):
            stripped=stripped[len(opener):-4];break
    sf.parse(stripped)
    return stripped


def mechanical(s,a):
    if a is None:
        return dict(status='not_attempted',strict_compliance=False,mechanically_extractable=False,
                    raw_content_available=False, human_assessability=None,mechanical=None,coverage=None)
    result=dict(status=a['status'],strict_compliance=False,mechanically_extractable=False,
                raw_content_available=bool(a['text'].strip()),human_assessability=None,
                mechanical=None,coverage=None,abstain=None,empty_answer=None)
    # Completed refusals require human interpretation. Truncation/infra stay separate.
    if a['status']!='completed': return result
    try:
        sf.parse(a['text']);result['strict_compliance']=True
    except (ValueError,TypeError): pass
    try:
        text=extract(a['text']);sc=sf.score(s,text)
        result.update(mechanically_extractable=True,mechanical=sc['mechanical'],coverage=sc['coverage'],
                      abstain=sc['abstain'],empty_answer=sc['status']=='empty',parsed_status=sc['status'],
                      abstention_target_correct=sc['abstention_target_correct'])
    except (ValueError,TypeError):
        result['parsed_status']='malformed'
    return result


def review_id(p,m,slot):
    return 'review-'+digest([p['protocol']['task_version'],digest(p['dataset']),m,slot])[:24]


def semantic(public, reviews, item_id):
    for r in reviews: review.validate_submission(public,r,reviews)
    fields=['task_success','answer_completeness','semantic_source_support','attribution',
            'quotation_relevance','abstention_appropriateness','human_assessability','response_behavior']
    result={}
    for field in fields:
        individuals=[dict(reviewer_id=r['reviewer_id'],value=row['ratings'][field],submission_sha256=digest(r))
            for r in reviews if r['kind']=='human' and r['record_type']=='individual'
            for row in r['ratings'] if row['item_id']==item_id and row['ratings'][field] is not None]
        adjudications=[dict(reviewer_id=r['reviewer_id'],value=row['ratings'][field],submission_sha256=digest(r))
            for r in reviews if r['kind']=='human' and r['record_type']=='adjudication'
            for row in r['ratings'] if row['item_id']==item_id and row['ratings'][field] is not None]
        if len({r['reviewer_id'] for r in individuals})!=len(individuals):
            raise ValueError('multiple individual versions for one reviewer; select one explicitly')
        if len(adjudications)>1: raise ValueError('multiple adjudications; select one explicitly')
        values={r['value'] for r in individuals}
        result[field]=dict(individuals=individuals,adjudications=adjudications,
            provisional=individuals[0]['value'] if individuals else None,
            consensus=next(iter(values)) if len(values)==1 else None,
            disagreement=len(values)>1,adjudicated=adjudications[0]['value'] if adjudications else None)
    return result


def calculate(raw,public=None,reviews=()):
    validate(raw);p=raw['plan'];scenarios={s['scenario_id']:s for s in p['dataset']['scenarios']}
    if public and public.get('source_raw_sha256')!=digest(raw): raise ValueError('review/raw lineage mismatch')
    if reviews and public is None: raise ValueError('reviews need packet')
    rows=[]
    for slot in p['allocation']:
        for m in MODELS:
            a=raw['attempts'][m].get(slot['slot']);s=scenarios[slot['scenario_id']]
            rows.append(dict(**slot,model=m,answerable=s['annotations']['answerable'],quote_required=s['annotations']['quote_required'],
                result=mechanical(s,a),semantic=semantic(public,reviews,review_id(p,m,slot['slot'])) if public and slot['trial']==0 else None))
    summary={}
    for m in MODELS:
        main=[r for r in rows if r['model']==m and r['trial']==0]; rr=[r['result'] for r in main]
        success=[r['semantic']['task_success'] for r in main if r['semantic']]
        summary[m]=dict(planned_main=8,attempted_main=sum(r['status']!='not_attempted' for r in rr),
            completed=sum(r['status']=='completed' for r in rr),strict_compliance=sum(r['strict_compliance'] for r in rr),
            mechanically_extractable=sum(r['mechanically_extractable'] for r in rr),
            raw_content_available=sum(r['raw_content_available'] for r in rr),
            answers=sum(r.get('coverage')==1 for r in rr),empty_answers=sum(r.get('empty_answer') is True for r in rr),
            abstentions=sum(r.get('abstain') is True for r in rr),
            answerable_abstentions=sum(r['result'].get('abstain') is True for r in main if r['answerable']),
            insufficient_abstentions=sum(r['result'].get('abstain') is True for r in main if not r['answerable']),
            provisional_success_coverage=sum(s['provisional'] in ('pass','fail') for s in success),
            provisional_pass=sum(s['provisional']=='pass' for s in success),
            provisional_full_set_success=sum(s['provisional']=='pass' for s in success)/8 if sum(s['provisional'] in ('pass','fail') for s in success)==8 else None,
            adjudicated_success_coverage=sum(s['adjudicated'] in ('pass','fail') for s in success),
            adjudicated_pass=sum(s['adjudicated']=='pass' for s in success),
            adjudicated_full_set_success=sum(s['adjudicated']=='pass' for s in success)/8 if sum(s['adjudicated'] in ('pass','fail') for s in success)==8 else None,
            repeats=[dict(scenario_id=s,main_present=(s+'-main') in raw['attempts'][m],repeat_present=(s+'-repeat') in raw['attempts'][m],
                exact_text_status_match=(raw['attempts'][m][s+'-main']['text'],raw['attempts'][m][s+'-main']['status'])==(raw['attempts'][m][s+'-repeat']['text'],raw['attempts'][m][s+'-repeat']['status']) if all(s+t in raw['attempts'][m] for t in ('-main','-repeat')) else None)
                for s in p['protocol']['repeat_scenarios']])
        for field in ('citation_ids','valid_citation_ids','quote_spans','accurate_quote_spans','claims','claims_with_citations'):
            summary[m][field]=sum((r['mechanical'] or {}).get(field,0) for r in rr)
        summary[m]['citation_id_precision']=(summary[m]['valid_citation_ids']/summary[m]['citation_ids'] if summary[m]['citation_ids'] else None)
        summary[m]['quote_exactness']=(summary[m]['accurate_quote_spans']/summary[m]['quote_spans'] if summary[m]['quote_spans'] else None)
        summary[m]['human_components']={}
        for field in ('task_success','answer_completeness','semantic_source_support','attribution','quotation_relevance','abstention_appropriateness','human_assessability','response_behavior'):
            entries=[r['semantic'][field] for r in main if r['semantic']]
            summary[m]['human_components'][field]=dict(planned=8,
                individual_rating_count=sum(len(e['individuals']) for e in entries),
                provisional_values=[e['provisional'] for e in entries],
                consensus_coverage=sum(e['consensus'] is not None for e in entries),
                disagreement_count=sum(e['disagreement'] for e in entries),
                adjudication_coverage=sum(e['adjudicated'] is not None for e in entries))
        summary[m]['strata']={}
        for name,answerable in (('answerable',True),('insufficient_source',False)):
            subset=[r for r in main if r['answerable']==answerable]
            labels=[r['semantic']['task_success'] for r in subset if r['semantic']]
            summary[m]['strata'][name]=dict(planned=len(subset),
                extracted=sum(r['result']['mechanically_extractable'] for r in subset),
                answers=sum(r['result'].get('coverage')==1 for r in subset),
                abstentions=sum(r['result'].get('abstain') is True for r in subset),
                provisional_determinate=sum(e['provisional'] in ('pass','fail') for e in labels),
                provisional_pass=sum(e['provisional']=='pass' for e in labels),
                adjudicated_determinate=sum(e['adjudicated'] in ('pass','fail') for e in labels),
                adjudicated_pass=sum(e['adjudicated']=='pass' for e in labels))
        # Claims count is attached to parsed score, reconstruct only mechanically extractable claims.
        summary[m]['claims']=sum(len(sf.parse(extract(raw['attempts'][m][r['slot']]['text']))['claims']) for r in main if r['result']['mechanically_extractable'])
    agreement={}
    for field in review.SOURCE_RUBRIC:
        if field=='notes': continue
        overlap=[r['semantic'][field] for r in rows if r['trial']==0 and r['scenario_id'] in p['protocol']['review']['second_reviewer_scenarios'] and r['semantic']]
        jointly=[e for e in overlap if len(e['individuals'])>=2]
        agreement[field]=dict(planned_overlap_responses=8,jointly_rated=len(jointly),
            exact_agreement=sum(len({r['value'] for r in e['individuals']})==1 for e in jointly),
            rate=sum(len({r['value'] for r in e['individuals']})==1 for e in jointly)/len(jointly) if jointly else None)
    return dict(schema_version=VERSION,raw_sha256=digest(raw),plan_sha256=digest(p),scorer_source_sha256=file_hash(__file__),
        mechanical_scorer=sf.VERSION,mechanical_source_sha256=file_hash(sf.__file__),review_packet_sha256=digest(public) if public else None,
        review_sha256=[digest(r) for r in reviews],summary=summary,rows=rows,overlap_agreement=agreement,
        human_validation='Only genuine human imports contribute; all unavailable labels stay null. No semantic inference from mechanics.')


def score_file(raw_path, output, packet_path=None, review_paths=()):
    write_new(output,calculate(read(raw_path),read(packet_path) if packet_path else None,[read(p) for p in review_paths]))


def report_file(raw_path,scores_path,output,packet_path=None,review_paths=()):
    raw=read(raw_path);scores=read(scores_path)
    if scores!=calculate(raw,read(packet_path) if packet_path else None,[read(p) for p in review_paths]): raise ValueError('score lineage mismatch')
    lines=['# Exploratory source-fidelity pilot','', 'Mechanical checks do not establish source support. Human labels remain pending unless imported. No preservation, equivalence or study readiness claim.','',
           '```json',json.dumps(scores['summary'],indent=2),'```','', '## Every planned case (repeats secondary)']
    for row in scores['rows']:
        a=raw['attempts'][row['model']].get(row['slot'])
        lines.extend(['',f"### {row['model']} {row['slot']}",'', '```json',json.dumps(row,indent=2),'```','', 'Raw response:', '', '    '+(a['text'].replace('\n','\n    ') if a else '[not attempted]')])
    with output.open('x') as f: f.write('\n'.join(lines)+'\n')


def export_review(raw_path,output):
    raw=read(raw_path);validate(raw);p=raw['plan'];items=[];mapping={}
    for s in p['dataset']['scenarios']:
        for m in MODELS:
            slot=s['scenario_id']+'-main';a=raw['attempts'][m].get(slot);key=review_id(p,m,slot)
            mapping[key]=dict(model=m,slot=slot,scenario_id=s['scenario_id'])
            items.append(dict(item_id=key,task_version=p['protocol']['task_version'],scenario_id=s['scenario_id'],
                sources=s['sources'],question=s['question'],keys=s['annotations'],
                conversation=sf.messages(s)+[dict(role='assistant',content=a['text'] if a else '[not attempted]')],
                inference_status=a['status'] if a else 'not_attempted',human_fields=dict.fromkeys(review.SOURCE_RUBRIC)))
    public=review.packet(items,mapping,output,p['protocol']['review']['order_seed'],rubric=review.SOURCE_RUBRIC,
        version=review.SOURCE_VERSION,metadata=dict(source_raw_sha256=digest(raw),selection='All 16 main responses; repeats excluded'))
    template=read(output/'template.json')
    write_new(output/'reviewer-1.json',template)
    second=copy.deepcopy(template);second['ratings']=[r for r in template['ratings'] if mapping[r['item_id']]['scenario_id'] in p['protocol']['review']['second_reviewer_scenarios']]
    write_new(output/'reviewer-2.json',second)
    review.readable(public,output/'packet.md',source=True)
    return public


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    a=sub.add_parser('prepare');a.add_argument('--run',type=Path,required=True)
    a=sub.add_parser('run');a.add_argument('--run',type=Path,required=True);a.add_argument('--deployment',choices=MODELS,required=True);a.add_argument('--limit',type=int,default=10)
    a=sub.add_parser('snapshot');a.add_argument('--run',type=Path,required=True);a.add_argument('--output',type=Path,required=True)
    for name in ('score','report','review'):
        a=sub.add_parser(name);a.add_argument('--raw',type=Path,required=True);a.add_argument('--output',type=Path,required=True)
        if name in ('score','report'):
            a.add_argument('--packet',type=Path);a.add_argument('--reviews',type=Path,nargs='*',default=[])
        if name=='report': a.add_argument('--scores',type=Path,required=True)
    a=parser.parse_args()
    if a.command=='prepare': prepare(a.run)
    elif a.command=='run': print(run(a.run,a.deployment,a.limit))
    elif a.command=='snapshot': snapshot(a.run,a.output)
    elif a.command=='review': export_review(a.raw,a.output)
    elif a.command=='score': score_file(a.raw,a.output,a.packet,a.reviews)
    else: report_file(a.raw,a.scores,a.output,a.packet,a.reviews)


if __name__=='__main__': main()
