## Context

See [proposal.md](proposal.md). Three resolvers supply this repository: Mise (Node, Python, uv and the ETHOS release, declared in `.config/mise/config.toml` and locked in `mise.lock`), uv (the Python packages, `uv.lock`) and npm (`package-lock.json`). The archived Change `2026-11-14-declare-release-age-and-take-latest-supply` made the Mise line the age's one tracked home and left the uv and npm locks to take their cutoff from it when they are refreshed, by hand.

What was read and tried on 18 November 2026 [S2] [S3]:

- With the project's line at `72h`, `mise install --locked` into an empty data folder installs every declared tool, uv 0.13.9 among them, published 32 hours before. The age filters what Mise resolves from a listing; an exact version that the lock holds is not resolved.
- `npm ci --min-release-age=3` installs both locks this repository will hold (the present one, 128 packages, and the one the Change `draw-pictures-natively` brings, 38) though each holds `puppeteer-core` 25.18.1, published 18 hours before. A resolve of that version under the same setting is refused (`ETARGET … with a date before 11/15/2026`), from the command line and from `.npmrc` alike; a misspelt setting warns.
- Six artifacts of the uv lock are younger than 72 hours: regex 2026.11.15, numpy 2.5.5, httpcore2 and httpx2 2.16.2, mlx-audio 0.6.6 and filelock 4.2.11, the last reaching the age on 20 November 2026 at 14:35 CST. `pyproject.toml` pins each exactly, so a relock under a 72-hour cutoff before then finds no version to resolve.

## Goals / Non-Goals

**Goals:**

- Each resolver holds third-party supply to the age by its own configuration, and nothing else in the repository states the number.

**Non-Goals:**

- Moving any pin back. What the lock holds stays; the age governs the next move.
- The films' declarations, and the common form for the owner's own repositories, which are their owners'.

## Decisions

1. **Each resolver reads the age from its own configuration; no test or script holds it.**
   - **Rests on:** the owner's direction as relayed [S1]; the three resolvers above, none of which reads another's setting.
   - **Considered:** (a) the Mise line alone, as since 14 November, with the uv and npm cutoffs applied by hand at a refresh: the number then lives in a person's command; (b) one value in a file of the repository's own that a script hands to each resolver: a script would hold the wiring and every resolver's native reading would be bypassed; (c) each resolver's native setting in its own configuration file.
   - **Chosen because:** (c) is what each resolver enforces without a caller, and what the common form states. The value stands in three configuration files and in no code.
   - **Applies to:** `.config/mise/config.toml` (`minimum_release_age`), `.npmrc` (`min-release-age`), and `pyproject.toml` (`exclude-newer`) when decision 3 allows.
   - **Reopened when:** one of the resolvers reads a shared declaration, or the common form names another carrier.
   - **Sources:** [S1] [S2] [S3].
2. **No exclusion is declared here for the owner's own tools.**
   - **Rests on:** the owner's exemption as relayed [S1]; of this repository's supply only the ETHOS release is the owner's, declared for Mise's `http` backend by exact URL and checksum for each platform, with no listing to filter; it installed under the 72-hour line in the trial [S2]. No Python or npm package of the owner's is resolved here.
   - **Considered:** (a) an entry in `minimum_release_age_excludes` for the ETHOS release; (b) none.
   - **Chosen because:** (b): an entry that excludes nothing a resolver filters would be a declaration without an effect.
   - **Applies to:** `.config/mise/config.toml`.
   - **Reopened when:** this repository resolves one of the owner's tools or packages from a listing, or the common form asks for the entry.
   - **Sources:** [S1] [S2].
3. **uv's line waits for the lock to be 72 hours old, and comes with its relock in one commit.**
   - **Rests on:** the six artifacts above; uv records the cutoff in the lock, so the line and the lock move together.
   - **Considered:** (a) the line now, with pins moved back to versions that are old enough: it would undo the supply 0.23.1 released and every take a film narrates with it; (b) the line now without a relock: `uv lock --check` refuses a lock whose options differ; (c) the line and the relock once the youngest artifact is old enough.
   - **Chosen because:** (c) changes no artifact.
   - **Applies to:** a Change of its own. Owner: the engine's maintainer. Next action: on or after 20 November 2026, 14:35 CST, read the lock's upload times again, declare `exclude-newer` in `pyproject.toml`, relock, and verify that no artifact of the lock changed. Read again: 2026-11-20.
   - **Reopened when:** a pin moves before that day; the date then follows the new artifact.
   - **Sources:** [S3].

## Risks / Trade-offs

- A security repair younger than three days cannot be resolved by npm or Mise. → The owner decided that a security fix does not wait [S1]: it is taken through one declared exemption that names the advisory, in the resolver's own configuration, and the exemption is removed once the fix is installed. Nothing is resolved backwards to meet the age.
- Until 21 November 2026, 00:28 CST, a re-resolve of the npm lock is refused for `puppeteer-core` 25.18.1, which the lock already holds. → `npm ci` installs the lock; the lock that the Change `draw-pictures-natively` brings was resolved before this line and installs under it [S2].
- The number stands in three files. → Each is the configuration its resolver reads; the Changelog names all three.

## Sources

Read or measured on 18 November 2026. Paths under `build/evidence/` are the canonical checkout's local evidence.

- **[S1] The owner's decisions, as relayed:** heard first-hand by the repository steward's session on 18 November 2026 (about 17:1x CST: the age is 72 hours for the host and every governed repository, and no test or script holds the number; about 18:2x CST: the owner's own repositories and tools are exempt, through each resolver's own exclusion list) and sent to the films' session, with the ETHOS product session's common form (17:55 CST: the Mise line at any time; uv's `exclude-newer` only with a relock in the same commit once every locked artifact is 72 hours old; npm's line once `npm ci` passes under it). The ETHOS product session heard the owner first-hand at 18:33 CST (a security fix does not wait, by one declared exemption that names the advisory and is removed once the fix is installed; nothing is resolved backwards) and took into the common form that the npm line may enter at any time and that a lock's age is read from the registry's publication times. None of this was heard first-hand by this repository's maintainer.
- **[S2] The trials:** `build/evidence/hold-third-party-supply-72-hours/age-probe.log` with `age-probe.sh` and `mise-install.log` (Mise 2026.11.9; the declared tools' publication times from the forge's API); `npm-age.log` with `npm-age.sh` and each lock's `times.txt` and `npm-ci.log` (npm 11.20.0, the one Node 26.13.1 ships; the registry's publication times); `npm-control.log` with `npm-control.sh`.
- **[S3] The uv lock's upload times:** `build/evidence/hold-third-party-supply-72-hours/uv-lock-ages.txt` with `uv-lock-ages.py`, read from `uv.lock` at `b1d5ec1`.
