"""Offline source-fidelity development only; no inference entry point."""
import argparse
from importlib.resources import files
import json
from pathlib import Path

from .records import digest, file_hash, read, write_new
from .review import packet, RUBRIC

VERSION='source-fidelity-mechanical-v1'
FORMAT=('Return only JSON with exactly "abstain" (boolean) and "claims" (array). '
        'Each claim has exactly "text" (string), "citations" (array of source IDs), '
        'and "quotes" (array of objects with exactly "source_id" and "text" strings). '
        'Use supplied documents only. Set abstain true with no claims if the sources are insufficient.')


def load():
    return read(files('cib').joinpath('data/source-fidelity-dev-v1.json'))


def messages(s):
    return [dict(role='user',content='Supplied fictional documents:\n'+
        '\n'.join(f'[{k}] {v}' for k,v in s['sources'].items())+'\nQuestion: '+s['question']+'\n'+FORMAT)]


def parse(text):
    def pairs(items):
        if len(items)!=len(dict(items)):
            raise ValueError('duplicate keys')
        return dict(items)
    obj=json.loads(text,object_pairs_hook=pairs)
    if not isinstance(obj,dict) or set(obj)!={'abstain','claims'} or type(obj['abstain']) is not bool or not isinstance(obj['claims'],list):
        raise ValueError('invalid response schema')
    if obj['abstain'] and obj['claims']:
        raise ValueError('abstention with claims')
    for c in obj['claims']:
        if not isinstance(c,dict) or set(c)!={'text','citations','quotes'} or not isinstance(c['text'],str) or not c['text'].strip():
            raise ValueError('invalid claim')
        if not isinstance(c['citations'],list) or not all(isinstance(i,str) for i in c['citations']):
            raise ValueError('invalid citations')
        if not isinstance(c['quotes'],list):
            raise ValueError('invalid quotes')
        for q in c['quotes']:
            if not isinstance(q,dict) or set(q)!={'source_id','text'} or not all(isinstance(v,str) for v in q.values()):
                raise ValueError('invalid quote')
    return obj


def score(s, text):
    try:
        obj=parse(text)
    except (ValueError,TypeError):
        return dict(status='malformed',mechanical=None,semantic_support=None,coverage=0)
    claims=obj['claims']
    ids=[i for c in claims for i in c['citations']]
    quotes=[q for c in claims for q in c['quotes']]
    valid=sum(i in s['sources'] for i in ids)
    accurate=sum(bool(q['text']) and q['source_id'] in s['sources'] and
        q['text'] in s['sources'][q['source_id']] for q in quotes)
    return dict(status='abstained' if obj['abstain'] else 'answered' if claims else 'empty',
        coverage=int(bool(claims)),claims=len(claims),abstain=obj['abstain'],
        abstention_target_correct=int(obj['abstain']==(not s['annotations']['answerable'])),
        mechanical=dict(valid_citation_ids=valid,citation_ids=len(ids),
            citation_id_precision=valid/len(ids) if ids else None,
            accurate_quote_spans=accurate,quote_spans=len(quotes),
            quote_exactness=accurate/len(quotes) if quotes else None,
            claims_with_citations=sum(bool(c['citations']) for c in claims)),
        semantic_support=None,unqualified_fidelity_score=None,
        interpretation='Mechanical properties only; human semantic support and relevance pending. Empty/abstained answers never receive a perfect fidelity score.')


def fixture(output):
    data=load()
    output.mkdir(parents=True,exist_ok=False)
    scenarios={s['scenario_id']:s for s in data['scenarios']}
    observations=[dict(response_id=r['response_id'],scenario_id=r['scenario_id'],
        messages=messages(scenarios[r['scenario_id']]),text=json.dumps(r['response']),status='completed') for r in data['responses']]
    raw=dict(label='SYNTHETIC source-fidelity development fixtures; not measured model performance',
        task_version=data['task_version'],dataset_sha256=digest(data),observations=observations)
    write_new(output/'raw.json',raw)
    regenerate(output/'raw.json',output/'scores.json')
    return raw


def regenerate(raw_path,output):
    raw=read(raw_path);data=load()
    if raw['task_version']!=data['task_version'] or raw['dataset_sha256']!=digest(data) or raw.get('label')!='SYNTHETIC source-fidelity development fixtures; not measured model performance':
        raise ValueError('incompatible fixture lineage')
    expected={r['response_id']:r for r in data['responses']}
    scenarios={s['scenario_id']:s for s in data['scenarios']}
    if len(raw['observations'])!=len(expected) or {a['response_id'] for a in raw['observations']}!=set(expected):
        raise ValueError('missing or unknown fixture response')
    scores=[]
    for a in raw['observations']:
        r=expected[a['response_id']]
        if a['scenario_id']!=r['scenario_id'] or a['messages']!=messages(scenarios[r['scenario_id']]) or a['status']!='completed':
            raise ValueError('fixture input ownership mismatch')
        scores.append(dict(response_id=a['response_id'],scenario_id=a['scenario_id'],**score(scenarios[a['scenario_id']],a['text'])))
    result=dict(label=raw['label'],task_version=data['task_version'],scorer_version=VERSION,
        raw_sha256=file_hash(raw_path),dataset_sha256=digest(data),source_sha256=file_hash(__file__),
        planned=len(expected),answer_coverage=sum(s['coverage'] for s in scores),
        abstained=sum(s['status']=='abstained' for s in scores),scores=scores,human_validation=False)
    write_new(output,result)
    return result


def review_packet(raw_path,output):
    raw=read(raw_path);data=load()
    # Apply the same lineage validation as regeneration without writing artifacts.
    if raw['task_version']!=data['task_version'] or raw['dataset_sha256']!=digest(data):
        raise ValueError('incompatible task version')
    scenarios={s['scenario_id']:s for s in data['scenarios']}
    items,mapping=[],{}
    for a in raw['observations']:
        s=scenarios[a['scenario_id']]
        item_id='review-'+digest([data['task_version'],digest(data),a['response_id']])[:24]
        mapping[item_id]=dict(response_id=a['response_id'],scenario_id=a['scenario_id'],kind='synthetic_fixture')
        items.append(dict(item_id=item_id,task_version=data['task_version'],scenario_id=s['scenario_id'],
            sources=s['sources'],question=s['question'],options=None,keys=s['annotations'],
            intended_construct='Source fidelity: semantic support, citation attribution, accurate quotation, appropriate abstention',
            conversation=a['messages']+[dict(role='assistant',content=a['text'])],
            diagnostic_mapping=score(s,a['text']),human_fields=dict.fromkeys(RUBRIC),
            label='Synthetic fixture; agent annotations are review aids, not human ratings'))
    return packet(items,mapping,output)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=('fixture','score','review'))
    p.add_argument('--raw',type=Path)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.command=='fixture': fixture(a.output)
    elif a.command=='score': regenerate(a.raw,a.output)
    else: review_packet(a.raw,a.output)


if __name__=='__main__':
    main()
