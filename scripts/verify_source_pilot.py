"""Inference-free pilot reproduction, streams/pairing and historical integrity audit."""
import argparse
from pathlib import Path
from cib import source_pilot as sp, review
from cib.records import read,file_hash,write_new,digest


def verify(run,raw_path,inventory,output):
    old=read(inventory)
    def unchanged():
        changed=[p for p,h in old.items() if not Path(p).is_file() or file_hash(p)!=h]
        if changed:raise ValueError('historical mutation: '+repr(changed[:5]))
    unchanged();output.mkdir(parents=True,exist_ok=False)
    originals={str(p):file_hash(p) for p in run.rglob('*') if p.is_file() and p.name!='.lock'}
    raw=read(raw_path);sp.validate(raw)
    streams=0;tokens=0
    for m in sp.MODELS:
        for slot,a in raw['attempts'][m].items():
            base=run/m/slot
            stream=Path(str(base)+'.stream.jsonl')
            if stream.exists():
                events=[__import__('json').loads(line) for line in stream.read_text().splitlines()]
                if ''.join(e['text'] for e in events)!=a['text']:raise ValueError('stream differs')
                streams+=1
            if a.get('actual'):
                if read(Path(str(base)+'.input.json'))!=a['actual']:raise ValueError('saved actual input differs')
                tokens=max(tokens,len(a['actual']['input_token_ids']))
            if a['status'] in ('completed','truncated') and a.get('cache_dtypes')!=['mlx.core.bfloat16']:
                raise ValueError('unexpected KV cache precision')
    inventories=[]
    for n in (1,2):
        root=output/str(n);root.mkdir()
        sp.export_review(raw_path,root/'review')
        sp.score_file(raw_path,root/'scores.json',root/'review/packet.json')
        sp.report_file(raw_path,root/'scores.json',root/'report.md',root/'review/packet.json')
        review.first_batch(root/'sycophancy-first-review')
        inventories.append({str(p.relative_to(root)):file_hash(p) for p in root.rglob('*') if p.is_file()})
    if inventories[0]!=inventories[1]:raise ValueError('regeneration differs')
    published=Path('docs/evidence/m5-source-fidelity')
    for name in ('scores.json','report.md'):
        if (published/name).exists() and file_hash(published/name)!=file_hash(output/'1'/name):
            raise ValueError('published derived artifact differs: '+name)
    if any(file_hash(p)!=h for p,h in originals.items()):raise ValueError('raw journal mutated')
    unchanged()
    result=dict(label='AGENT offline verification, no human validation',inference_calls=0,
        historical_artifacts_unchanged=len(old),new_run_artifacts_unchanged=len(originals),
        byte_identical_regenerated_files=len(inventories[0]),streams_matching=streams,
        maximum_input_tokens=tokens,matched_rendered_tokenized_pairs=True,bf16_kv_caches=True,published_scores_report_match=True,
        plan_sha256=digest(raw['plan']),raw_sha256=file_hash(raw_path))
    write_new(output/'verification.json',result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True);p.add_argument('--raw',type=Path,required=True)
    p.add_argument('--inventory',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(verify(a.run,a.raw,a.inventory,a.output))
