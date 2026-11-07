# Tasks

## 1. Player switches keep the picture

- [ ] 1.1 Move the page's script into `delivery/player-page.js`, which `player.py` inlines. Done when each edition's rendered page is byte for byte the page before the move.
- [ ] 1.2 Hand over to a hidden second video that shows only once it holds its frame, in `player-page.js` and the page's style. Done when `tests/delivery/player-page.test.mjs`, red on the reloading script, passes: no switch paints the cover or a flat frame, a paused switch keeps the time, a playing film plays on to the hand-over, and a second switch, a seek during a switch and a failing film end on the right film.
- [ ] 1.3 Watch each switch's frames and times in the readback, in `player-frames.mjs`, `player-read.mjs`, `player-verdict.mjs` and `player-check.mjs`. Done when `tests/delivery/player-frames.test.mjs` and `tests/delivery/player-read.test.mjs`, red before the change, fail a switch that paints the cover or a flat frame, moves a paused film's time by 0.02 s or starts a playing film over, and pass the others.
- [ ] 1.4 Read back one delivery in Chrome Headless Shell 152, from disk and over the media server, with the 0.13.0 pages and with this engine's. Done when the readback fails the 0.13.0 pages, naming the cover frames, and passes the new ones (`build/evidence/keep-frames-across-switches/player-readback.json`).
- [ ] 1.5 Describe the hand-over and the watched switches in `README.md` and the Changelog. Done when `npm run format:markdown:check` passes.

## 2. Player typography

- [ ] 2.1 Set a Chinese size after a closing full-width bracket without a space and the English unplayable message's apostrophe as a right single quotation mark, in `player.py`, and accept such a size in the readback. Done when `tests/delivery/test_player.py` reads 讲稿（Markdown，供下载）· 9 KB and system’s, and `tests/delivery/player-read.test.mjs` passes that label.

## 3. Caption terms

- [ ] 3.1 Compare declared caption terms with the captions' words in lowercase in `captions/english.py`, and say so in `README.md` and the Changelog. Done when `tests/captions/test_phrasing.py`, red before the change, keeps a term declared with capitals on one line, and `tests/test_concepts.py` still names terms as declared.

## 4. Arcs that may vanish

- [ ] 4.1 Record in the headless stand-in each stroked clockwise `arc()` through a whole turn from a start that is not a whole number of turns, with the line that drew it. Done when `tests/picture/headless-composition.test.mjs`, red before the change, finds such an arc with its line and none for an ellipse from 0, `arc(0, 2π)` or an anticlockwise arc.
- [ ] 4.2 Report them in the frame audit as `vanishing_arcs` and gate them in `check-picture` with the remedy, and document the finding in `README.md` and the Changelog. Done when `tests/picture/frame-audit.test.mjs` and `tests/picture/test_gates.py` refuse such an arc, naming its scene, times, start, line and the ellipse form, and the sample film's audit reports none.
- [ ] 4.3 Record the browser measurement behind the rule and scan each film's current composition for such arcs. Done when `build/evidence/keep-frames-across-switches/arcs.json` holds the measured empty draws and `film-arcs.json` the arcs, or none, of ddwg-film, ethos-film and ddwg-essentials-film.

## 5. Integration

- [ ] 5.1 Run the repository's checks on the change. Done when `npm test`, `npm run format:markdown:check`, the Python suite, the gate-exact Ruff and ESLint checks and `openspec validate keep-frames-across-switches --strict` pass.

## Workflow follow-up

- The chair sets the version, proves the archived head, lands and releases the change.
- Each film adopts the release by packaging its metadata again and reading its delivery back in its own lane.
