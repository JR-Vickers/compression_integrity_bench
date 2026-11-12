# Compression Integrity Bench

CIB investigates how quantization changes specified epistemic behaviors. The Milestone 1 workflow uses **synthetic development fixtures only**. Milestone 2 adds a separate, explicit local MLX loading/generation check using a real BF16/4-bit pair. Neither workflow establishes compression effects. Research scope and open choices live in [PROJECT.md](docs/PROJECT.md), [METHODOLOGY.md](docs/METHODOLOGY.md), and [PLAN.md](docs/PLAN.md).

## Offline setup and workflow

Run from the repository root with Python 3.11 or newer. Runtime and tests use only the Python standard library; no credentials, accelerator, network, or model downloads are required. The source workflow also works on a Python installation without packaging tools:

```sh
python3 -m venv .venv
export PYTHONPATH="$PWD/src"
mkdir -p outputs/fixture-v1
.venv/bin/python -m cib fixture --output outputs/fixture-v1/raw.json
.venv/bin/python -m cib score --raw outputs/fixture-v1/raw.json --output outputs/fixture-v1/scores.json
.venv/bin/python -m cib report --raw outputs/fixture-v1/raw.json --scores outputs/fixture-v1/scores.json --output outputs/fixture-v1/report.md
.venv/bin/python -m unittest discover -s tests -v
```

Outputs are created exclusively: use a new directory or new filenames when repeating commands. Existing artifacts are never replaced. Open `outputs/fixture-v1/report.md` in a Markdown reader. It contains the full configuration, coverage counts, scenario metrics, independent targets, paired exact inputs, all raw responses, and failures.

To rescore saved records and regenerate the report without producing responses:

```sh
.venv/bin/python -m cib score --raw outputs/fixture-v1/raw.json --output outputs/fixture-v1/rescored.json
.venv/bin/python -m cib report --raw outputs/fixture-v1/raw.json --scores outputs/fixture-v1/rescored.json --output outputs/fixture-v1/regenerated.md
```

The test suite verifies that raw bytes remain unchanged and repeated scoring is byte-identical. Run IDs and timestamps differ across new response-production runs; scripted response content and analysis are deterministic.

For an installed `cib` entry point, the build prerequisite is setuptools >=68 (install it separately if unavailable). With that prerequisite installed, installation itself can be offline:

```sh
.venv/bin/python -m pip install --no-cache-dir --no-index --no-build-isolation --no-deps -e .
.venv/bin/cib --help
```

Observed setup: CPython 3.11.17, pip 26.2, setuptools 84.0.0 on macOS arm64; the default tests also pass on CPython 3.15.0. No runtime or test dependencies were installed. The commands above were exercised; packaging prerequisites can vary by Python distribution.

## What the fixture measures

Two hand-authored base scenarios have priors 0.5 and 0.2, supporting, opposing, and uninformative evidence, and original/swapped labels. The opposing evidence is weaker in the rare-prior scenario. Label variants remain grouped with their base scenario. Both scenarios share a template cluster; these are engineering examples, not a research sample.

Each of the 12 scenario/condition/label combinations has separate self-contained pre and post requests for each scripted provider: 24 requests per provider, 48 total. Post requests restate the prior and evidence and never include a generated pre answer. Providers receive identical rendered inputs. Provider scripts contain hand-entered probabilities independently of the scorer's exact-fraction Bayes calculation.

`fixture-perfect` has all valid, target-correct responses. `fixture-perturbed` contains known wrong probabilities plus one malformed output, one refusal, one truncation, and one infrastructure error. Stop statuses are scripted metadata, not guesses from response prose. There is one attempt per request and no retries or reprompts.

Parsing accepts only a JSON object containing exactly `probability`, whose value must be a finite JSON number in [0,1]. Duplicate keys, booleans, strings, extra fields, out-of-range numbers, and surrounding prose are invalid. JSON whitespace is accepted. This is a development parser choice, not a frozen study protocol.

The scorer calculates posterior absolute error, prior absolute error, update error, and uninformative-evidence drift. Conditions and label variants are equally weighted within each base scenario; scenarios receive equal weight. Each metric requires all its eligible conditions to be scoreable for a scenario mean. A valid incorrect answer gets its actual numerical loss; an invalid observation gets a missing score. Reports show complete-scenario contrasts and conservative full-set posterior-loss bounds using missing losses in [0,1]. These are not confidence intervals. Direction/stability thresholds are explicitly `null` and those diagnostics are disabled.

## Records and limitations

