## Context

See [proposal.md](proposal.md) for the decision and the place it changes. The owner's words came relayed, and so did his confirmation of the reading: every Mise pin of every repository ETHOS governs moves to Mise's latest stable release, 2026.11.14 now, one supply Change for each repository; filmkit's is the Change after 0.34.1 [S1, C-12]. The repository's supply rule asks the same of every tool: its latest stable release, once 24 hours old [S3].

**How the release reaches each place.** The CI declaration `.config/ci/verification.toml` holds the release at line 7, `[supply] mise_version` [S4]. ETHOS's CI model requires the field to read as a Mise release, `YYYY.M.N`, and puts it into one place only: the GitHub job's step `jdx/mise-action@b44d12e7…` takes it as `with.version`, beside `install: false` and `cache: false` [S6]. `ethos lane project` writes `.github/workflows/ci.yml` (line 33) and `.gitlab-ci.yml` from the declaration, and `ethos lane project --check` refuses a CI file that differs from what it would write; the requirement that both files are generated, never edited by hand, rests on that check [S7]. GitLab's jobs run `mise install --locked` with the Mise of the runner they land on; the model pins no release for them. A developer's checkout runs the Mise its owner installs: Homebrew on this host [S5].

**The floor.** `.config/mise/config.toml` has set `min_version = "2026.10.14"` since the toolchain was first bound on 30 October 2026 [S4]. Mise reads a plain string as a hard minimum: an older Mise stops with an error and prints how to upgrade. A table `{ hard, soft }` warns below `soft` and stops only below `hard`, and Mise's documentation advises `hard` for the oldest release that understands the file and `soft` for the release the team should be on [S8]. The two earlier Changes that moved the hosted job's Mise, to 2026.11.10 and 2026.11.11, kept the floor as a non-goal, as the oldest Mise that reads the configuration. For every governed repository, the ETHOS session answered on 26 November at about 06:30: leave `min_version` where it is and move only the CI pins, since the owner's confirmed reading covers the pins only; the rule for the floor's form goes to ETHOS's CI paradigm (97f828, by 3 December) [S10]. DDWG did the same: at its `dev` head `4f4a228b`, which archives its Change `move-hosted-mise-2026-11-14`, `mise_version` reads 2026.11.14 and `min_version` 2026.10.14 [S11]. Neither `CONTRIBUTING.md` nor the README names a Mise release: both say that Mise installs the locked tools.

**The specifications.** No requirement of `openspec/specs/` names Mise's release or where it comes from. Of its 26 capabilities, `formal-register` names Mise only in the line `mise use github:vale-cli/vale@<version>` that pins Vale, and `engine-verification` requires both CI files to be generated from one declaration and every job to install the same locked supply; it names Mise's lock and `mise run bootstrap`, not Mise's own release [S7].

**What the releases since 2026.11.11 change for the engine** [S2]. 2026.11.12 records in the lock, as `unsupported_platforms`, the platforms a tool has no build for, without a new lock format, and refuses a `mise lock` upgrade that would drop a platform. 2026.11.13 stops the configuration search at a ceiling path reached through a symbolic link, reads a task's `tools` pin from the task configuration's own lock, and stops rewriting a `pipx:` or `pypi:` tool's lock entry when only the release-age cutoff moved. 2026.11.14 adds an experimental sandbox for cached tasks, enforced on Linux only, and makes an invalid `#MISE` header of a file task an error. The engine has no file task, no task that declares `tools` or `cache`, and no `pipx:` or `pypi:` tool; GitLab's jobs set `MISE_CEILING_PATHS` to the folder above the checkout, where 2026.11.13 only makes Mise honour that ceiling also when the path to it passes through a symbolic link, as Git does. Mise 2026.11.14 already wrote the lock that 0.34.1 holds, offline, when `run-ci-on-arm-macos` removed its Windows tables [S9].

## Goals / Non-Goals

**Goals:**

