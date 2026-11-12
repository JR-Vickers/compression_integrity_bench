"""One optional local backend. Only messages enter templating; no scorer data."""
from collections import Counter
import os
from pathlib import Path

from .feasibility import cache_metadata, environment, inventory
from .records import digest, read


class MLXAdapter:
    def __init__(self, config, prepared, deployment):
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        import mlx.core as mx
        from mlx.utils import tree_flatten
        from mlx_lm.utils import load_model, load_tokenizer
        self.mx, self.config = mx, config
        for name in {'reference', deployment}:
            if inventory(prepared[name]['path']) != prepared[name]['files']:
                raise ValueError('artifact fingerprint changed')
        mx.set_default_device(mx.gpu)
        self.model, model_config = load_model(Path(prepared[deployment]['path']), lazy=False,
                                             trust_remote_code=False)
        source = Path(prepared['reference']['path'])
        eos = read(source / 'generation_config.json')['eos_token_id']
        self.tokenizer = load_tokenizer(source, {'trust_remote_code': False, 'local_files_only': True},
                                        eos_token_ids=eos)
        self.metadata = {
            'environment': environment(config), 'device': str(mx.default_device()),
            'model_config': model_config, 'chat_template': self.tokenizer.chat_template,
            'template_sha256': digest(self.tokenizer.chat_template),
            'eos_token_ids': sorted(self.tokenizer.eos_token_ids),
            'parameter_dtype_counts': dict(Counter(str(v.dtype) for _, v in tree_flatten(self.model.parameters()))),
            'quantized_modules': [n for n, m in self.model.named_modules() if hasattr(m, 'bits')]}
        expected = ({'mlx.core.bfloat16': 338} if deployment == 'reference' else
                    {'mlx.core.bfloat16': 535, 'mlx.core.uint32': 197})
        if self.metadata['parameter_dtype_counts'] != expected:
            raise ValueError('unexpected loaded parameter precision')

    def render(self, payload):
        rendered = self.tokenizer.apply_chat_template(payload['messages'], tokenize=False,
                                                       add_generation_prompt=True)
        tokens = self.tokenizer.encode(rendered, add_special_tokens=False)
        if len(tokens) + self.config['generation']['max_tokens'] > self.config['generation']['context_limit']:
            raise ValueError('context acceptance limit exceeded')
        return {'rendered_input': rendered, 'input_token_ids': tokens}

    def generate(self, actual, emit):
        from mlx_lm import stream_generate
        from mlx_lm.models.cache import make_prompt_cache
        from mlx_lm.sample_utils import make_sampler
        g = self.config['generation']
        self.mx.random.seed(g['seed'])
        cache = make_prompt_cache(self.model)
        for response in stream_generate(self.model, self.tokenizer, prompt=actual['input_token_ids'],
                max_tokens=g['max_tokens'], sampler=make_sampler(temp=g['temperature']),
                logits_processors=[], prompt_cache=cache, kv_bits=None, max_kv_size=None,
                prefill_step_size=g['prefill_step_size']):
            emit({k: getattr(response, k) for k in ('text', 'token', 'finish_reason', 'generation_tokens')})
        self.mx.synchronize()
        return cache_metadata(cache)
