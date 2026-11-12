"""Audit saved M2 tokens using the source tokenizer, without MLX or generation."""
import argparse
import json
from pathlib import Path

from tokenizers import Tokenizer

from cib.records import file_hash, read, write_new


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared', type=Path, default=Path('outputs/m2-prepare/prepared.json'))
    parser.add_argument('--streams-root', type=Path, default=Path('outputs'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    prepared = read(args.prepared)
    tokenizer = Tokenizer.from_file(str(Path(prepared['reference']['path']) / 'tokenizer.json'))
    rows = []
    for name in ('reference', 'quantized'):
        root = args.streams_root / ('m2-' + name + '-v2')
        for index, attempt in enumerate(read(root / 'checked.json')['attempts']):
            stream = root / f'stream-{index}.jsonl'
            events = [json.loads(line) for line in stream.read_text().splitlines()]
            decoded = tokenizer.decode([event['token'] for event in events], skip_special_tokens=True)
            rows.append({
                'deployment': name, 'index': index, 'stream_sha256': file_hash(stream),
                'joined_stream_equals_raw': ''.join(e['text'] for e in events) == attempt['raw_text'],
                'decoded_generated_tokens': decoded,
                'decoded_tokens_equal_raw': decoded == attempt['raw_text'],
                'raw_text': attempt['raw_text'],
                'rendered_contains_fence': '```' in attempt['rendered_input']})
    write_new(args.output, rows)
    if not all(row['joined_stream_equals_raw'] and row['decoded_tokens_equal_raw']
               and not row['rendered_contains_fence'] for row in rows):
        raise ValueError('stream audit failed; evidence retained')
    print(f'{len(rows)} streams match raw text and decoded generated tokens; no input contains a fence')


if __name__ == '__main__':
    main()
