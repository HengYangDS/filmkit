## 1. Repair

- [x] 1.1 Read the band's measures inside a block that closes the file (`picture/ground.py`, `ground_check`); verify `tests/picture/test_derivation.py` with `-W error` (six of its nine tests fail on the code before, on a host with FFmpeg) and the whole suite with `-W error`. On 18 November 2026 the nine tests pass with `-W error`, and the whole suite run with it on a clone of `aa416b2` with the repair fails no test on a warning.
