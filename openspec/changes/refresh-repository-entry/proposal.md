# Proposal

## Why

Three facts about the repository's entry points changed on 2026-11-01. The owner moved the GitLab project into the Tools / Films group, so the release declaration names a GitLab peer that now answers only through a redirect. The repository of the DDWG introduction films was renamed `data-department-work-guidelines-film` on both forges, so the README and NOTICE link to its old name. And the repository has no contributing guide, although it is published on two forges and the owner expects one in every governed repository.

## What Changes

- `.ethos/release.toml` names the GitLab peer at its new address, `http://192.168.64.101:18086/dig/misc/tools/films/filmkit`.
- The README and NOTICE link to `https://github.com/HengYangDS/data-department-work-guidelines-film`.
- `CONTRIBUTING.md` explains how to prepare the tools, change the engine in an ETHOS Work Lane, verify a change, commit, and cut and publish a release. The README's development section points to it, and the Changelog records it under Unreleased.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. No engine behaviour or film output changes, so `.openspec.yaml` sets `skip_specs: true`.

## Impact

- `.ethos/release.toml`, `README.md`, `NOTICE`, `CONTRIBUTING.md`, `CHANGELOG.md`, and `package.json`, whose Markdown formatter commands gain the guide.
- Out of scope: released Changelog entries and the sample film's content and source manifest, which record the name the DDWG film repository had at their commit; GitHub redirects that name.
- The local `gitlab` remote already points at the new address. The change lands on the local `dev`; publication waits for the user's approval of the next release.
