## Context

See [proposal.md](proposal.md). `tests/conftest.py` holds two readings of a host. `speech_runtime` imports `mlx.core` in a child process and leaves five modules uncollected where the import fails. `HOST_TOOLS` names the tools a marked test runs; a test whose tool is absent is skipped, and the run's header and summary name each. One test of the suite evaluates on the device itself: it frees distinctly sized buffers and reads how much the runtime's cache retains; every other test of the speech modules narrates with a model double.

What was read on the failing machine on 18 November 2026 [S1]: as two runner users with two environments, `mx.eval` of 1,024 `float32` values fails in 0.2 s with `Unable to load kernel … Compilation failed`, the machine logs `kIOGPUCommandBufferCallbackErrorHang` of its paravirtual GPU, and `import mlx.core` succeeds.

## Goals / Non-Goals

**Goals:**

- A host whose device evaluates nothing is named by the run, and the run fails no test for it.

**Non-Goals:**

- Repairing a host. The machine's GPU is its owner's to restore.
- Proving on a hosted runner that the cache stays bounded. The release proof runs on a host whose device evaluates, and says in its header that it does.

## Decisions

1. **The device is asked for what the test needs of it: one evaluation, in a child process, once a run.**
   - **Rests on:** [S1]: the import passes and every evaluation fails on the same device; [S2]: the probe's statement fails there with a status other than 0 and passes on the release host.
   - **Considered:** (a) leaving the test to fail on such a host, which turns a hosted proof red for the runner's device (two tickets of the host's queue on 18 November); (b) leaving the speech modules uncollected where the evaluation fails, by widening `speech_runtime`: the five modules' other tests, which narrate with a double and pass on that host, would no longer run there; (c) a marker for a test that evaluates, skipped and named like a test whose host tool is absent; (d) trying again inside the test: the fault did not pass in three hours.
   - **Chosen because:** (c) loses the one test that cannot run and keeps the rest, in the form the suite already uses for what a host lacks.
   - **Applies to:** `tests/conftest.py` (`metal_evaluates`, `HOST_TOOLS["metal"]`, the reason of a skip) and the marked test.
   - **Reopened when:** a second test evaluates on the device (it takes the marker), or a hosted run must prove an evaluation (the marker's absence then becomes an error on that runner, by an option).
   - **Sources:** [S1] [S2].
2. **A probe that does not end is a device that does not evaluate.**
   - **Rests on:** the fault's name, a hang of a command buffer; on the failing machine the error came back in 0.2 s, and nothing says it always will.
   - **Considered:** (a) letting the timeout raise at collection, which fails the whole run; (b) reading it as no evaluation.
   - **Chosen because:** (b): the question has two answers.
   - **Applies to:** `metal_evaluates`; the probe waits 120 s, as the load's probe does.
   - **Reopened when:** not applicable.
   - **Sources:** [S1].

## Risks / Trade-offs

- A release host whose device fails would skip the test instead of failing it. → The run's header and summary name the skip, the proof's record counts it, and a narration on such a host fails at its first take.
- One more child process a run. → It imports the runtime and evaluates 1,024 values; the load's probe already starts one.

## Sources

Read or measured on 18 November 2026. Paths under `build/evidence/` are the canonical checkout's local evidence.

- **[S1] The failing machine:** `build/evidence/release-0.23.1/guest-job-73051/cause.md` with the suite's output of both jobs, the proof payload of the first, and the two diagnostics' output (`mlx-probe.raw`, `mlx-probe2.raw`): the CI macOS guest of this host, GitLab jobs 73051 (12:38 CST) and 73083 (14:04 CST) of commit `27e1027`.
- **[S2] The probe on both hosts:** the same record (`mlx-probe.raw`: the statement `mx.eval(mx.zeros((1024,), dtype=mx.float32) + 1)` fails as the review runner's user) and `build/evidence/ask-the-device-before-its-test/focused.log` (on the release host the run's header reads "host Metal evaluation: present" and the marked test passes).
