# Proposal

## Why

The owner found the delivered films' author shown as "Yang HENG (2)". Packaging writes the author into two QuickTime keys, Author and Artist, and Spotlight's importer adds every author-bearing QuickTime key to a file's authors, so each film lists its author twice; the item-list artist tags it also writes do not count. The production reviews of the ETHOS film found the 1080p films ring (EN-R12-03, EN-R13-03, zh-R13-15): the VideoToolbox scaler lays a dark fringe along every stroke, 12 to 20 % of the ground pixels near ink more than 8 levels darker than the ground, where the UHD master averaged over 2×2 blocks has none, and lifts the brightest ink to 255 where the master reaches 242. Their encoder also keeps FFmpeg's default group of 12 pictures, a keyframe every 0.2 s.

## What Changes

- **The author once.** A delivered film carries its author in the QuickTime Author key and in the item-list artist and album-artist tags, and no longer in the QuickTime Artist key. Packaging and the verifier refuse a film with a QuickTime key outside its release's keys and its creation date, so a second author key cannot return unnoticed.
- **A 1080p picture that does not ring.** The 1080p films are decoded through VideoToolbox, scaled by averaging each 2×2 block of the UHD picture and encoded through VideoToolbox at 10 Mb/s as before.
- **A keyframe every 2 s.** The 1080p films hold a keyframe at every 120th frame from the first, and packaging and the verifier refuse a 1080p film whose keyframes fall elsewhere.
- **Output bytes.** Every delivered film's QuickTime keys change, and the 1080p films' pictures. The UHD films copy their pictures' streams as before; the soundtracks, captions, subtitles, chapters, covers and players do not change. **BREAKING**: the verifier refuses the films a film packaged with an earlier release until it packages them again.
- **Out of scope.** The UHD films' keyframe interval: HyperFrames 0.9.9 applies `--keyframe-interval` only to its software encoder, and the films render through its VideoToolbox encoder, which keeps the default of 12; the master's picture stream stays as the renderer writes it.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `film-package`: a delivered film names its author once, and the 1080p films average the master's 2×2 blocks and hold a keyframe every 2 s.

## Impact

- **Code.** `production.py`, `media.py`, `delivery/packaging.py` and `delivery/verification.py`.
- **Films.** A film adopts the release by packaging its editions again from the pictures and soundtracks it has; its review and delivery follow, since the films' bytes change.
