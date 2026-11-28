## Context

The README at `8ef48f3` is 93 lines (65 nonblank), an opening and eight `##` sections; it is the only page of the engine's documentation besides the
Changelog and the contribution guide [S2]. ETHOS's Docs Registry [S4] governs Markdown under the documentation root an
adopter's profile declares as `[roots] docs`, `docs` where the profile declares none (`RepositoryRoots` in ETHOS's
`src/ethos/repository/profile.py`); each page declares subject, role, state and relations in plain YAML front matter;
roles are ETHOS's kernel vocabulary, which `docs/_meta/taxonomy.toml` may extend and which applies whole where no
taxonomy stands; a README stays only where it is its directory's index (`role: index`, at most 100 nonblank lines); a
directory with two or more navigable children needs one. ETHOS ships no scaffold for an adopter's root.

ETHOS composes into every repository's default and full proof sets each gate of its packaged set whose
`required_for_paths` matches an authored path, beside the gates of the repository's own gates file
(`select_gate_declaration` in `src/ethos/repository/policy/quality/gate_composition.py` at `v0.2.0-beta.11`), and
refuses a repository's declaration of such a gate that runs it differently (`common_gate_execution_conflict`). The four
documentation gates match `*.md`, so filmkit's proof already runs them: the local proof of `8ef48f3` ran each, and each
passed [S6].

## Goals / Non-Goals

Goal: the owner's two parts of G-2 for this repository: a documentation set on ETHOS's base, and a README that only
orients and routes. Non-goals: new content (the move changes no meaning, and adds
one fact on `filmkit supply`, decision 2), the films' documentation (their own lanes),
ETHOS's base itself (ETHOS's).

## Decisions

