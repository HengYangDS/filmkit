Every task leaves the engine's whole suite passing on its commit. The whole check and the full proof each run as the child of a host ticket, `ethos host run --wait 14400 --root <checkout> -- <command>`, queued only while swap is under 32 GiB and the memory pressure level reads 1, both readings in its START line, with START and DONE lines to the keeper (host rules 2, 8 and 9); every other command named here is light. No task changes a film's file, a delivered byte, or anything below `src/` or `tests/`. Evidence, `research.md` among it, goes to `build/evidence/run-ci-on-arm-macos/`. Before the proposal is pushed, the ETHOS session has added the new tags to filmkit's two GitLab runners (design, Migration Plan, step 1).

The release runs these checks, unchanged, on every planned commit and at the archived head; this Change edits no code, test or README, so it puts none at risk:

- the size gate: the pre-commit hook's own functions (`effective_lines` and the paradigm's `size.code_effective_lines`, 500) over every planned commit, as the films session's `lane-r2b1/round_sizes.py` runs them;
- the coverage scope: the kit's whole check (`tools/fkrel/check.sh <lane> <folder> full`, its `scope` step) and `tools/js-scope.py <lane>`, which the proof's `native-behavior` gate enforces;
- the README's license link: the paradigm report's `license-entry` gap;
- Markdown spacing: the pre-commit hook's spacing check and `mise run check`'s Markdown format check;
- the proof preview's paradigm report: `ethos prove --root <lane> --json` with no required gap, then `ethos prove --readiness --execute --expect-head <head> --json`;
- `openspec validate --all --strict`, and the full proof at the archived head.

## 1. The base

- [x] 1.1 Confirm on the lane's base, `00549d3` (tag `v0.34.0`) or a later released head, every site the design's Context cites: the live files that name Windows or a runner tag, whether `.config/mise/config.toml` sets `lockfile_platforms`, each locked tool's platform tables, and the Windows entries of `uv.lock` and `package-lock.json`. Done when `research.md` names the base and states each site as found, with any line that moved.

## 2. The supply

- [x] 2.1 Delete the `windows-arm64` and `windows-x64` rows of the ETHOS pin, set `lockfile_platforms` under `[settings]` to every platform the lock holds besides Windows (design decision 2), and regenerate the lock with `mise lock`. Done when the lock's diff deletes exactly the five `platforms.windows-x64` tables and changes no other line, `mise run check:dependencies` passes, and `research.md` keeps the diff's stat and Mise's version.
- [ ] 2.2 Delete the template's commented `context` example from `openspec/config.yaml` (lines 7-10 at `00549d3`). Done when `openspec validate --specs --strict` passes.
- [ ] 2.3 Add `environments = ["sys_platform != 'win32'"]` under `[tool.uv]` in `pyproject.toml` with one comment line, and regenerate `uv.lock` with the pinned uv, `mise exec -- uv lock --python 3.12 --offline` (design decision 8, source [S8]). Done when the lock's diff removes only Windows wheels and `colorama`, and nothing else, besides the header line in which uv records the declared environments if it writes one; `mise run check:dependencies` passes; and `research.md` keeps the diff's stat, uv's version and the reason `package-lock.json` stays.
- [ ] 2.4 Check that nothing the repository declares names Windows. Done when `git grep -n -i -w windows -- .config .github .gitlab-ci.yml openspec/config.yaml pyproject.toml` prints nothing.

## 3. The CI

- [ ] 3.1 Set `[gitlab.runners.macos]` `review_tags = ["macos-latest", "review"]` and `protected_tags = ["macos-latest", "protected"]` in `.config/ci/verification.toml`, with a comment naming the owner's decision of 2026-11-25, and apply the patch that `ethos lane project --json` previews. Done when `ethos lane project --check --json` passes, the diff of `.gitlab-ci.yml` changes only the two jobs' `tags` lists, and `.github/workflows/ci.yml` is byte-identical.

## 4. Local first

Shown by `local-first.md`, which names for each clone its head, what `git remote -v` printed and the Mise variables it ran with.

- [ ] 4.1 Make three clones of the lane head by its full object name in a folder below the lane's `build/runtime/work/run-ci-on-arm-macos/`, and in each run `git remote remove origin`: one is left with no remote; one gains `gitlab` and one `github`, each at the canonical checkout's URL for it and fetched, so it holds the tracking refs a real checkout of one remote holds. In each, with `MISE_CEILING_PATHS` set to that folder, so that Mise reads no configuration of the lane above it, and `MISE_TRUSTED_CONFIG_PATHS` set to the clone's own `.config/mise/config.toml`, run `mise run bootstrap`, `ethos status --json` and `ethos prove --readiness --execute --json` at nice 10. Done when `local-first.md` records each clone's three results and none reports a required gap for an absent peer. A refusal for another reason is a blocker for the ETHOS session, and the task stays open.
- [ ] 4.2 In the clone with no remote, with the same Mise variables, run `ethos host run --wait 14400 --root <clone> -- mise run check`, and then `ethos host run --wait 14400 --root <clone> -- ethos prove --full --execute --expect-head <full head> --json`. Done when both pass at the lane head and `local-first.md` states their verdicts and seconds beside the canonical checkout's verdicts at the same head; then the three clones are removed and `local-first.md` says so. A refusal is a blocker, and the task stays open.

## 5. Acceptance on the forges

- [ ] 5.1 Push the proposal, and with it the wait for its GitLab pipeline, as the child of one host ticket held until the pipeline's last guest job ends (host rule 6, as the kit's `pipelines` step does; with no pipeline ten minutes after the push, the ticket is released and the keeper told); read GitHub's run outside the ticket. Done when `hosted.md` names GitHub's `verify (macos-latest)` and GitLab's review job by their ids, the runner's image or tags and platform as each job's log states them (an ARM64 macOS image on GitHub, `arch=arm64 os=darwin` and the tags `macos-latest` and `review` on GitLab), and each verdict at the proposal's head.

## 6. The words

- [ ] 6.1 Say in `CONTRIBUTING.md`, under "Verify a change", that GitHub and GitLab run the same proof on Apple-silicon macOS alone, GitHub on `macos-latest` and GitLab on runners tagged `macos-latest` with `review` or `protected`, and that a checkout with no remote, with one or with both checks and proves the same. Done when `mise run check`'s Markdown check passes and the section names no other platform.
- [ ] 6.2 Add the release's entries under `Unreleased` in `CHANGELOG.md` as design decision 7 states them: under `Changed`, the runner labels and where the engine is checked; under `Removed`, ETHOS's Windows archives from the Mise pin and lock, and the Windows wheels and `colorama` from uv's lock through `[tool.uv] environments`. Done when `mise run check`'s Markdown check passes.
