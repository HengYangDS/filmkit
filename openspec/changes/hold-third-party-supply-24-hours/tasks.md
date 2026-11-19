## 1. The declarations

- [x] 1.1 Declare `minimum_release_age = "24h"` in `.config/mise/config.toml` and `min-release-age=1` in `.config/npm/npmrc`; verify under Mise that each reader states the new age and that `mise install --locked` and `mise run bootstrap` pass. On 19 November 2026, in a clone of `4893228` with the lines, Mise states `24h`, npm states `1` from the repository's own file, `mise install --locked` finds every tool installed and `mise run bootstrap` passes.
- [x] 1.2 Declare `exclude-newer = "24 hours"` under `[tool.uv]` in `pyproject.toml` and write the uv lock again in the same commit; verify that the lock holds the packages and artifacts it held before, and that `uv lock --check --offline` and `mise run check:dependencies` pass. On 19 November 2026 the relock resolved 59 packages before and after, with the same names, versions and artifacts; the lock gained two options, the span among them; the lock check passed twice, 65 s apart, and `mise run check:dependencies` passed.
- [x] 1.3 State the age and uv's line in the Changelog; verify the repository's Markdown check. On 19 November 2026 the Changelog's unreleased section states both, and the Markdown check passes with it.

## 2. Verification

- [ ] 2.1 Run every command of the repository's check on the lane, the whole suite as the child of a host ticket; verify that each passes.
