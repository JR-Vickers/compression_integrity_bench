"""Offline pilot regeneration audit; creates a new verification directory."""
import argparse
import json
from pathlib import Path
from cib.records import file_hash, digest, read, write_new
from cib.pilot import analyze
from cib.pilot_report import report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=False)
    originals={str(p):file_hash(p) for p in a.run.iterdir() if p.is_file() and p.name!='.lock'}
    first=analyze(a.run/'raw.json',a.output/'scores.json')
    analyze(a.run/'raw.json',a.output/'rescored.json')
    report(a.run/'raw.json',a.output/'scores.json',a.output/'report.md')
    report(a.run/'raw.json',a.output/'scores.json',a.output/'regenerated.md')
    assert (a.output/'scores.json').read_bytes()==(a.output/'rescored.json').read_bytes()
    assert (a.output/'report.md').read_bytes()==(a.output/'regenerated.md').read_bytes()
    assert all(file_hash(path)==h for path,h in originals.items())
    previous=read(a.run/'scores.json')
    # Source lineage can change when report-only code is added after the original scoring.
    assert {k:v for k,v in first.items() if k!='scorer_source_sha256'}=={k:v for k,v in previous.items() if k!='scorer_source_sha256'}
    raw=read(a.run/'raw.json')
    ids={r['request_id'] for r in raw['requests']}
    assert {a['request_id'] for a in raw['attempts'] if a['status']!='not_attempted'}==ids
    assert len(raw['attempts'])==344
    assert all(a['status']=='completed' and a['cache_dtypes']==['mlx.core.bfloat16'] for a in raw['attempts'])
    assert len(list(a.run.glob('*.result.json')))==344
    assert len(list(a.run.glob('*.start.json')))==344
    assert len(list(a.run.glob('*.stream.jsonl')))==344
    stream_tokens={d:0 for d in ('reference','quantized')}
    for attempt in raw['attempts']:
        stream=a.run/(attempt['request_id']+'-'+str(attempt['attempt_index'])+'.stream.jsonl')
        events=[json.loads(line) for line in stream.read_text().splitlines()]
        assert ''.join(e['text'] for e in events)==attempt['text']
        assert events[-1]['finish_reason']=='stop'
        stream_tokens[attempt['deployment_id']]+=sum(e.get('token') is not None for e in events)
    assert all(file_hash(path)==h for path,h in originals.items())
    verification=dict(schema_version='cib.pilot-verification.v1',immutable_files_checked=len(originals),
        original_file_hash_inventory_sha256=digest(originals),original_files_unchanged=True,
        rescoring_byte_identical=True,report_regeneration_byte_identical=True,
        numerical_results_equal_original=True,all_attempts_completed=True,all_kv_bfloat16=True,
        stream_text_matches_raw=True,stream_terminal_stops_match=True,stream_token_events=stream_tokens,
        planned=344,executed=344,raw_sha256=file_hash(a.run/'raw.json'),
        artifact_sha256={str(p):file_hash(p) for p in a.output.iterdir() if p.is_file()},
        dataset_sha256=first['dataset_sha256'],parser_implementation_sha256=first['parser_implementation_sha256'],
        protocol=first['protocol'])
    write_new(a.output/'verification.json',verification)
    print(a.output/'verification.json')


if __name__=='__main__': main()
