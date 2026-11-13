"""Offline regeneration and historical immutability check; never imports inference."""
import argparse
from pathlib import Path
from cib import content_audit, review, source_fidelity
from cib.records import file_hash, read, write_new


def verify(evidence, inventory, output):
    historical=read(inventory)
    changed=[name for name,h in historical.items() if not Path(name).is_file() or file_hash(name)!=h]
    if changed:
        raise ValueError('historical artifacts changed: '+repr(changed[:10]))
    output.mkdir(parents=True,exist_ok=False)
    for n in (1,2):
        root=output/str(n);root.mkdir()
        content_audit.generate(evidence,root/'content')
        review.sycophancy_packet(evidence,root/'sycophancy-review')
        source_fidelity.fixture(root/'source-fixture')
        source_fidelity.regenerate(root/'source-fixture/raw.json',root/'source-rescored.json')
        source_fidelity.review_packet(root/'source-fixture/raw.json',root/'source-review')
        if (root/'source-fixture/scores.json').read_bytes()!=(root/'source-rescored.json').read_bytes():
            raise ValueError('source rescoring mismatch')
    first={p.relative_to(output/'1'):file_hash(p) for p in (output/'1').rglob('*') if p.is_file()}
    second={p.relative_to(output/'2'):file_hash(p) for p in (output/'2').rglob('*') if p.is_file()}
    if first!=second:
        raise ValueError('regeneration differs')
    published=Path('docs/evidence/m5-content-audit')
    checked=0
    for rel,h in first.items():
        if rel.name=='source-rescored.json':
            continue
        parts=list(rel.parts)
        if parts[0]=='content':
            parts[0]='diagnostic'
        path=published.joinpath(*parts)
        if path.is_file():
            if file_hash(path)!=h:
                raise ValueError('published derived artifact differs: '+str(path))
            checked+=1
    if any(file_hash(name)!=h for name,h in historical.items()):
        raise ValueError('historical mutation during regeneration')
    result=dict(label='AGENT offline programmatic verification; human validation pending',
        inference_calls=0,model_downloads=0,historical_artifacts_unchanged=len(historical),
        inventory_sha256=file_hash(inventory),byte_identical_regenerated_files=len(first),
        published_derived_files_match=checked,
        frozen_primary_reproduced=True,source_fixture_rescoring_identical=True)
    write_new(output/'verification.json',result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evidence',type=Path,default=Path('docs/evidence/m5-sycophancy-v2'))
    p.add_argument('--inventory',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    print(verify(a.evidence,a.inventory,a.output))
