"""Offline M4c preflight and saved-output/immutable-file verification; no inference."""
import argparse
from pathlib import Path
import json
import re
from fractions import Fraction as F
from cib.records import read, file_hash, write_new, digest
from cib.rule_diagnostic import load, planned, target, score, report, FORMULA
from cib.diagnostic import FORMAT


def instrument_audit(requests):
    """Recover numbers from prompts, independently use posterior odds and expression."""
    rows = []
    ds = load()
    for s in ds['scenarios']:
        rr = {r['prompt_variant']:r for r in requests if r['scenario_id'] == s['scenario_id'] and r['trial_index'] == 0}
        text = rr['A']['input']['messages'][0]['content']
        p, complement = map(F, re.search(r'P\(H\)=([0-9]+(?:\.[0-9]+)?) and P\(not H\)=([0-9]+(?:\.[0-9]+)?)', text).groups())
        a, b = map(F, re.search(r'P\(E\|H\)=([0-9]+(?:\.[0-9]+)?) and P\(E\|not H\)=([0-9]+(?:\.[0-9]+)?)', text).groups())
        assert p+complement == 1
        odds = p/complement * a/b
        independent = odds/(1+odds)
        assert independent == target(s)
        assert rr['B']['input']['messages'][0]['content'] == text.removesuffix(FORMAT)+FORMULA+FORMAT
        c = rr['C']['input']['messages'][0]['content']
        nums = tuple(map(F, re.fullmatch(r'Evaluate the numerical expression \(([0-9]+(?:\.[0-9]+)?)\*([0-9]+(?:\.[0-9]+)?)\) / \(([0-9]+(?:\.[0-9]+)?)\*([0-9]+(?:\.[0-9]+)?) \+ \(1-([0-9]+(?:\.[0-9]+)?)\)\*([0-9]+(?:\.[0-9]+)?)\)\.'+re.escape(FORMAT), c).groups()))
        assert nums == (p,a,p,a,p,b)
        n1,n2,d1,d2,d3,d4=nums
        expression = n1*n2/(d1*d2+(1-d3)*d4)
        assert expression == independent
        for r in rr.values():
            assert set(r['input']) == {'messages'}
            assert len(r['input']['messages']) == 1
            assert r['input']['messages'][0]['content'].endswith(FORMAT)
        rows.append(dict(scenario_id=s['scenario_id'], prior=str(p), likelihood_h=str(a), likelihood_not_h=str(b),
                         odds_target=str(independent), numerical_expression_target=str(expression), equivalent=True))
    assert len(rows) == 12
    assert len(requests) == 42 and len({r['request_id'] for r in requests}) == 42
    return rows


