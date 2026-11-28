## Why

On 23 November 2026 the owner set a goal for the engine's documentation. filmkit had no documentation set and its README was too long; it needs a complete documentation set, on a common base that ETHOS provides beneath every repository it governs, and the documentation of each such repository follows one paradigm; the README orients and routes, a thin entry that does not accumulate content. The same day he confirmed the maintainer's reading and plan: filmkit adopts ETHOS's four documentation gates, moves the README's content into `docs/` by ETHOS's roles, cuts the README to an index and changes the requirement that binds content to the README; the three parts ETHOS lacks (a directory scaffold, the names of subdirectories, and limits on length by content rather than by lines alone) go to ETHOS's maintainers, and filmkit follows ETHOS's present role names until ETHOS decides them [S1]. On 28 November he asked for the plan again; it had not started [S1].

filmkit's README is 93 lines and carries the engine's content: its requirements, how a film installs it, a film's layout and declaration, the verbs and the sample film [S2]. The repository has no `docs/`, and the requirement "Each release SHALL state, in the repository's README, the folder layout the engine reads, the declaration's fields, the npm packages a film declares, and the host tools a build needs" binds that content to the README [S3].

ETHOS's Docs Registry states the base an adopter follows: the documentation root that the repository profile declares, `docs/` where it declares none; front matter on every page (subject, role, state, relations), with a role and a state from ETHOS's vocabulary, which a repository's `docs/_meta/taxonomy.toml` may extend; a README under that root kept only as an index (`role: index`, its directory's purpose and scope, routes to its children, at most 100 nonblank lines); and decision records in one form [S4]. ETHOS already runs its four documentation gates (`docs-registry`, `markdown-links`, `markdown-lint`, `prose`) in filmkit's proof beside filmkit's own gates; on `8ef48f3` all four passed, and the registry read no page, since `docs/` does not exist [S6].

## What Changes

- **The README becomes the thin entry.** It says what filmkit is and that it carries no film's content, where each kind of document lives (the documentation, the specifications, the Changelog, the contribution guide), how to start (routes to the pages on installing the engine in a film, a film's layout and building a film), and the license. Nothing else stays in it.
- **`docs/` holds the content, moved by reader task.** A page for installing the engine in a film with its host tools (how-to), one for a film's layout and declaration (reference), one for the verbs and targets (reference), one for building a film (how-to), and one for a film's tests and the sample film (reference); `docs/README.md` is the index. Each sentence of the old README is mapped to the page that takes it before it leaves the README; meaning is not changed in the move. The page on building a film adds one fact the old README left out: `filmkit supply` runs first, since a build reads what it installs.
- **The base is ETHOS's, as published.** The pages sit under `docs/`, the root ETHOS reads when the profile declares none, and use ETHOS's roles and states, to which filmkit adds none; every page carries ETHOS's front matter; ETHOS's four documentation gates, already in filmkit's proof, check the pages. Where ETHOS's base is still a draft (its design of 23 November: the root README's size limits, a scaffold, folder names), filmkit takes the strictest reading now and follows ETHOS when it decides [S5].
- **The requirement changes its carrier.** `engine-distribution` states that a release documents the layout, the fields, the npm packages and the host tools in the documentation the README routes to.
- The Changelog records the change under `Changed`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `engine-distribution`: the requirement that names the README as the carrier of a film's contract names the documentation instead; its scenario follows.

## Impact

- **Text:** `README.md`, new `docs/` (index and five pages), `CHANGELOG.md`, and the route for a film's maintainer in `CONTRIBUTING.md`.
- **Configuration:** `package.json`, whose Markdown formatter scripts name the pages. `.ethos/profile.toml` and `system/gates.toml` do not change.
- **Specification:** `openspec/specs/engine-distribution/spec.md` through this Change's delta.
- **Unchanged:** every file below `src/`, `tests/` and `examples/`; no film's output bytes.
- **Films:** none in this release. `ddwg-film` adopts the same form in its next release lane and `ethos-film` in its December lane; `ddwg-essentials-film` retires after the fused film's release and adopts none.
- **Release:** a minor release, 0.36.0, after the ETHOS 0.2.0-beta.12 rebind.

Owner: the engine's maintainer. Sources: [S1] `build/evidence/owner-words.md`, item G-2; [S2] `README.md` at `8ef48f3`; [S3] `openspec/specs/engine-distribution/spec.md` line 25; [S4] ETHOS `docs/governance/docs-registry.md`, `src/ethos/repository/profile.py` and `src/ethos/repository/registry/docs/` at `v0.2.0-beta.11`, the release filmkit bound when this Change was written, and the same in these parts at `v0.2.0-beta.12`; [S5] ETHOS's draft `build/runtime/work/beta-13/drafts/docs-base-design-20261123.md` (its third draft, 23 November), sections 三, 五 and 六; [S6] the local proof of `8ef48f3` (26 November 2026), ETHOS artifact `ef70e6fc2b4da66612d0bb219278ee7ecf0f305864724841fdc389f671e63dd3` in filmkit's Git common directory, read on 28 November, and ETHOS's `src/ethos/repository/policy/quality/gate_composition.py` at `v0.2.0-beta.11`.
