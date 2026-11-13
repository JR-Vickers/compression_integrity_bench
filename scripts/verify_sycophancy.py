"""Export compact measured evidence; optionally verify actual tokenizer rendering.

No inference. Use existing Transformers environment only with --tokenizer.
"""
import argparse
from pathlib import Path
from cib.records import read, digest, file_hash, write_new
from cib.sycophancy import validate, parse, calculate


def export(root, output, tokenizer=False):
    raw=read(root/'raw.json')
    validate(raw)
    output.mkdir(parents=True,exist_ok=True)
    observations={}
    controls={}
    models={}
    sources=raw['plan']['models']
    for m,history in raw['attempts'].items():
        if not history:
            continue
        spec=sources[m]
        loaded=read(root/m/'loaded.json')
        tok=None
        if tokenizer:
            from transformers import AutoTokenizer
            tok=AutoTokenizer.from_pretrained(spec['prepared']['reference']['path'],local_files_only=True)
            assert digest(tok.chat_template)==loaded['template_sha256']
        observations[m]={}
        for slot,a in history.items():
            if tok:
                rendered=tok.apply_chat_template(a['messages'],tokenize=False,add_generation_prompt=True)
                assert rendered==a['actual']['rendered_input']
                assert tok.encode(rendered,add_special_tokens=False)==a['actual']['input_token_ids']
            assert a['cache_dtypes']==['mlx.core.bfloat16']
            assert a['status']=='completed' and a['stop_reason']=='stop'
            assert a['timestamp']>raw['plan']['created_at']
            observations[m][slot]={k:a[k] for k in ('slot','model','scenario_id','branch','turn',
                                                   'parents','messages','text','status','stop_reason')}
            observations[m][slot]['actual_sha256']=digest(a['actual'])
            observations[m][slot]['answer']=parse(a['text'])
        models[m]={'loaded_metadata':loaded,'attempts':len(history),
                   'generation_wall_seconds':sum(a['generation_wall_seconds'] for a in history.values()),
                   'mlx_peak_bytes':max(a['mlx_peak_bytes'] for a in history.values()),
                   'process_peak_rss_bytes':max(a['process_peak_rss_bytes'] for a in history.values()),
                   'max_input_tokens':max(len(a['actual']['input_token_ids']) for a in history.values())}
        wrong=[]
        for s in raw['plan']['dataset']['scenarios']:
            answer=observations[m][s['scenario_id']+'-evidence-1']['answer']
            if answer!=s['false']:
                wrong.append({'scenario_id':s['scenario_id'],'answer':answer,'target':s['false']})
        controls[m]=wrong
    # Initial messages and actual tokens must be identical across deployments.
    for s in raw['plan']['dataset']['scenarios']:
        slot=s['scenario_id']+'-initial-0'
        a,b=(raw['attempts'][m][slot] for m in ('reference','quantized'))
        assert a['messages']==b['messages'] and a['actual']==b['actual']
    for field in ('chat_template','template_sha256','eos_token_ids'):
        assert models['reference']['loaded_metadata'][field]==models['quantized']['loaded_metadata'][field]
    for field in ('packages','platform','python','source_sha256'):
        assert models['reference']['loaded_metadata']['environment'][field]==models['quantized']['loaded_metadata']['environment'][field]
    write_new(output/'observations.json',{'label':'MEASURED local MLX exploratory structured-answer pilot',
              'raw_sha256':file_hash(root/'raw.json'),'observations':observations})
    write_new(output/'summary.json',read(root/'scores.json'))
    write_new(output/'protocol.json',raw['plan'])
    write_new(output/'review.json',read(root/'review.json'))
    write_new(output/'render-preflight.json',read(root/'render-preflight.json'))
    write_new(output/'verification.json',read('outputs/m5-sycophancy-verification-v1/verification.json'))
    write_new(output/'audit.json',{'models':models,'incorrect_evidence_controls':controls,
              'initial_actual_input_pairs_equal':12,'tokenizer_verified':tokenizer,
              'tokenizer_checks':sum(len(h) for h in raw['attempts'].values()) if tokenizer else 0,
              'scripts_dataset_unchanged':raw['plan']['dataset']==read('src/cib/data/sycophancy-v1.json'),
              'source_hash_at_generation':raw['plan']['source_sha256'],
              'total_generation_attempts':sum(len(h) for h in raw['attempts'].values()),
              'fallback':'not triggered; contingency slots are not allocated missing observations',
              'human_validation':False})
    print({m:{k:v for k,v in d.items() if k!='loaded_metadata'} for m,d in models.items()})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--tokenizer',action='store_true')
    a=p.parse_args()
    export(a.run,a.output,a.tokenizer)
