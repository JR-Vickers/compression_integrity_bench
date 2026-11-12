"""Offline saved-output regeneration and immutable-record audit for M4b."""
import argparse
import json
from pathlib import Path
from cib.records import read,file_hash,write_new,digest
from cib.diagnostic import score
from cib.diagnostic_report import report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--historical-hashes',type=Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    old=read(a.historical_hashes)
    assert all(file_hash(path)==h for path,h in old.items())
    original={str(p):file_hash(p) for p in a.run.iterdir() if p.is_file() and p.name!='.lock'}
    s=score(a.run/'raw.json',a.output/'scores.json');score(a.run/'raw.json',a.output/'rescored.json')
    assert (a.output/'scores.json').read_bytes()==(a.output/'rescored.json').read_bytes()
    report(a.run/'raw.json',a.output/'scores.json',a.output/'report.md');report(a.run/'raw.json',a.output/'scores.json',a.output/'regenerated.md')
    assert (a.output/'report.md').read_bytes()==(a.output/'regenerated.md').read_bytes()
    previous=read(a.run/'scores.json')
    assert {k:v for k,v in s.items() if k!='source_sha256'}=={k:v for k,v in previous.items() if k!='source_sha256'}
    raw=read(a.run/'raw.json');attempts=[a for a in raw['attempts'] if a['status']!='not_attempted']
    for attempt in attempts:
        stream=a.run/(attempt['request_id']+'-'+str(attempt['attempt_index'])+'.stream.jsonl')
        events=[json.loads(line) for line in stream.read_text().splitlines()]
        assert ''.join(e['text'] for e in events)==attempt['text']
        if attempt['status']=='completed':assert events[-1]['finish_reason']=='stop'
        assert attempt.get('cache_dtypes')==['mlx.core.bfloat16']
    assert all(file_hash(path)==h for path,h in original.items())
    assert all(file_hash(path)==h for path,h in old.items())
    write_new(a.output/'verification.json',dict(schema_version='cib.diagnostic-verification.v1',raw_sha256=file_hash(a.run/'raw.json'),planned=len(raw['requests']),attempts=len(attempts),
        historical_files_checked=len(old),historical_files_unchanged=True,run_files_checked=len(original),run_files_unchanged=True,raw_streams_match=True,bfloat16_kv=True,
        repeated_scores_byte_identical=True,repeated_reports_byte_identical=True,numerical_results_equal_original=True,
        historical_inventory_sha256=digest(old),run_inventory_sha256=digest(original),artifacts={str(p):file_hash(p) for p in a.output.iterdir() if p.is_file()}))
    print(a.output/'verification.json')


if __name__=='__main__':main()
