# Tasks

## 1. Author

- [x] 1.1 Drop the QuickTime Artist key from `quicktime_keys` in `delivery/packaging.py`. Done when `tests/delivery/test_packaging.py`, red before the change, expects the ExifTool command without `-Keys:Artist`, and a two-second film packaged that way lists its author once under `mdimport -t -d2`. The command test failed on 0.16.0's keys and passes; a two-second film with the Author key and the item-list artist tags lists Yang HENG once, and with Artist as well twice.
- [x] 1.2 Refuse a QuickTime key outside the release's keys and the creation date in `check_delivered_film` and `verify_media`. Done when the packaging and verifier media tests, red before the change, refuse a film that carries the Artist key and still pass one that carries the creation date. Both tests failed before the change on a film carrying Artist and pass; a film carrying its creation date passes both.

## 2. 1080p films

- [x] 2.1 Scale the 1080p rendition by a 2×2 area average between VideoToolbox decode and encode in `production.py`. Done when the packaging command test, red before the change, expects `-hwaccel videotoolbox` and `scale=w=1920:h=1080:flags=area`, and an encode of 8 s of the ETHOS film's Chinese UHD film measures no ground pixel near ink more than 8 levels darker than the ground and its brightest ink within 4 levels of the averaged master. The command test failed on 0.16.0's rendition and passes. On the frame at 489.5 s the encode has no such pixel (0.00 %, against 12.31 % for the delivered 1080p film) and its brightest ink stands at 243, against 242 for the averaged master and 255 for the delivered film.
- [x] 2.2 Report each video packet's keyframe in `media.video_cadence`, declare the rendition's `keyframe_seconds`, pass it to the encoder and refuse other keyframes in `check_delivered_film` and `verify_media`. Done when `tests/test_media.py` reads keyframes 0 and 120 of a 240-frame film encoded with `-g 120`, and the packaging and verifier tests, red before the change, refuse a 1080p film keyed every 12 frames and pass one keyed every 120. The cadence test failed without the keyframes and passes, and the four keyframe tests pass, the two at 12 frames having failed before; an 8-second encode with this rendition keys frames 0, 120, 240 and 360 only, where the delivered film keyed every 12th.

## 3. Integration

- [x] 3.1 Describe the author, the downscale and the keyframes in `README.md` and the Changelog. Done when `npm run format:markdown:check` passes. The Markdown check passes.
- [x] 3.2 Run the repository's checks on the change. Done when `npm test`, `npm run format:markdown:check`, the Python suite, the gate-exact Ruff check and `openspec validate clean-delivered-films --strict` pass. On 0.17.0's dev, 165 Node tests, the Markdown check and 970 Python tests pass; the gate's Ruff 0.17.3 (E, F, B, I, UP, line length 100) passes on the eight changed Python files, each at most 477 effective lines; the change validates strictly.

## Workflow follow-up

- The chair sets the version, proves the archived head, lands and releases the change.
- Each film adopts the release by packaging its editions again, then has them reviewed and delivers them.
