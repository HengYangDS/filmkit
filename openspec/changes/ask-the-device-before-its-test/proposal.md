## Why

On 18 November 2026 the proposal of 0.23.1 failed twice in its hosted proof on a virtual machine, an hour of the host's queue each time, on a commit whose proof on the release host and whose hosted run on another forge had passed. One test of 1,609 failed: `test_local_narration_bounds_retained_gpu_buffer_cache`, the only test that evaluates an array on the host's Metal device. The machine's paravirtual GPU had stopped building compute pipelines that morning; the speech runtime still loaded there, so the suite's question to its host, whether `mlx.core` imports, was answered yes.

The suite already says what a host lacks instead of failing on it: modules that load the speech runtime are not collected where it does not load, and tests that run FFmpeg, ExifTool or rsync 3 are skipped by name where the tool is absent. The device was asked the wrong question: whether the runtime loads, where the test needs it to evaluate.

## What Changes

- The suite asks the Metal device for one small evaluation in a child process, and a test marked `metal` is skipped where the device gives none; the header and the summary of the run say so, as they do for a host tool.
- The one test that evaluates on the device is marked.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. No requirement of the engine changes: the suite's reading of its host is not a requirement of a film's build, so `.openspec.yaml` sets `skip_specs: true`.

## Impact

`tests/conftest.py`, `tests/narration/test_synthesis.py`, `tests/test_host_probes.py`. No source file of the engine, no gate, no record and no byte of a film changes, and the Changelog gains no entry. `tasks.md` is the sole progress ledger.
