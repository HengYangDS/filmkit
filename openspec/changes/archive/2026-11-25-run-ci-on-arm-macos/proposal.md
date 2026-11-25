## Why

On 25 November 2026 the owner ruled for every repository that ETHOS governs, as relayed by the session that onboards repositories to ETHOS [S1, C-11, D-63]: Windows support leaves CI and every other part, and a macOS-only project runs only ARM macOS (13:45); every project works with no remote, one or both, local first, the shared parts mirrored (13:47); and the label is `macos-latest`, GitLab adding `review` or `protected` (13:54).

filmkit already runs CI only on ARM macOS [S2]. Left: GitLab's old runner tags, ETHOS's Windows archives in the Mise pin and a Windows table for each of the five tools in the Mise lock, Windows wheels in uv's lock, a Windows example in `openspec/config.yaml`, and no requirement that states where the engine is checked or that it checks the same with no remote, one or both.

## What Changes

- **One label on both forges.** The GitLab review job selects `macos-latest` and `review`, the protected job `macos-latest` and `protected`; both CI files are generated again from `.config/ci/` by `ethos lane project`. GitHub's file comes out unchanged, since its job already runs on `macos-latest`.
- **No Windows in the Mise supply.** The ETHOS pin loses its two Windows rows. The Mise configuration declares `lockfile_platforms` as the platforms the lock holds besides Windows, and Mise's own `mise lock` then removes the five Windows tables and nothing else; the Linux tables stay, by the ETHOS session's answer of 15:09 for every governed repository (design decision 2).
- **No Windows in uv's lock.** `[tool.uv]` gains `environments = ["sys_platform != 'win32'"]`, and `uv lock` drops the 174 Windows wheels and `colorama`, the one package that only Windows pulls in; the engine's record of what it was released on, which the fix task writes from that lock, drops `colorama` with it. npm's lock stays as npm writes it: npm has no setting that leaves an optional platform package out of its lock (design decision 8).
- **No Windows example in the OpenSpec configuration.** The template's commented `context` example goes.
- **A requirement for where and how the engine is checked**, in the new capability `engine-verification`: on Apple-silicon macOS alone; one check projected to both forges from one declaration; the whole check and the full proof passing with no remote; and ETHOS's status and the proof's readiness reporting no required gap for an absent peer.
- **The contributing guide** says where CI runs and that the number of remotes changes neither the check nor the proof.

filmkit is macOS-only, and no Linux job is added: the engine's speech models run on MLX, its renderer loads the canvas build `@napi-rs/canvas-darwin-arm64`, and its picture checks run the browser build `chrome-headless-shell-mac-arm64` (design decision 3). No engine code, test, film or delivered byte changes; the engine's record loses one package (design decision 8).

Out of scope, each with its owner in the design: the GitLab runner registrations (the ETHOS session); the kit's release tool, which is not part of the engine (design decision 6 states what it owes); the code paths that serve Linux, which stay because the 13:45 words remove Windows and not Linux, and no engine code serves Windows; npm's two optional win32 entries; and the Mise lock's format upgrade.

## Capabilities

### New Capabilities

- `engine-verification`: where and how the engine's head is checked: Apple-silicon macOS alone, one check projected to each forge from one declaration, and the same check and proof whatever remotes a checkout has.

### Modified Capabilities

None.

## Impact

- **Configuration:** `.config/ci/verification.toml` (the two GitLab tag lists), the generated `.gitlab-ci.yml`, `.config/mise/config.toml` (the pin's Windows rows, `lockfile_platforms`), `.config/mise/mise.lock` (through `mise lock`), `pyproject.toml` (`[tool.uv] environments`), `uv.lock` (through `uv lock`), `src/filmkit/released.json` (through `mise run fix`), `openspec/config.yaml`.
- **Text:** `CONTRIBUTING.md`, `CHANGELOG.md`; the new specification through its delta.
- **Unchanged:** `.github/workflows/ci.yml` (regenerated, same bytes), `.config/ci/runners.toml`, `.ethos/release.toml`, `package-lock.json`, the README, every other file below `src/` and every file below `tests/`.
- **Outside the repository:** the ETHOS session adds `macos-latest` with `review`, and `macos-latest` with `protected`, to filmkit's two GitLab runners before the proposal is pushed, and drops the old tags after `main` is published (design, Migration Plan). GitHub requires no status check on filmkit, so a renamed job breaks no protection [S3].
- **Host:** each push that starts a GitLab pipeline holds one host ticket until the pipeline's last guest job ends (host rule 6); the full proof in a clone with no remote holds one ticket of its own.
- **Release:** a patch, 0.34.1, if it lands alone after 0.34.0; it rides in the same release as `measure-balance-on-content` if the two land together.
- **Films:** none. Each film takes the same rules in its own repository with its December edition [S1, C-11 relations].

Owner: the engine's maintainer (the films session).

## Sources

Numbered as in the design.

- **[S1]** `build/evidence/owner-words.md` in the engine's canonical checkout: D-63 and C-11, read on 2026-11-25 at about 20:20.
- **[S2]** The engine at `00549d3` (tag `v0.34.0`): `.config/ci/verification.toml`, `.github/workflows/ci.yml`, `.gitlab-ci.yml`, `.config/mise/config.toml`, `.config/mise/mise.lock`, `pyproject.toml`, `uv.lock`.
- **[S3]** `build/runtime/work/ci-windows-inventory.md` beside the drafts: the GitHub rulesets read through the API at about 14:50, and the ETHOS session's answers of 14:57, 15:06, 15:08 and 18:09 (relayed, not read first-hand).
