## 1. Hosted supply

- [ ] 1.1 Move `[supply] mise_version` to Mise 2026.11.11 and generate the pipelines again; done
      when `ethos lane project --check --json` reports the projections conforming and only the Mise
      lines changed. The parameter moved; the check reports the projections conforming, and the
      GitHub workflow's Mise line is the only generated change.
- [ ] 1.2 Record the move under Changed in the Changelog's Unreleased section; done when the
      repository check passes. The Unreleased section names Mise 2026.11.11.

## 2. Lock compatibility

- [ ] 2.1 Check the tracked version-3 lock with Mise 2026.11.11's `mise lock --check` before
      landing; done when it passes, or its only problems are platforms the release does not build
      and are named in this task, and the lock's bytes are unchanged. Mise 2026.11.11 reports the
      lock up to date (4 tool versions, 24 platform entries) and exits 0; the lock's bytes are
      unchanged.
