# Contributing

This guide is for maintainers who change, verify or release filmkit. A film that uses the engine needs only the [README](README.md); Agents start at the [Agent entry](AGENTS.md).

| Your task                 | Read next                               |
| ------------------------- | --------------------------------------- |
| Prepare a checkout        | [Prepare the tools](#prepare-the-tools) |
| Change the engine         | [Change the engine](#change-the-engine) |
| Check a change            | [Verify a change](#verify-a-change)     |
| Record a change           | [Commit](#commit)                       |
| Cut and publish a release | [Release](#release)                     |

## What the engine owns

filmkit carries no film's content. A film's scripts, casts, pages, review policy and picture composition stay in the film's own repository, and the engine reads them from the film it builds. An engine change keeps every existing film's output bytes unless its release says otherwise, and a film adopts a release only after it rebuilds and compares the result under its own reproduction standard. The tests load only the sample film in [`examples/sample-film`](examples/sample-film), whose text is written for them.

## Prepare the tools

The engine builds films on an Apple-silicon Mac. [Mise](https://mise.jdx.dev) installs the locked Node, CPython, uv and ETHOS that the [project configuration](.config/mise/config.toml) and its [lock](.config/mise/mise.lock) declare, and Homebrew supplies FFmpeg with VideoToolbox, ExifTool and rsync 3:

```sh
brew install ffmpeg exiftool rsync
mise run bootstrap
```

`bootstrap` prepares the frozen Python environment and the locked npm packages. Run ETHOS through `mise exec --locked --` or with Mise activated in your shell, so that the declared release answers rather than another installation.

## Change the engine

Every change is an OpenSpec Change, worked in its own ETHOS Work Lane:

1. Run `ethos status --json` in the canonical checkout and follow the next action it reports.
2. Start a Work Lane with `ethos lane start`, then create the Change in it with OpenSpec. Its `proposal.md` says why and what changes, `design.md` how, and `tasks.md` lists the work in order; `tasks.md` is the only progress record.
3. Before you edit a tracked file, obtain `ethos lane prewrite` admission for its exact path.
4. Show a defect or a new behaviour with a test that fails first, then change the code. Generated output belongs under the ignored `build/`; the tracked tree holds sources only.
5. When the tasks are done, archive the Change, prove the archived head once, then land it and close out as `ethos status` directs.

## Verify a change

```sh
mise run check
```

The check confirms that the locks are current, runs the Node and Python suites and checks the Markdown format without writing; `mise run fix` applies the Markdown formatter. A committed head must then pass the full proof, which runs every gate the repository declares in [`system/gates.toml`](system/gates.toml):

```sh
ethos prove --host --execute --full --json
```

GitHub Actions and GitLab CI run the same portable proof. Building the sample film is a local acceptance, because it needs the speech models and the browser build:

```sh
mise run sample:supply
mise run sample:build
```

A change to narration, sound or picture rebuilds the sample film and compares it with its previous output. Packaging refuses to extend films bound to other inputs, so first delete each edition's four films and its `film-package.json`, as the README describes.

## Commit

Sign every commit with your own SSH key; ETHOS's hooks check each commit's signature, subject and admission. Set `ETHOS_ACTOR` to the Lease holder and `ETHOS_CHANGE` to the Change's name when you commit. The subject is a Conventional Commit whose type is `build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`, `refactor`, `revert` or `test`, with an optional kebab-case scope and `!` for a breaking change, as in `fix(soundtrack): name every abrupt thought`.

## Release

filmkit follows Semantic Versioning; until 1.0.0 the declaration format may change in a minor release. `VERSION` holds the version, and `CHANGELOG.md` follows Keep a Changelog: record each change under `Unreleased` as it lands, and date its heading only when the release is cut. A release is a signed `v*` tag that `ethos land --release` cuts from the accepted head. `ethos publish` then sends the branches and the tag to the peers that [`.ethos/release.toml`](.ethos/release.toml) declares, GitHub and GitLab, and each gets a source-only Release page. A film moves its pin to the new tag in its own repository, after it rebuilds and compares under its reproduction standard.

## License

Contributions are licensed under the repository's [MIT License](LICENSE). [NOTICE](NOTICE) names the sample film's recordings and fonts, which keep their own licenses.
