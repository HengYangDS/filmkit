## 1. Hosted supply

- [x] 1.1 Move `[supply] mise_version` to Mise 2026.11.10 and generate the pipelines again; done
      when `ethos lane project --check --json` reports the projections conforming and only the Mise
      lines changed. `[supply] mise_version` names 2026.11.10; the applied preview changed only the
      GitHub workflow's `version: 2026.11.10` line (the GitLab pipeline uses the guests' Mise), and
      the check reports both projections conforming.
- [x] 1.2 Record the move under Changed in the Changelog's Unreleased section; done when the
      repository check passes. The Unreleased bullet names Mise 2026.11.10; the format check and the
      documentation gates pass.

## 2. Lock compatibility

- [x] 2.1 Check the tracked version-3 lock with Mise 2026.11.10's `mise lock --check` before
      landing; done when it passes, or its only problems are platforms the release does not build
      and are named in this task, and the lock's bytes are unchanged. The official macOS archive of
      Mise 2026.11.10 (digest equal to `SHASUMS256.txt`) reports the lock up to date (4 tool
      versions, 24 platform entries) and exits 0; the lock's bytes are unchanged.