- The hosted GitHub job installs Mise 2026.11.14, the release the owner's decision names.
- The CI files stay ETHOS's projection of the declaration.

**Non-Goals:**

- **The floor.** `min_version` stays (decision 2); a rule for its form is ETHOS's CI paradigm's to set, for every governed repository [S10].
- **The GitLab guest's Mise.** It is the ETHOS session's; by that session's word it reads 2026.11.14 on every runner account since 05:50 [S1].
- **The films' pins.** Each film moves its own in its December lane, after the films' freeze [S1].
- **The lock's format.** Mise suggests `mise lock --upgrade` for the lock's format version 3; that is a change of its own, as `run-ci-on-arm-macos` left it.
- **Any tool of the lock, any gate, runner declaration or publication.**

## Decisions

### 1. The declaration carries the hosted job's release, and the projection writes it

- **Rests on:** the CI model's single use of `[supply] mise_version` [S6] and the requirement that the CI files are generated, never edited by hand [S7].
- **Options:** (a) move `[supply] mise_version`, preview `ethos lane project` and apply exactly its patch; (b) write the new `version` into `.github/workflows/ci.yml` by hand.
- **Chosen because:** (a) is the only way that `ethos lane project --check` passes afterwards; (b) leaves a file the check refuses. The release then stands in one place, the declaration, and the workflow is derived from it.

### 2. The floor stays at 2026.10.14

- **Rests on:** the ETHOS session's answer for every governed repository (relayed) [S10], DDWG's move to 2026.11.14 [S11], and Mise's meaning of `min_version` [S8].
- **Options:** (a) `min_version = "2026.11.14"`, a hard minimum; (b) `min_version = { hard = "2026.10.14", soft = "2026.11.14" }`, which warns on an older Mise; (c) leave it at 2026.10.14.
- **Chosen because:** (c). The owner's confirmed reading moves Mise's pins, and `min_version` pins nothing: Mise reads it as the oldest release that understands the file, which this Change does not move. The ETHOS session's answer keeps the floor for every governed repository, DDWG kept it in its own move to 2026.11.14, and the engine's two earlier Mise Changes kept it. Whether a floor follows the pin, and in which form, is one rule for every governed repository, which ETHOS's CI paradigm sets [S10]; the engine takes it in a Change of its own once it is set.
- **Trade-off:** a GitLab runner or a checkout on a Mise from 2026.10.14 to 2026.11.13 still runs the checks, without a warning. The hosted GitHub job runs 2026.11.14, and the guest runs it by the ETHOS session's word [S1].

### 3. The lock is written by Mise 2026.11.14 and kept as it comes out

- **Rests on:** the lock is Mise's to write, and the engine's checks install from it.
- **Chosen because:** running Mise 2026.11.14's own `mise lock` on the configuration as it stands shows what the release does to the lock; task 1.2 keeps its diff if it writes one, and otherwise the lock's bytes stay as 0.34.1 holds them.

## Risks / Trade-offs

