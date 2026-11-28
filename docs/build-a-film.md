---
subject: filmkit:build-a-film
role: how-to
state: active
relations:
  projects:
    - ../openspec/specs/film-engine/spec.md
    - ../openspec/specs/build-time/spec.md
---

# Building a film

Film Kit narrates each script with a local speech model, assembles one soundtrack per edition, times the captions, draws the picture on a native canvas with and without its captions, packages a UHD master and a 1080p viewing film with FFmpeg, and verifies every film against the inputs it binds. After one supply step the build is offline.

## The steps

A build reads what `filmkit supply` installs and checks, the pinned browser build, dictionary and speech models, so it runs first. A film is built by `filmkit check`, `filmkit narrate --edition all`, then `filmkit build all`. The narration is GPU work. `filmkit build all` first names the light build to run outside any host ticket, then each heavy invocation to run as the child of its own ticket; heavy nodes share one invocation once measured within 30 minutes. `filmkit verify --technical-only` then verifies the delivered films.

[The verbs](verbs.md) states what each verb does and what a target is.
