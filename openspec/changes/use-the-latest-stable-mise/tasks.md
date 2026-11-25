Every command named here is light and runs at nice 15; no task changes a file below `src/`, `tests/` or `examples/`, and no test reads Mise's release. The release runs its own checks on every commit and at the archived head, and the hosted runs on both forges (design, Migration Plan).

## 1. Mise's release

- [ ] 1.1 Move `[supply] mise_version` in `.config/ci/verification.toml` to 2026.11.14 and apply exactly the patch that `ethos lane project --json` previews. Done when `ethos lane project --check --json` passes, the patch changes only the `version` line of the GitHub job's `jdx/mise-action` step, and `.gitlab-ci.yml` is byte-identical.
- [ ] 1.2 Run Mise 2026.11.14's `mise lock` offline, with `MISE_CEILING_PATHS` set above the checkout, on the Mise configuration as it stands: its `min_version` stays at 2026.10.14 (design decision 2). Done when `.config/mise/config.toml` is byte-identical and the lock's bytes are unchanged, or the lock's diff is named here and kept beside the landing round (design decision 3).
- [ ] 1.3 Record the move under `Changed` in the Changelog's `Unreleased` section, naming the release, the floor that stays and the lock's outcome. Done when `npm run format:markdown:check` passes.