1. **A flat `docs/`.** Five pages and an index sit directly under `docs/`: two how-to pages and three references are
   too few for subfolders, and a folder with two children would need its own README (ETHOS's entrypoint rule). Pages
   are split by the reader's task, not by length.
2. **The map, sentence by sentence** (task 2.1). The README at `8ef48f3` holds 32 sentences (R1 to R32, in order),
   three tables (T1 to T3) and one code block (C1). Each goes to one place with its words unchanged, but for these: a
   link on a page starts from `docs/`; R2's subject, "It", names Film Kit on its new page, and R12's, "Its", names a
   film's `package.json` under its new heading; and R29 and R30 become routes in the README's list "Where to read",
   each naming what its target holds as the sentence did:

   | README at `8ef48f3`                                                                           | Section                    | Goes to                                                             | Role      |
   | --------------------------------------------------------------------------------------------- | -------------------------- | ------------------------------------------------------------------- | --------- |
   | R1 "Film Kit rebuilds a narrated explainer film, …"                                           | Opening                    | README, first sentence                                              | index     |
   | R2 "It narrates each script with a local speech model, …"; R3 "After one supply step …"       | Opening                    | `docs/build-a-film.md`, opening                                     | how-to    |
   | R4 "The engine carries no film's content."                                                    | Opening                    | README, second sentence                                             | index     |
   | R5 "Each film's repository holds its scripts, …"                                              | Opening                    | `docs/film-layout.md`, opening                                      | reference |
   | R6 "The DDWG introduction films are built with it."                                           | Opening                    | README, third sentence                                              | index     |
   | R7 to R10, the four host requirements                                                         | Requirements               | `docs/install.md`, "Prepare the host"                               | how-to    |
   | R11 "A film pins a release tag …" and C1                                                      | Installing the engine      | `docs/install.md`, "Pin a release"                                  | how-to    |
   | R12 "Its `package.json` declares the npm packages …"                                          | Installing the engine      | `docs/install.md`, "Declare the npm packages"                       | how-to    |
   | R13 "A film is the folder …", R14 "The engine builds the film …" and T1                       | A film's layout            | `docs/film-layout.md`                                               | reference |
   | R15 "The declaration states …", T2 and R16 "The fields and their refusals …"                  | A film's layout            | `docs/film-layout.md`, "The declaration"                            | reference |
   | R17 "Run in a film's folder.", R18 and R19 (exit 1 and exit 2) and T3                         | The verbs                  | `docs/verbs.md`                                                     | reference |
   | R20 "A target is …" and R21 "Every node's run writes its run record …"                        | The verbs                  | `docs/verbs.md`, "Targets and run records"                          | reference |
   | R22 "A film is built by …", R23 "The narration is GPU work.", R24 and R25 (the build's order) | The verbs                  | `docs/build-a-film.md`, "The steps", which "How to start" routes to | how-to    |
   | R26 "A film's tests import only `filmkit.api` …"                                              | A film's tests             | `docs/film-tests.md`                                                | reference |
   | R27 "`examples/sample-film` is a film of two editions …" and R28 "Its tasks run the verbs …"  | The sample film            | `docs/film-tests.md`, "The sample film"                             | reference |
   | R29 (the specifications and the changes) and R30 (the Changelog and CONTRIBUTING.md)          | Specifications and changes | README, "Where to read", as routes                                  | index     |
   | R31 and R32 (the license and NOTICE)                                                          | License                    | README, "License"                                                   | index     |

   The move adds one fact, at the head of "The steps" in `docs/build-a-film.md`: a build reads what `filmkit supply`
   installs and checks, the pinned browser build, dictionary and speech models, so it runs first. The README at
   `8ef48f3` named the supply only in R3 and R10, and its build order (R22) began at `filmkit check`. The fact is the
   engine's: `filmkit supply` is the one step that reaches the network (`src/filmkit/graph/cli.py`), it checks each
   supply against its pins so that the build after it reads only checked inputs and runs offline
   (`src/filmkit/supply.py`), and narration refuses, naming `filmkit supply`, where the dictionary it places is missing
   (`narration-convergence`); `filmkit supply --help` states only its usage. Every other sentence the move adds routes
   or orients and states no content: the README's routes, the index's purpose and its table of questions, the opening
   line of `docs/install.md` and the route from `docs/build-a-film.md` to `docs/verbs.md`.

3. **The README routes; `docs/README.md` indexes.** The root README names the repository, says in one sentence what
   the engine does and that it carries no film's content, routes to `docs/`, `openspec/specs/`, the Changelog and
   the contribution guide, and says how to start by three routes: install the engine as `docs/install.md` states, lay
   out and declare the film as `docs/film-layout.md` states, and build it as `docs/build-a-film.md` states. It restates
   nothing those pages hold, the index's table of questions included. The films session's reading of the owner's
   request, which the owner confirmed on 23 November at 14:29 (item G-2), names these three: what it is, where each kind
   of document lives and how to start; ETHOS's draft design of 23 November reads the owner's words the same way (its
   first section, item 2) [S5]. `docs/README.md` states the root's purpose and routes to each page with one line on the
   question it answers.
4. **The requirement moves with the content.** `engine-distribution` names the documentation as the carrier; its
   Purpose sentence changes with it at archive. Its first scenario keeps its name, "A new film follows the README",
   and its WHEN names the README's "How to start" routes to the pages on installing the engine and on a film's layout:
   OpenSpec 2.0.0 and 2.2.0 refuse a MODIFIED block that drops a current scenario's name
   (`findMissingCurrentScenarios`, its `validator.js`), and a REMOVED and ADDED pair would change the requirement's
   identity for a name (the films session's decision, 28 November). The requirement's text is 454 characters, under
   OpenSpec's limit of 500, and `openspec validate --strict` passes.
5. **ETHOS's defaults stand undeclared.** The pages sit under `docs/`, the root ETHOS reads where the profile declares
   none, so the profile does not change: ETHOS writes a profile without its defaults (`render_repository_profile`,
   `exclude_defaults=True`), and its own profile declares no root. The pages use ETHOS's kernel roles and states, and no
   `docs/_meta/taxonomy.toml` is written while filmkit adds no role: ETHOS reads the taxonomy only where it stands, and
   a copy of its vocabulary would be a second source of it. A role of filmkit's own would join there.
6. **The gates are ETHOS's composition.** `system/gates.toml` declares none of the four: ETHOS already runs them in
   filmkit's proof, and a declaration of its own would be a second copy that ETHOS refuses once it differs.
7. **The root README carries no front matter.** The registry selects only the Markdown under the documentation root
   (`build_docs_registry`), and its check of a README without children skips the repository root's
   (`_childless_readmes`); ETHOS's own root README has none. The repository's Markdown ceiling of 500 nonblank lines
   still holds it, as every tracked authored Markdown file.
8. **The formatter reads the pages.** `package.json`'s `format:markdown` and `format:markdown:check` name
   `docs/**/*.md` beside the root files, so `mise run fix` and `mise run check` format and check the pages as ETHOS's
   `markdown-lint` gate does.

## Open questions

None at `v0.2.0-beta.11`. At `v0.2.0-beta.12` the registry's code, the profile's roots and `select_gate_declaration`
are unchanged (`git diff v0.2.0-beta.11 v0.2.0-beta.12` over them, 28 November), so the rebind runs the four gates
in the same way, and its full check runs them again.

## Risks / Trade-offs

- A sentence lost in the move: answered by task 2.1's map before any deletion.
- A film's link into the README would break: none was found in the three films' tracked files on 28 November
  (`rg` for links to filmkit's README in each repository); task 2.4 searches again at the Change's base.
- The release step rewrote the pin's tag in the README: from 0.36.0 it must rewrite `docs/install.md`. The
  maintainer's release tool outside the tracked tree finds the file that holds the pin in the tree since 28 November.
- ETHOS decides later what it has only drafted (the root README's size limits, the scaffold, folder names; its draft's
  section 六, for the owner). The thin README and a flat `docs/` meet the strictest reading of each; if ETHOS decides
  otherwise, filmkit follows in a later Change.
