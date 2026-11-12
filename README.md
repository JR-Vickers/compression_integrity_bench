# Compression Integrity Bench

CIB investigates how quantization changes specified epistemic behaviors. The implemented Milestone 1 workflow uses **synthetic development fixtures only**. It runs no models and produces no evidence about compression effects. Research scope and open choices live in [PROJECT.md](docs/PROJECT.md), [METHODOLOGY.md](docs/METHODOLOGY.md), and [PLAN.md](docs/PLAN.md).

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

Only Milestone 1 is implemented. There is no real inference adapter, resume/retry runner, empirical uncertainty analysis, held-out data, preservation threshold, or result from a real model. Next: declare hardware and budget, then establish a feasible same-checkpoint reference/quantized deployment pair. The original grant proposal was not present in the initial repository and has not been reconstructed.