[ARCHITECTURE.md](docs/ARCHITECTURE.md) describes record ownership and lineage; [DECISIONS.md](docs/DECISIONS.md) records development choices. Small versioned task definitions and response scripts live in `src/cib/data/`; bulk outputs, models, caches, and credentials are ignored by Git. Raw v1 records include a complete task snapshot and are supported by this fixture implementation; new fixture/protocol versions require explicit implementation support.

Milestones 1 and 2 are implemented. The real feasibility probe is separate from the fixture runner; there is no integrated real comparison/resume/retry runner, empirical uncertainty analysis, held-out evaluation, or preservation threshold. Next: Milestone 3 runner integration, followed by explicit instrument development for the observed format failures. The original grant proposal was not present in the initial repository and has not been reconstructed.

## Local deployment feasibility (Milestone 2)

Selected engineering pilot pair: official `Qwen/Qwen2.5-1.5B-Instruct` at revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`, **original BF16 reference** versus a **locally derived 4-bit affine/group-64** variant. Both use MLX-LM 0.32.2 / MLX 0.32.4 on the same Apple GPU and the exact original tokenizer/template. This does not select the final study models. See [D004–D005](docs/DECISIONS.md#d004--local-pilot-deployment-pair) for verified alternatives, licensing/provenance, controls, and confounds, and [saved evidence](docs/evidence/m2/README.md) for raw outputs and measurements.

Observed on a 64 GiB M4 Max, macOS 15.7.7: each deployment loaded and generated all six predefined task prompts to EOS. Peak MLX allocations were 3.24 GB (reference) and 1.20 GB (quantized); process peak RSS was 3.46 GB and 1.24 GB. These are decimal GB, distinct counters, and smoke measurements rather than performance benchmarks. All twelve responses were Markdown-fenced JSON: **0/6 per deployment pass the unchanged strict bare-JSON parser**. Probabilities remain missing; no numerical task performance is claimed. No prompts or parser rules were changed to obtain a favorable result.

The following commands were verified from the repository root. They require Apple silicon with Metal access and Python 3.11. Preparation downloads approximately 3.1 GB of public source weights and saves an approximately 0.87 GB derivative. Initial dependency installation/preparation needs network access; generation uses local files with Hub/Transformers offline mode. No credentials or paid services are used. Keep the standard-library fixture environment separate:

```sh
python3.11 -m venv outputs/mlx-env
uv --cache-dir outputs/uv-cache pip install --python outputs/mlx-env/bin/python -r requirements-feasibility.txt
export PYTHONPATH="$PWD/src"
outputs/mlx-env/bin/python -m cib.feasibility prepare --config configs/feasibility-qwen25-1.5b.json --artifacts .cache/m2-qwen25 --output outputs/m2-prepare > outputs/m2-prepare.log 2>&1
outputs/mlx-env/bin/python -m cib.feasibility check --config configs/feasibility-qwen25-1.5b.json --prepared outputs/m2-prepare/prepared.json --deployment reference --output outputs/m2-reference-v2 > outputs/m2-reference-v2.log 2>&1
outputs/mlx-env/bin/python -m cib.feasibility check --config configs/feasibility-qwen25-1.5b.json --prepared outputs/m2-prepare/prepared.json --deployment quantized --output outputs/m2-quantized-v2 > outputs/m2-quantized-v2.log 2>&1
```

Run checks sequentially in separate processes. Output directories and derivative model directories must be new: after an existing run, choose new `--output` paths/log filenames; for a new preparation also choose a new `--artifacts` root. Existing raw records are never replaced. If preparation already exists on this machine, use just the two `check` commands with new output paths. The cached source contains the original license. No upload occurs.

The probe enforces pinned backend versions, verifies downloaded source weights are BF16 and match the official LFS hash, and fingerprints both artifacts before loading. Both deployments intentionally load the source tokenizer rather than the converter's reserialized copy. The same greedy settings, original EOS IDs, 64-token output budget, 2048-token context acceptance limit, and full unquantized KV caches apply to both. No separate reasoning mode, output constraints, penalties, retries, or generated prior answers enter the inputs. Floating-point accumulation remains backend-defined; quantized and BF16 kernels differ.

The first sandbox preparation failed because Metal was unavailable; rerunning with local GPU access succeeded. Initial checks completed generation but failed cache dtype inspection on its integer offset; those records remain at `outputs/m2-reference` and `outputs/m2-quantized`. The fixed `*-v2` records preserve the same prompts and raw text and include BF16 cache evidence. In a restricted execution environment, local Metal access must be permitted to run these commands. Failures and partial streamed outputs remain saved rather than being silently retried.

Default regression checks still need no MLX installation, network, model files, or accelerator:

```sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

All 13 tests passed on CPython 3.11.17 and 3.15.0. The original offline fixture commands were rerun successfully with artifacts at `outputs/m2-offline-regression/report.md`.
