# Design

## Context

See proposal.md for why. Packaging (`delivery/packaging.py`) writes each film in three steps: FFmpeg muxes the picture, the soundtrack and the chapters with the item-list release tags (`release_tags`), among them `artist` and `album_artist`; a second FFmpeg pass attaches the cover; ExifTool then writes the QuickTime keys of `quicktime_keys`, Author and Artist among them, with the creation date. `check_delivered_film` refuses a finished film whose expected tags differ, and the verifier's `verify_media` checks the delivered films the same way; neither looks at a tag it does not expect.

Spotlight's MPEG-4 importer adds the QuickTime Author and Artist keys alike to `kMDItemAuthors` and reads neither item-list tag for it: a two-second film carrying Author and the item-list artist tags lists "Yang HENG" once under `mdimport -t -d2`, and the same film with Artist as well lists it twice, which Finder shows as "Yang HENG (2)".

The 1080p rendition (`production.VIEWING`) decodes the UHD picture into VideoToolbox frames, scales them with `scale_vt` and encodes with `h264_videotoolbox` at 10 Mb/s. On the ETHOS film's Chinese frame at 489.5 s, 12.31 % of the ground pixels within 3 px of ink (luma above 120) are more than 8 levels darker than the ground and the brightest 0.5 % of ink reaches 255; the same frame averaged over 2×2 blocks has none darker and its ink reaches 242. The encoder takes FFmpeg's default group of pictures, 12 frames.

## Goals / Non-Goals

**Goals:**

- Every delivered film lists its author once in Spotlight and Finder.
- The 1080p films show the master's strokes without a fringe or lifted whites, and seek on a declared interval.

**Non-Goals:**

- The UHD films' keyframes, which the renderer writes.
- The 1080p bit rate, the encoders and the release tags' content.

## Decisions

### Author in the QuickTime Author key and the item-list artist tags

`quicktime_keys` drops Artist. Author is the key that names who made the work; the item-list `artist` and `album_artist` tags stay among the release tags the verifier checks, and Spotlight does not count them. Alternatives considered: dropping Author and keeping Artist lists the author once as well, but names the maker as a performer and leaves the verifier's QuickTime author check without its key.

### No QuickTime key outside the release

`check_delivered_film` and `verify_media` refuse a film that carries a QuickTime key (`com.apple.quicktime.*`) outside `delivered_tags` and the creation date. A film packaged by an earlier release still carries Artist, so the verifier refuses it until the film is packaged again; that is the point, since its delivered bytes are the ones the owner found wrong.

### A 2×2 area average in software between VideoToolbox decode and encode

The 1080p rendition decodes with `-hwaccel videotoolbox` into system memory, scales with FFmpeg's `scale=w=1920:h=1080:flags=area` and encodes with `h264_videotoolbox` as before. The UHD picture is exactly twice 1080p in each direction, so the area filter averages each 2×2 block of luma and chroma, which can neither overshoot nor ring. On the frame above the encoded result has no darker pixel near ink and its brightest ink reaches 243, within 4 levels of the averaged master; an 8-second encode of the Chinese film ran at about 160 frames per second, within the rendition's encoding deadline of twice the film's length.

Alternatives considered: `scale_vt` has no filter choice; a software Lanczos or bicubic scale rings like it; software decoding as well would cost more CPU for the same picture.

### A keyframe every 2 s, declared by the rendition

A rendition declares `keyframe_seconds`, 2 for the 1080p films, and packaging passes `-g:v:0` with that many seconds of frames to the encoder. `media.video_cadence` reports the frames its packets mark as keyframes, and packaging and the verifier refuse a rendition that declares an interval when its keyframes are not exactly every interval from frame 0. `h264_videotoolbox` with `-g 120` keys an 8-second encode at frames 0, 120, 240 and 360 and nowhere else. Two seconds is the interval common to streaming and still lets a player seek quickly; the UHD rendition declares none.

## Risks / Trade-offs

- [VideoToolbox could insert a keyframe of its own] → The check refuses such a film at packaging, naming the delivery contract, before it is linked into place.
- [Software scaling uses CPU during packaging] → The 2×2 average is one of FFmpeg's cheapest filters, and packaging runs once per edition.
- [The verifier refuses films packaged by earlier releases] → Each film packages again on adoption, without new narration or picture.

## Migration Plan

Release as a minor version. Each film adopts it by packaging its editions again, has the new films reviewed and delivers them. Rollback pins the previous release, whose films keep the second author key and the ringing downscale.

## Open Questions

None.
