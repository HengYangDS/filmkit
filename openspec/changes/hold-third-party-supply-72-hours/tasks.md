## 1. The declarations

- [ ] 1.1 Declare `minimum_release_age = "72h"` in `.config/mise/config.toml`; verify that `mise install --locked` into an empty data folder installs every declared tool under it.
- [ ] 1.2 Declare `min-release-age=3` in `.npmrc`; verify that `npm ci` installs the lock under it and that a resolve of a version younger than three days is refused.
- [ ] 1.3 State the three resolvers' lines, and that uv's waits for its lock, in the Changelog; verify the repository's Markdown check and `mise run check:dependencies` on the lane.
