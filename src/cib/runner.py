"""Resumable local real inference, immutable snapshots, and checked M2 import.

Run one deployment per process. Journals are append-only exclusive files; a process
lock prevents concurrent mutation. Exactly one infrastructure retry is permitted.
Malformed/refusal/truncated responses never trigger retries. No cross-run cache.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
import tempfile
from pathlib import Path
import traceback
import uuid
import time

from .feasibility import validate_config, model_inputs
from .pipeline import planned_requests, source_hash, git_state
from .records import digest, file_hash, key, observation_id, read, encode
from .tasks import load_fixture, load_pilot


def validate_run_config(config):
    if config['schema_version'] == 'cib.larger-reference-config.v1':
        from .larger_reference import validate_config as validate_larger
        validate_larger(config)
    else:
        validate_config(config)


def write_new(path, value):
    """Commit complete journal files atomically, never replacing a destination."""
    path = Path(path)
    descriptor, temporary = tempfile.mkstemp(prefix='.commit-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(encode(value))
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
    finally:
        os.unlink(temporary)


def interrupted(start):
    abandoned = read(start)
    stream = start.with_name(start.name.replace('.start.json', '.stream.jsonl'))
    events = []
    if stream.exists():
        for line in stream.read_bytes().splitlines():
            try:
                events.append(json.loads(line))
            except ValueError:
                break  # torn final event remains preserved in the stream
    abandoned.update(text=''.join(e['text'] for e in events),
                     status='infrastructure_error', stop_reason=None,
                     error='Interrupted before result commit; partial stream retained')
    return abandoned


def now():
    return datetime.now(timezone.utc).isoformat()


def deployment_registry(config, prepared):
    if config['schema_version'] == 'cib.larger-reference-config.v1':
        return {'reference': {'deployment_id': 'reference', 'kind': 'real_local_mlx',
                'source': config['source'], 'backend': config['backend'],
                'artifact_files': prepared['reference']['files'],
                'tokenizer_files': prepared['reference']['files'], 'quantization': None}}
    return {name: {'deployment_id': name, 'kind': 'real_local_mlx', 'source': config['source'],
                   'backend': config['backend'], 'artifact_files': prepared[name]['files'],
                   'tokenizer_files': prepared['reference']['files'],
                   'quantization': None if name == 'reference' else config['quantization']}
            for name in ('reference', 'quantized')}


def requests_for(dataset, deployments, config):
    if dataset.get('schema_version') == 'cib.rule-dataset.v1' and digest(config) != dataset['required_config_sha256']:
        raise ValueError('M4c requires the unchanged existing 7B configuration')
    result = planned_requests(dataset, ('reference', 'quantized') if 'quantized' in deployments else ('reference',))
    for request in result:
        request['decoding'] = config['generation']
        request['deployment_fingerprint'] = digest(deployments[request['deployment_id']])
        request['request_id'] = digest({'observation': observation_id(request),
                                        'artifact': request['deployment_fingerprint']})
    return result


def cache_identity(request, actual):
    return digest({'artifact': request['deployment_fingerprint'], 'input': request['input'],
                   'actual': actual, 'decoding': request['decoding'], 'trial': key(request)})


def new_run(config, prepared, dataset=None):
    validate_run_config(config)
    if prepared['schema_version'] != 'cib.prepared.v1' or prepared['config_sha256'] != digest(config):
        raise ValueError('preparation/config mismatch')
    dataset = load_fixture() if dataset is None else dataset
    if dataset.get('schema_version') == 'cib.rule-dataset.v1' and digest(prepared) != dataset['required_prepared_sha256']:
        raise ValueError('M4c requires the existing pinned preparation')
    deployments = deployment_registry(config, prepared)
    return {'schema_version': 'cib.real-run.v1', 'dataset': dataset,
            'manifest': {'schema_version': 'cib.real-manifest.v1', 'run_id': str(uuid.uuid4()),
                         'created_at': now(), 'label': 'Exploratory engineering check on development tasks',
                         'split': dataset['split'], 'dataset_sha256': digest(dataset),
                         'analysis': dataset['analysis'], 'deployments': deployments,
                         'config': config, 'prepared': prepared, 'infrastructure_retry_limit': 1,
                         'planning_policy': 'full 24-request development set per deployment; M2 selections only used on import',
                         'code': git_state(), 'source_sha256': source_hash()},
            'requests': requests_for(dataset, deployments, config), 'attempts': []}


def missing(request):
    return {'request_id': request['request_id'], 'deployment_id': request['deployment_id'],
            'attempt_index': 0, 'status': 'not_attempted', 'text': None,
            'stop_reason': None, 'error': None}


def validate_real(raw):
    manifest, dataset = raw['manifest'], raw['dataset']
    config, prepared = manifest['config'], manifest['prepared']
    validate_run_config(config)
    from .diagnostic import load_diagnostic
    from .rule_diagnostic import load as load_rule
    if dataset.get('schema_version') == 'cib.rule-dataset.v1':
        if digest(prepared) != dataset['required_prepared_sha256']:
            raise ValueError('M4c preparation changed')
        if sum(a['status'] != 'not_attempted' for a in raw['attempts']) > dataset['diagnostic_protocol']['max_generation_requests']:
            raise ValueError('M4c attempt ceiling exceeded')
    if prepared['config_sha256'] != digest(config) or dataset not in (load_fixture(), load_pilot(), load_diagnostic(), load_diagnostic(True), load_rule()):
        raise ValueError('unsupported task or preparation')
    if (manifest['dataset_sha256'] != digest(dataset) or manifest['analysis'] != dataset['analysis']
            or manifest['deployments'] != deployment_registry(config, prepared)):
        raise ValueError('manifest identity mismatch')
    if raw['requests'] != requests_for(dataset, manifest['deployments'], config):
        raise ValueError('planned inputs/identities changed')
    expected = {r['request_id']: r for r in raw['requests']}
    grouped = {}
    for a in raw['attempts']:
        r = expected.get(a['request_id'])
        if not r or a['deployment_id'] != r['deployment_id']:
            raise ValueError('attempt ownership mismatch')
        grouped.setdefault(a['request_id'], []).append(a)
        if a['status'] not in {'completed', 'truncated', 'refusal', 'infrastructure_error', 'not_attempted'}:
            raise ValueError('unknown status')
        if a['text'] is not None and not isinstance(a['text'], str):
            raise ValueError('invalid raw text')
        if a['status'] == 'not_attempted':
            if a != missing(r):
                raise ValueError('invalid missing placeholder')
        else:
            if a['cache_identity'] != cache_identity(r, a['actual']):
                raise ValueError('cache identity mismatch')
            if a['status'] == 'truncated' and a['stop_reason'] != 'length':
                raise ValueError('truncation must retain length stop reason')
            if a['status'] == 'completed' and (not isinstance(a['text'], str) or a['stop_reason'] != 'stop'):
                raise ValueError('completion missing text or EOS')
    if set(grouped) != set(expected):
        raise ValueError('missing planned observation')
    for attempts in grouped.values():
        if len(attempts) > 2 or [a['attempt_index'] for a in attempts] != list(range(len(attempts))):
            raise ValueError('invalid attempt history')
        if len(attempts) == 2 and attempts[0]['status'] != 'infrastructure_error':
            raise ValueError('only infrastructure retries permitted')


def snapshot(root, output):
    raw = read(root / 'run.json')
    for request in raw['requests']:
        starts = sorted(root.glob(request['request_id'] + '-*.start.json'))
        if not starts:
            raw['attempts'].append(missing(request))
        for start in starts:
            result = start.with_name(start.name.replace('.start.json', '.result.json'))
            raw['attempts'].append(read(result) if result.exists() else interrupted(start))
    validate_real(raw)
    write_new(output, raw)
    return raw


def run(config, prepared, root, deployment, limit, factory=None, dataset=None):
    if limit < 0:
        raise ValueError('limit must be nonnegative')
    root.mkdir(parents=True, exist_ok=True)
    with (root / '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if not (root / 'run.json').exists():
            plan = new_run(config, prepared, dataset)
            if dataset is not None:
                policy = dataset.get('diagnostic_protocol', dataset.get('pilot_protocol'))
                plan['manifest'].update(label=dataset.get('split', 'exploratory'), planning_policy=policy)
            write_new(root / 'run.json', plan)
        plan = read(root / 'run.json')
        if plan['manifest']['config'] != config or plan['manifest']['prepared'] != prepared:
            raise ValueError('resume configuration changed')
        if dataset is not None and dataset != plan['dataset']:
            raise ValueError('resume dataset changed')
        validate_real({**plan, 'attempts': [missing(r) for r in plan['requests']]})
        adapter = None
        executed = 0
        invocation_start = time.monotonic()
        protocol = plan['dataset'].get('diagnostic_protocol', plan['dataset'].get('pilot_protocol'))
        prior_attempts = len(list(root.glob('*.start.json')))
        if protocol:
            saved = [read(p) for p in root.glob('*.result.json')]
            prior_seconds = sum(a.get('generation_wall_seconds', 0) for a in saved)
            if any(a.get('mlx_peak_bytes', 0) > protocol['max_mlx_peak_bytes'] for a in saved):
                raise ValueError('pilot memory budget exceeded; retain unexecuted observations')
        for request in plan['requests']:
            if request['deployment_id'] != deployment:
                continue
            prefix = request['request_id']
            # A start with no result represents an interrupted infrastructure attempt.
            for start in sorted(root.glob(prefix + '-*.start.json')):
                result = start.with_name(start.name.replace('.start.json', '.result.json'))
                if not result.exists():
                    write_new(result, interrupted(start))
            history = [read(p) for p in sorted(root.glob(prefix + '-*.result.json'))]
            if history and (history[-1]['status'] != 'infrastructure_error' or len(history) >= 2):
                continue
            if executed >= limit:
                break
            if protocol:
                if prior_attempts + executed >= protocol['max_generation_requests']:
                    raise ValueError('configured generation request ceiling reached; remaining work is unexecuted')
                if prior_seconds + time.monotonic() - invocation_start > protocol['max_wall_seconds']:
                    raise ValueError('pilot wall budget exhausted')
                if sum(p.stat().st_size for p in root.iterdir() if p.is_file()) > protocol['max_disk_bytes']:
                    raise ValueError('pilot disk budget exhausted')
                if adapter is not None and getattr(adapter, 'mx', None) and adapter.mx.get_peak_memory() > protocol['max_mlx_peak_bytes']:
                    raise ValueError('pilot memory budget exhausted')
            if adapter is None:
                if factory is None:
                    from .mlx_adapter import MLXAdapter
                    factory = MLXAdapter
                try:
                    adapter = factory(config, prepared, deployment)
                except Exception:
                    write_new(root / (deployment + '.setup-error-' + str(uuid.uuid4()) + '.json'),
                              {'timestamp': now(), 'error': traceback.format_exc()})
                    raise
                loaded = root / (deployment + '.loaded.json')
                if not loaded.exists():
                    write_new(loaded, adapter.metadata)
            actual = adapter.render(request['input'])
            index = len(history)
            base = root / (prefix + f'-{index}')
            attempt = {'schema_version': 'cib.real-attempt.v1', 'request_id': prefix,
                       'deployment_id': deployment, 'attempt_index': index, 'timestamp': now(),
                       'actual': actual, 'cache_identity': cache_identity(request, actual),
                       'text': '', 'status': 'infrastructure_error', 'stop_reason': None, 'error': None,
                       'loaded_metadata': adapter.metadata}
            write_new(str(base) + '.start.json', attempt)
            started = time.monotonic()
            try:
                with Path(str(base) + '.stream.jsonl').open('xb') as stream:
                    def emit(event):
                        stream.write(encode(event).replace(b'\n', b'') + b'\n')
                        stream.flush()
                        attempt['text'] += event['text']
                        attempt['stop_reason'] = event['finish_reason']
                    attempt.update(adapter.generate(actual, emit))
                if attempt['stop_reason'] not in {'stop', 'length'}:
                    raise ValueError('missing/unknown terminal stop reason')
                attempt['status'] = 'completed' if attempt['stop_reason'] == 'stop' else 'truncated'
            except Exception:
                attempt.update(status='infrastructure_error', error=traceback.format_exc())
            attempt['generation_wall_seconds'] = time.monotonic() - started
            write_new(str(base) + '.result.json', attempt)
            executed += 1
        return executed


def import_m2(config, prepared, reference, quantized, output):
    raw = new_run(config, prepared)
    selections = {key(r): r for r in model_inputs(config)}
    raw['manifest']['m2_loaded_metadata'] = {}
    for name, path in (('reference', reference), ('quantized', quantized)):
        checked = read(path)
        if (checked['schema_version'] != 'cib.feasibility-check.v1' or checked['deployment'] != name
                or checked['prepared_sha256'] != digest(prepared)):
            raise ValueError('M2 lineage mismatch')
        if checked['environment']['packages']['mlx-lm'] != config['backend']['mlx-lm']:
            raise ValueError('M2 backend mismatch')
        raw['manifest']['m2_loaded_metadata'][name] = {k: v for k, v in checked.items() if k != 'attempts'}
        indexed = {key(a['request']): a for a in checked['attempts']}
        if len(indexed) != len(checked['attempts']) or indexed.keys() != selections.keys():
            raise ValueError('M2 selection mismatch')
        for r in raw['requests']:
            if r['deployment_id'] != name:
                continue
            a = indexed.get(key(r))
            if a is None:
                raw['attempts'].append(missing(r))
                continue
            if a['request']['input'] != r['input'] or a['input_sha256'] != digest(r['input']):
                raise ValueError('M2 input mismatch')
            actual = {k: a[k] for k in ('rendered_input', 'input_token_ids')}
            raw['attempts'].append({
                'schema_version': 'cib.real-attempt.v1', 'request_id': r['request_id'],
                'deployment_id': name, 'attempt_index': 0, 'timestamp': a['started_at'],
                'text': a['raw_text'], 'status': a['status'], 'stop_reason': a['finish_reason'],
                'error': a.get('error'), 'actual': actual, 'cache_identity': cache_identity(r, actual),
                'source_path': str(path), 'source_sha256': file_hash(path), 'original_attempt': a})
    raw['manifest']['m2_sources'] = {n: {'path': str(p), 'sha256': file_hash(p)} for n, p in
                                     (('reference', reference), ('quantized', quantized))}
    left, right = (raw['manifest']['m2_loaded_metadata'][n] for n in ('reference', 'quantized'))
    if any(left[k] != right[k] for k in ('chat_template', 'template_sha256', 'eos_token_ids')):
        raise ValueError('M2 template/stop mismatch')
    # Ensure rendered/tokenized inputs, not just messages, were matched.
    for a, b in zip(read(reference)['attempts'], read(quantized)['attempts']):
        if any(a[k] != b[k] for k in ('request', 'rendered_input', 'input_token_ids')):
            raise ValueError('M2 actual input pairing mismatch')
    validate_real(raw)
    write_new(output, raw)
    return raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('run', 'snapshot', 'import-m2'))
    parser.add_argument('--config', type=Path, default=Path('configs/feasibility-qwen25-1.5b.json'))
    parser.add_argument('--prepared', type=Path, default=Path('outputs/m2-prepare/prepared.json'))
    parser.add_argument('--run', type=Path)
    parser.add_argument('--deployment', choices=('reference', 'quantized'))
    parser.add_argument('--limit', type=int, default=6, help='maximum new attempts this invocation')
    parser.add_argument('--pilot', action='store_true', help='use the pinned exploratory pilot v1')
    parser.add_argument('--diagnostic', action='store_true', help='use the pinned M4b wording diagnostic')
    parser.add_argument('--rule-diagnostic', action='store_true', help='use the pinned M4c single-answer diagnostic')
    parser.add_argument('--reference', type=Path)
    parser.add_argument('--quantized', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.command == 'run':
        if args.run is None or args.deployment is None:
            parser.error('run requires --run and --deployment')
        if sum((args.pilot, args.diagnostic, args.rule_diagnostic)) > 1:
            parser.error('choose only one dataset')
        from .diagnostic import load_diagnostic
        config = read(args.config)
        from .rule_diagnostic import load as load_rule
        dataset = (load_rule() if args.rule_diagnostic else load_diagnostic(config['schema_version'] == 'cib.larger-reference-config.v1') if args.diagnostic
                   else load_pilot() if args.pilot else None)
        print(run(config, read(args.prepared), args.run, args.deployment, args.limit, dataset=dataset))
    elif args.command == 'snapshot':
        if args.run is None or args.output is None:
            parser.error('snapshot requires --run and --output')
        # Sharing the inference lock prevents exporting a changing journal.
        with (args.run / '.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            snapshot(args.run, args.output)
    else:
        if any(v is None for v in (args.reference, args.quantized, args.output)):
            parser.error('import-m2 requires --reference, --quantized, --output')
        import_m2(read(args.config), read(args.prepared), args.reference, args.quantized, args.output)


if __name__ == '__main__':
    main()
