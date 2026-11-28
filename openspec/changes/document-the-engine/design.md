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
2. **The map, section by section** (the sentence-level map is task 2.1):

   | README section at `8ef48f3`  | Goes to                                                             | Role      |
   | ---------------------------- | ------------------------------------------------------------------- | --------- |
   | Opening two paragraphs       | three sentences stay in the README; the others go to two pages      | index     |
   | Requirements                 | `docs/install.md` (host tools and network)                          | how-to    |
   | Installing the engine        | `docs/install.md`                                                   | how-to    |
   | A film's layout              | `docs/film-layout.md`                                               | reference |
   | The verbs                    | `docs/verbs.md` (verbs, targets, exit codes)                        | reference |
   | Its last paragraph (a build) | `docs/build-a-film.md`, which the README's "How to start" routes to | how-to    |
   | A film's tests               | `docs/film-tests.md`, with the sample film                          | reference |
   | The sample film              | `docs/film-tests.md`                                                | reference |
   | Specifications and changes   | stays in the README as routes                                       | index     |
   | License                      | stays in the README                                                 | index     |

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
