# Proposal

## Why

On 2 November 2026 the owner asked that every governed repository keep its supply at the latest stable releases. filmkit's renderer moved to HyperFrames 0.9.3 in `refresh-renderer`, which landed without a tag. A currency audit the same evening found filmkit's locks eight packages behind the newest releases their declared ranges admit: anyio 4.16.0 in `uv.lock`, and @hono/node-server 2.1.6, ansi-regex 6.5.0, hono 4.13.16, nanoid 3.3.20, postcss 8.5.32, tslib 2.9.1 and ws 8.22.1 in `package-lock.json`. Every other declared package and tool is current; Python stays at 3.12.16, the newest release of the 3.12 line, by its standing decision.

The films pin filmkit by tag, and the engine refuses any renderer but its own, so `ddwg-film`, `ethos-film` and `ddwg-essentials-film` can reach HyperFrames 0.9.3 and these locks only through a release. A film that adopts it must also raise its own `hyperframes` pin, so the release is 0.4.0.

## What Changes

- Refresh `package-lock.json` with `npm update --package-lock-only` and `uv.lock` with `uv lock --upgrade`, so that each lock holds the newest release its ranges admit.
- Record the refresh under `Unreleased`, date the notes as `[0.4.0] - 2026-11-02`, open an empty `Unreleased`, and point the history links at `v0.3.0...v0.4.0` and `v0.4.0...HEAD`.
- Set `VERSION` to 0.4.0 and the README's example pin to `v0.4.0`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The engine's contract is unchanged, so `.openspec.yaml` sets `skip_specs: true`.

## Impact

`package-lock.json`, `uv.lock`, `CHANGELOG.md`, `VERSION` and `README.md`. The signed `v0.4.0` tag, its publication to both peers and the source-only Release pages follow the landed source and are not tasks of this Change. Each film moves its pin in its own repository, when it builds and accepts an edition on 0.4.0. `tasks.md` is the sole progress ledger.
