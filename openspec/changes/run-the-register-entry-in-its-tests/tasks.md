## 1. The entry in its tests

- [ ] 1.1 Add a test to `tests/register/test_register_check.py` that runs `filmkit.register` as `python -m` runs it, in the test's process, and holds the report the run prints and the refusal it exits with. Done when the file's tests pass.
- [ ] 1.2 Every line of `src/filmkit/register/__main__.py` runs in the register tests' process. Done when `pytest tests/register --cov=src/filmkit/register --cov-report=term-missing` reports the file at 100 %; at `1e4d459` it reports 0 %.