- [A GitLab runner is left on an older Mise] → the floor does not stop it; the ETHOS session owns the guest's Mise and read 2026.11.14 back on every runner account (relayed) [S1].
- [Mise 2026.11.14 changes the hosted bootstrap] → the release's hosted runs on both forges qualify it before it lands; restoring the earlier value rolls it back.
- [ETHOS's CI paradigm sets a rule for the floor] → the engine follows it in a Change of its own [S10].
- [A later Mise release passes its 24 hours] → the next Change moves `[supply] mise_version` again.

## Migration Plan

The Change is built in its lane: the declaration and the projection in one step through `ethos lane project --apply --authorize`, then the Changelog. The release (the films session) archives it, proves the archived head once and runs the proposal's pipelines, GitLab's on the guest's Mise, each push as the child of one host ticket (host rule 6). To roll back, restore `mise_version = "2026.11.11"` and write the CI files again with `ethos lane project`.

## Sources

- **[S1]** `build/evidence/owner-words.md` in the engine's canonical checkout, C-12, read on 2026-11-26 at about 06:00 and again at 06:32: the owner's words of 05:49, relayed at about 05:54 by the session that onboards repositories to ETHOS, with that session's reading of 2026.11.14, its upgrade of the guest at 05:50 and its list of the repositories that pin 2026.11.11; and the confirmation, the owner's words of 06:08 to that session, relayed at about 06:09 (all of it relayed; none read first-hand by the films session).
- **[S2]** Mise's GitHub releases, read through GitHub's API on 2026-11-25 at 22:01 UTC (2026-11-26 06:01 CST): `releases/latest` is `v2026.11.14`, published `2026-11-24T11:00:43Z`, neither a draft nor a prerelease, at <https://github.com/jdx/mise/releases/tag/v2026.11.14>; the stable releases before it are 2026.11.13 (`2026-11-23T23:20:03Z`), 2026.11.12 (`2026-11-21T11:26:01Z`) and 2026.11.11 (`2026-11-20T15:20:06Z`), and 2026.10.14 was published at `2026-10-18T18:37:28Z`; and the release notes of 2026.11.12, 2026.11.13 and 2026.11.14.
- **[S3]** `.config/mise/config.toml`, `minimum_release_age = "24h"`, and the archived Changes `2026-11-19-hold-third-party-supply-24-hours` (the owner's 24 hours of 19 November) and `2026-11-21-move-hosted-mise-2026-11-11` (his direction of 18 November that every governed repository takes the latest stable release of its supply). 24 hours after `2026-11-24T11:00:43Z` is `2026-11-25T11:00:43Z`, eleven hours before [S2] was read.
- **[S4]** The engine at `38d661c` (0.34.1 with `run-ci-on-arm-macos` archived), read on 2026-11-26: `.config/ci/verification.toml` line 7, `.github/workflows/ci.yml` line 33, `.config/mise/config.toml` line 1 (since commit `e7c0afc`), `.gitlab-ci.yml`, `CONTRIBUTING.md`, `README.md`, `openspec/specs/`.
- **[S5]** `mise --version` (`2026.11.14 macos-arm64 (2026-11-24)`) and `brew list --versions mise` (`mise 2026.11.14`) on the engine's host, 2026-11-26 at about 06:00.
- **[S6]** ETHOS at `0.2.0-beta.11` (`e4d9d04d36a0`), as installed: `resources/.config/ci/verification.cue`, lines 14-20 (`supply.mise_version`) and 62-63 (the mise-action step).
- **[S7]** `openspec/specs/engine-verification/spec.md`, requirement "Both forges run one check from one declaration".
- **[S8]** Mise's documentation at `v2026.11.14`, `docs/configuration.md`, section "`min_version`", read on 2026-11-26.
- **[S9]** The archived Change `2026-11-25-run-ci-on-arm-macos`, task 2.1, and its evidence `research.md`, section "Task 2.1": Mise 2026.11.14 ran `mise lock` offline on 26 November 2026 and removed exactly the five `windows-x64` tables.
- **[S10]** The ETHOS session's answer for every governed repository, as the films session relayed it on 2026-11-26 at about 06:30 (not read first-hand): leave `min_version`, move only the CI pins; the owner's confirmed reading covers the pins only; the rule for the floor's form goes to ETHOS's CI paradigm (97f828, by 3 December).
- **[S11]** DDWG's repository at `dev` `4f4a228b`, read on 2026-11-26 at about 06:32: `.config/ci/verification.toml` line 7 (`mise_version = "2026.11.14"`), `.config/mise/config.toml` line 1 (`min_version = "2026.10.14"`), commit `ed7f01c7` ("build(supply): move the hosted job to Mise 2026.11.14") and the archived Change `2026-11-25-move-hosted-mise-2026-11-14`, whose design keeps raising the Mise floor as a non-goal.
