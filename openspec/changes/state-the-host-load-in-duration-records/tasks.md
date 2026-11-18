## 1. The record and the command

- [ ] 1.1 Read the host's 1-minute load average at a run's start and at its end and state both in the duration record as `load_1m`, null on a host that states none (`durations.host_load`, `Run`); verify `tests/test_durations.py` (both readings, a refused command, a host whose average cannot be read and one without `os.getloadavg`).
- [ ] 1.2 Print a record's load beside its seconds and the range of the counted commands' loads after the build's time, and nothing for a record that states none (`durations.load_text`, `lines`, `load_range`, `build_time`); verify `tests/test_durations.py` (a line with two figures, with one, after `not completed`, and of a record without the field) and `tests/test_build_durations.py` (the range, commands that state none, a build without a load).

## 2. Acceptance

- [ ] 2.1 Run every command of `mise run check` with the suite's warnings as errors and the proof's static lint, the whole suite as the child of a host ticket; verify that each passes on the Change's head.
- [ ] 2.2 State the field and the two places it is printed in the README's "How long a build takes" and in the Changelog; verify the repository's Markdown check on both files.
- [ ] 2.3 Promote the records the design cites to `build/evidence/state-the-host-load-in-duration-records/` of the canonical checkout; done when `load-probe.py`, `load-probe.txt` and `build-time-requirements.txt` stand there.
