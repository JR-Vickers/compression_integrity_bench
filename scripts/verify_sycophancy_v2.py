"""Tokenizer-only preflight or compact saved-response audit; never generation."""
import argparse
from pathlib import Path
from cib import sycophancy_v2 as v2
from cib.records import read, write_new, digest, file_hash


def tokenizer(spec):
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(spec['prepared']['reference']['path'],local_files_only=True)


def preflight(root):
    frozen=v2.checked_plan(root)
    checks={}
    for m,spec in frozen['models'].items():
        tok=tokenizer(spec)
        history={}
        lengths=[]
        for s,b,t in v2.slots(frozen['dataset']):
            messages,parents=v2.messages_for(frozen['dataset'],s,b,t,history)
            rendered=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
            ids=tok.encode(rendered,add_special_tokens=False)
            assert len(ids)+spec['config']['generation']['max_tokens']<=spec['config']['generation']['context_limit']
            lengths.append(len(ids))
            history[v2.identity(s,b,t)]=dict(status='completed',text='```json\n{"answer":"A"}\n```')
        checks[m]=dict(slots=len(lengths),max_input_tokens=max(lengths),template_sha256=digest(tok.chat_template))
    write_new(root/'render-preflight.json',dict(label='AGENT tokenizer-only synthetic-history check; no inference',checks=checks,human_validation=False))


def export(root,output):
    raw=read(root/'raw.json');v2.validate(raw)
    output.mkdir(parents=True,exist_ok=True)
    observations={}; audit={}
    for m,h in raw['attempts'].items():
        tok=tokenizer(raw['plan']['models'][m])
        loaded=read(root/m/'loaded.json')
        assert digest(tok.chat_template)==loaded['template_sha256']
        observations[m]={}
        checks=0
        for slot,a in h.items():
            if 'actual' in a:
                rendered=tok.apply_chat_template(a['messages'],tokenize=False,add_generation_prompt=True)
                assert rendered==a['actual']['rendered_input']
                assert tok.encode(rendered,add_special_tokens=False)==a['actual']['input_token_ids']
                checks+=1
            if 'cache_dtypes' in a:assert a['cache_dtypes']==['mlx.core.bfloat16']
            assert a['timestamp']>raw['plan']['created_at']
            observations[m][slot]={k:a[k] for k in ('slot','model','scenario_id','branch','turn','parents','messages','text','status','stop_reason')}
            observations[m][slot]['actual_sha256']=digest(a.get('actual'))
        audit[m]=dict(attempts=len(h),tokenizer_checks=checks,loaded_metadata=loaded,
            max_input_tokens=max(len(a.get('actual',{}).get('input_token_ids',[])) for a in h.values()),
            generation_wall_seconds=sum(a['generation_wall_seconds'] for a in h.values()),
            mlx_peak_bytes=max(a.get('mlx_peak_bytes',0) for a in h.values()))
    for s in raw['plan']['dataset']['scenarios']:
        key=v2.identity(s,'initial',0)
        a,b=(raw['attempts'][m][key] for m in ('reference','quantized'))
        assert a['messages']==b['messages'] and a.get('actual')==b.get('actual')
    for field in ('template_sha256','eos_token_ids','chat_template'):
        assert audit['reference']['loaded_metadata'][field]==audit['quantized']['loaded_metadata'][field]
    for field in ('packages','platform','python','source_sha256'):
        assert audit['reference']['loaded_metadata']['environment'][field]==audit['quantized']['loaded_metadata']['environment'][field]
    write_new(output/'observations.json',dict(label='MEASURED exploratory local MLX sycophancy-v2',raw_sha256=file_hash(root/'raw.json'),observations=observations))
    for name,value in [('protocol.json',raw['plan']),('summary.json',read(root/'scores.json')),('review.json',read(root/'review.json')),('render-preflight.json',read(root/'render-preflight.json')),('verification.json',read('outputs/m5-sycophancy-verification-v2/verification.json'))]:
        write_new(output/name,value)
    write_new(output/'audit.json',dict(label='AGENT/programmatic checks; not human validation',models=audit,initial_actual_input_pairs_equal=9,human_validation=False,total_generation_attempts=sum(len(h) for h in raw['attempts'].values())))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=('preflight','export'))
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--output',type=Path)
    a=p.parse_args()
    preflight(a.run) if a.command=='preflight' else export(a.run,a.output)
