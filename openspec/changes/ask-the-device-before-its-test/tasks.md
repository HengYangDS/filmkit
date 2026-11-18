## 1. The probe

- [x] 1.1 Ask the device for one evaluation in a child process and skip a test marked `metal` where it gives none, named in the run's header and summary (`tests/conftest.py`: `metal_evaluates`, `HOST_TOOLS["metal"]`); mark `test_local_narration_bounds_retained_gpu_buffer_cache`; verify with `tests/test_host_probes.py` (the probe's two answers, a probe that does not end, a host whose runtime does not load, the skip and its reason) and the marked test on the release host, whose header reads "host Metal evaluation: present".
