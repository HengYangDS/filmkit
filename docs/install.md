---
subject: filmkit:install
role: how-to
state: active
relations:
  projects: ../openspec/specs/engine-distribution/spec.md
---

# Installing the engine in a film

A film's build needs the host below, and the film pins one release of the engine.

## Prepare the host

- An Apple-silicon Mac: the speech models run on MLX.
- [Mise](https://mise.jdx.dev), which installs the film's locked Node, CPython and uv, and [Vale](https://vale.sh) at the version the engine's record states; the register check refuses any other.
- FFmpeg with libx264, ExifTool and rsync 3, from Homebrew: `brew install ffmpeg exiftool rsync`.
- Network access for `filmkit supply` alone, which installs the browser build of the checks, the pinned CMUdict and the three speech models; `HF_ENDPOINT` names a Hugging Face mirror where the hub is unreachable.

## Pin a release

A film pins a release tag in its Python project and locks it:

```toml
[project]
dependencies = ["filmkit"]

[tool.uv.sources]
filmkit = { git = "https://github.com/HengYangDS/filmkit", tag = "v0.36.0" }
```

## Declare the npm packages

A film's `package.json` declares the npm packages the engine runs, `@napi-rs/canvas`, `puppeteer-core` and `@puppeteer/browsers`, each at the version the engine's own `package.json` names under `dependencies`, the one source of those versions; `filmkit check` names a package the film holds at another version.
