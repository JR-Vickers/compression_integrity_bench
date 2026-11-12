"""One optional larger BF16 reference preparation. Never quantizes a model."""
import argparse
from collections import Counter
from pathlib import Path
import time

from .records import read,write_new,digest
from .feasibility import inventory,tensor_inventory
from .pipeline import source_hash,git_state
from .diagnostic import load_diagnostic

REPO='Qwen/Qwen2.5-7B-Instruct'
REVISION='a09a35458c702b33eeacc393d103063234e8bc28'


def validate_config(config):
    ds=load_diagnostic(True)
    if (config['schema_version']!='cib.larger-reference-config.v1' or config['source']['repo_id']!=REPO
            or config['source']['revision']!=REVISION or config['source']['reference_dtype']!='bfloat16'
            or config['quantization'] is not None or config['generation']!=ds['diagnostic_protocol']['generation']
            or config['criteria']!=ds['diagnostic_protocol']['suitability_criteria']):
        raise ValueError('unsupported larger reference configuration')
    if config['backend']!={'mlx-lm':'0.32.2','mlx':'0.32.4'}:raise ValueError('unsupported backend')


def prepare(config,artifacts,output):
    from huggingface_hub import HfApi,snapshot_download
    validate_config(config);output.mkdir(parents=True,exist_ok=False)
    write_new(output/'invocation.json',dict(config=config,code=git_state(),source_sha256=source_hash()))
    started=time.monotonic()
    info=HfApi(token=False).model_info(REPO,revision=REVISION,files_metadata=True)
    if info.sha!=REVISION or info.gated or info.private:raise ValueError('unverified source identity')
    license_name=info.card_data.get('license')
    if license_name!='apache-2.0':raise ValueError('unexpected license')
    official={s.rfilename:dict(sha256=s.lfs.sha256,bytes=s.lfs.size) for s in info.siblings if s.lfs and s.rfilename.endswith('.safetensors')}
    if sum(x['bytes'] for x in official.values())>config['budget']['max_download_bytes']:raise ValueError('download budget exceeded')
    write_new(output/'official-files.json',dict(repo=REPO,revision=info.sha,gated=info.gated,license=license_name,weights=official))
    path=Path(snapshot_download(REPO,revision=REVISION,token=False,cache_dir=str(artifacts/'hub'),
        allow_patterns=['*.safetensors','*.json','*.txt','*.jinja','LICENSE','README.md'])).resolve()
    tensors=tensor_inventory(path);model_config=read(path/'config.json')
    if {t['dtype'] for t in tensors.values()}!={'BF16'} or any(k in model_config for k in ('quantization','quantization_config')):
        raise ValueError('source is not unquantized BF16')
    files=inventory(path)
    if set(official)!={p.name for p in path.glob('*.safetensors')}:raise ValueError('shard inventory differs')
    for name,v in official.items():
        if files[name]!=v:raise ValueError('official weight hash/size mismatch')
    dtype_counts=dict(Counter(v['dtype'] for v in tensors.values()))
    result=dict(schema_version='cib.prepared.v1',config_sha256=digest(config),source=config['source'],
        reference=dict(path=str(path),files=files),tensor_dtype_counts=dtype_counts,
        source_tensor_count=len(tensors),official_weights=official,official_revision=info.sha,license=license_name,
        preparation_seconds=time.monotonic()-started,source_sha256=source_hash(),quantization_performed=False)
    write_new(output/'prepared.json',result);return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True);p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    prepare(read(a.config),a.artifacts,a.output);print(a.output/'prepared.json')


if __name__=='__main__':main()
