## 1. Engine

- [x] 1.1 Pass `reviewedRuns.frame` whether a declared stage cut of the frame's scene falls since the previous sample, stop counting such a frame as growth, and report settled runs that a stage cut or another scene ends as `finished`; verify the balance tests. The new test fails on the 0.15.0 rule and passes here.
- [x] 1.2 Report `off_centre_finished` in the frame audit and refuse it in `check-picture`, keeping `off_centre_settled` recorded; verify the frame-audit and gate tests.

## 2. Films and release

- [x] 2.1 Run the frame audit of this lane on the three films' current compositions and timelines; verify that the essentials film's 07.3 before its repair is reported as finished and that each film's finished runs are listed. Before its repair 07.3 is finished at −64.0 px in Chinese (493.17–504.03 s) and −73.4 px in English (490.40–501.90 s), and after it neither edition has a run; the ETHOS film's English 05 is finished at 50.6 px (477.60–482.13 s), and the DDWG film has none (`build/evidence/gate-settled-runs-at-stage-cuts/films.json`).
- [x] 2.2 Prepare 0.16.0: `VERSION`, the CHANGELOG section and the README's balance paragraph and pin; verify `mise run check`. It passes: 155 Node tests, the Markdown check and 958 Python tests.
