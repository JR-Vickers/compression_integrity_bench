# Working on Compression Integrity Bench

## Purpose and document navigation

CIB measures how quantization changes specified epistemic behaviors of open-weight language models. Credible improvements, regressions, and null findings are all valid outcomes.

- Use [PROJECT.md](docs/PROJECT.md) for objectives, scope, deliverables, and completion criteria.
- Use [METHODOLOGY.md](docs/METHODOLOGY.md) when changing tasks, prompts, deployment controls, scoring, aggregation, or interpretation.
- Use [PLAN.md](docs/PLAN.md) for milestone scope, dependencies, and acceptance criteria.
- Consult `docs/DECISIONS.md` and `docs/ARCHITECTURE.md` when they exist and concern the work at hand.

The project begins with specifications. A proposed choice in a document remains proposed until explicitly resolved. Reviewing the documents does not silently choose a model, backend, sample size, or preservation threshold.

## How to work

Implement the requested milestone through its acceptance criteria, including running the relevant checks and fixing failures caused by the change. Keep changes focused on that milestone. Resolve routine engineering choices directly and record consequential rationale.

If a research decision is unresolved, keep it explicit and configurable. Continue work that does not depend on that decision. Surface a narrow conflict when it affects the validity or meaning of the requested result.

Build the smallest complete pipeline first. Keep task construction, inference, scoring, and reporting separable. Introduce additional backends, services, and abstractions when a concrete requirement justifies them.

## Research and data integrity

- Apply the measurement rules in `docs/METHODOLOGY.md`; do not change a scientific definition incidentally while implementing it.
- Score both deployments against independent targets or rubrics. Reference-model output is not an answer key.
- Preserve scenario grouping, deployment identity, exact inputs, raw outputs, attempt records, and scorer lineage.
- Keep original inference outputs immutable; rescoring creates derived artifacts.
- Distinguish infrastructure errors, malformed outputs, refusals, truncation, and valid incorrect responses. Missing scores remain missing.
- Keep scorer-only targets and annotations out of model-visible inputs.
- Label fixtures, exploratory pilot results, and held-out results explicitly. Synthetic responses must never appear as measured model performance.
- Preserve negative and inconclusive results. Avoid outcome-driven changes to tasks, exclusions, or metrics.

## Implementation and verification

Use a small Python package and command-line workflow for the initial implementation. Choose compatible versions and dependencies during bootstrap and record the actual setup in the root `README.md`.

Do not present proposed commands as working commands. Once a command exists, document its real invocation and verify the documented workflow.

Default tests must work without network access, model downloads, API credentials, or an accelerator. Use independent numerical examples and synthetic response fixtures. Keep real inference checks separate and explicitly configured.

Prioritize meaningful checks of analytic targets, parsing, pairing, missing-data handling, aggregation, and regeneration from saved outputs. Run affected checks after code changes; avoid rerunning inference when saved responses suffice.

Keep downloaded weights, caches, credentials, and bulk run artifacts out of Git. Retain versioned configurations and small, clearly labeled reproducibility fixtures.

## Documentation and handoff

Update affected documentation when behavior or setup changes. Update milestone status and verification evidence in `docs/PLAN.md`; use concise summaries rather than a transcript of tool calls.

Create `docs/DECISIONS.md` when the first consequential choice needs recording. Include status, rationale, consequences, and any superseded choice. Add a short architecture note once interfaces and data flow are concrete.

At handoff, report what works, what was verified, material limitations, and the next unresolved dependency. Never claim a test, experiment, or milestone completed without observed evidence.
