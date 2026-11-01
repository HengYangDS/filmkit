# Tasks

## 1. Code ceiling

- [ ] 1.1 Move the frame rules and the reviewers' measures from `geometry-check.mjs` to `src/filmkit/picture/rules/` and import them from their owners; done when the serialised rules' texts equal the old ones and the page program test passes.
- [ ] 1.2 Split `frame-audit.mjs` into its entry and `frame-audit/marks.mjs`, `composition.mjs` and `report.mjs`; done when its output and report files equal the old modules' byte for byte on both editions' timelines.
- [ ] 1.3 Move `motion-audit.mjs`'s analysis and report to `motion-audit/report.mjs`; done when its summary and report equal the old modules' byte for byte on both editions' timelines.
- [ ] 1.4 Split `tests/picture/picture.test.mjs` by subject over `tests/picture/sample-film.mjs` and name each file in `package.json`'s test command; done when `npm test` passes the same test names and every code file measures at most 500 effective lines.

## 2. Explicit encoding

- [ ] 2.1 Name `encoding="utf-8"` at the eight calls in `tests/delivery/conftest.py`, `tests/delivery/test_packaging.py` and `tests/picture/test_rendering.py`; done when Ruff's unspecified-encoding rule reports nothing and the Python tests pass.

## 3. Runtime

- [ ] 3.1 Replace the 0.2.0-alpha.21 declaration in `.config/mise/config.toml` with the one published with 0.2.0-alpha.25 and lock it again with native `mise lock`; done when the declaration equals the published one and the lock holds 0.2.0-alpha.25 at the declared checksums for each platform it records, with no 0.2.0-alpha.21 entry left.
- [ ] 3.2 Bind the repository family to the 0.2.0-alpha.25 runtime with the locked console's `hook install`, keeping 0.2.0-alpha.21 as the rollback; done when `ethos status` reports the lane under the 0.2.0-alpha.25 runtime.
- [ ] 3.3 Record the move under Unreleased in the Changelog; done when the repository check passes.
- [ ] 3.4 Regenerate the CI projection with `ethos lane project`; done when the projection check conforms.

## Workflow follow-up

- Archive the Change, prove the archived head once, land it and close out.
- Publication waits for the user's approval of a public push of this repository.