def historical_inventory():
    paths = []
    for root in ('docs/evidence/m2','docs/evidence/m3','docs/evidence/m4','docs/evidence/m4b',
                 'outputs/m4-pilot-v1','outputs/m4b-wording-v1','outputs/m4b-reference-7b-v1','outputs/m4b-7b-prepare-permitted'):
        paths.extend(p for p in Path(root).rglob('*') if p.is_file() and p.name != '.lock')
    # Include prior audited original-run inventory even if its root name differs.
    previous = read('outputs/m4b-audit-v1/original-hashes.json')
    assert all(file_hash(p) == h for p,h in previous.items())
    return {**previous, **{str(p):file_hash(p) for p in paths}}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=('preflight','render','verify'))
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--historical-hashes',type=Path)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=False)
    if a.command == 'preflight':
        plan=read(a.run/'run.json')
        assert not list(a.run.glob('*.start.json'))
        instrument=instrument_audit(plan['requests'])
        # No downloaded files or dependencies are modified.
        from cib.feasibility import inventory
        config=read('configs/reference-check-qwen25-7b.json')
        prepared=read('outputs/m4b-7b-prepare-permitted/prepared.json')
        assert digest(config)==load()['required_config_sha256']
        assert digest(prepared)==load()['required_prepared_sha256']
        assert inventory(prepared['reference']['path'])==prepared['reference']['files']
        provenance=read('docs/evidence/m4b/reference-provenance.json')
        assert provenance['prepared_sha256']==digest(prepared)
        assert prepared['official_revision']==config['source']['revision']=='a09a35458c702b33eeacc393d103063234e8bc28'
        assert prepared['tensor_dtype_counts']=={'BF16':339} and not prepared['quantization_performed']
        for name,info in prepared['official_weights'].items():
            assert prepared['reference']['files'][name]==info
        hashes=historical_inventory(); write_new(a.output/'historical-hashes.json',hashes)
        write_new(a.output/'preflight.json',dict(instrument=instrument,plan_sha256=file_hash(a.run/'run.json'),
            config_sha256=digest(config),prepared_sha256=digest(prepared),artifact_inventory_matches=True,
            official_weight_hashes_match=True,historical_files=len(hashes),
            frozen_files={str(p):file_hash(p) for p in [Path('configs/rule-diagnostic-v1.json'),Path('src/cib/data/rule-diagnostic-v1.json'),Path('src/cib/rule_diagnostic.py')]}))
    elif a.command == 'render':
        # Existing tokenizer only; can be run before any generation.
        from transformers import AutoTokenizer
        plan=read(a.run/'run.json')
        t=AutoTokenizer.from_pretrained(plan['manifest']['prepared']['reference']['path'],local_files_only=True,trust_remote_code=False)
        old=read('outputs/m4b-reference-7b-v1/reference.loaded.json')
        assert t.chat_template==old['chat_template']
        actual={}
        for r in plan['requests']:
            text=t.apply_chat_template(r['input']['messages'],tokenize=False,add_generation_prompt=True)
            assert r['input']['messages'][0]['content'] in text
            ids=t.encode(text,add_special_tokens=False)
            assert len(ids)+64<=2048
            actual[r['request_id']]=dict(rendered_input=text,input_token_ids=ids)
        write_new(a.output/'rendered-inputs.json',actual)
        write_new(a.output/'render-validation.json',dict(planned=len(actual),template_matches_m4b=True,
            all_message_text_preserved=True,context_limits_pass=True,rendered_inputs_sha256=digest(actual)))
    else:
        old=read(a.historical_hashes)
        assert all(file_hash(p)==h for p,h in old.items())
        original={str(p):file_hash(p) for p in a.run.iterdir() if p.is_file() and p.name!='.lock'}
        raw=read(a.run/'raw.json'); instrument_audit(raw['requests'])
        s=score(a.run/'raw.json',a.output/'scores.json'); score(a.run/'raw.json',a.output/'rescored.json')
        report(a.run/'raw.json',a.output/'scores.json',a.output/'report.md')
        report(a.run/'raw.json',a.output/'scores.json',a.output/'regenerated.md')
        assert (a.output/'scores.json').read_bytes()==(a.output/'rescored.json').read_bytes()
        assert (a.output/'report.md').read_bytes()==(a.output/'regenerated.md').read_bytes()
        assert s==read(a.run/'scores.json')
        loaded=read(a.run/'reference.loaded.json')
        prior_loaded=read('outputs/m4b-reference-7b-v1/reference.loaded.json')
        for k in ('parameter_dtype_counts','quantized_modules','chat_template','template_sha256','eos_token_ids','model_config'):
            assert loaded[k]==prior_loaded[k]
        assert loaded['parameter_dtype_counts']=={'mlx.core.bfloat16':339} and loaded['quantized_modules']==[]
        # Load only the existing tokenizer (no model, MLX, network or generation).
        from transformers import AutoTokenizer
        tokenizer=AutoTokenizer.from_pretrained(raw['manifest']['prepared']['reference']['path'],local_files_only=True,trust_remote_code=False)
        for attempt in raw['attempts']:
            if attempt['status']=='not_attempted':continue
            r=next(r for r in raw['requests'] if r['request_id']==attempt['request_id'])
            rendered=tokenizer.apply_chat_template(r['input']['messages'],tokenize=False,add_generation_prompt=True)
            assert attempt['actual']==dict(rendered_input=rendered,input_token_ids=tokenizer.encode(rendered,add_special_tokens=False))
            stream=a.run/(attempt['request_id']+'-'+str(attempt['attempt_index'])+'.stream.jsonl')
            events=[json.loads(line) for line in stream.read_text().splitlines()]
            assert ''.join(e['text'] for e in events)==attempt['text']
            if attempt['status']=='completed':
                assert events[-1]['finish_reason']=='stop'
                assert attempt['cache_dtypes']==['mlx.core.bfloat16']
        assert all(file_hash(p)==h for p,h in old.items())
        assert all(file_hash(p)==h for p,h in original.items())
        write_new(a.output/'verification.json',dict(raw_sha256=file_hash(a.run/'raw.json'),
            historical_files_checked=len(old),historical_files_unchanged=True,run_files_checked=len(original),run_files_unchanged=True,
            scores_byte_identical=True,reports_byte_identical=True,original_scores_equal=True,actual_rendering_and_tokens_verified=True,
            raw_streams_match=True,bfloat16_weights_and_kv=True,loaded_template_and_precision_match_m4b=True,
            historical_inventory_sha256=digest(old),run_inventory_sha256=digest(original)))
    print(a.output)


if __name__=='__main__':main()
