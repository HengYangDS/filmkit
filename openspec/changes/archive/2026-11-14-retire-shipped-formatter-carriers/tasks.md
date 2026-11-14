## 1. Carriers

- [x] 1.1 Remove `.config/checks/prettier/prettier.toml`, `.config/checks/ruff/ruff.toml` and
      `.config/checks/taplo/taplo.toml`; done when `ethos lane format --check --json`, the
      `config-quality` gate and `mise run check` pass without them. Each setting of the three
      carriers is in the shipped policy with the same value; without them the format check, the
      `config-quality` gate and the projection check pass, and `mise run check` passes with 1,102
      Python tests.
- [x] 1.2 Record the removal in the Changelog; done when the `markdown-lint`, `prose` and
      `docs-registry` gates pass. The Unreleased section records the removal under Removed; the
      `markdown-lint`, `prose`, `openspec` and `docs-registry` gates pass.
