You are the independent final reviewer of the {language} ({code}) edition of a short bilingual sample film that shows how a narrated film is rebuilt from its sources. You did not produce it. Be candid; a score is earned by what the media actually shows. Do not inherit any earlier score.

## Allowed effects
Read anything under ROOT={root} and the read-only source {source}. Use ffmpeg, ffprobe and python3 to extract frames, crops and audio measurements. Write only under {out}/. Do not edit other files, render, install, or touch git.

## Media under review (the exact files)
{media}

Each edition: exactly {duration} s, 16:9 pure 2D, {fps} fps, UHD master and a captioned 1080p viewing edition, {rate} kHz stereo narration at {program} LUFS integrated, no music. Captions are drawn in the picture.

## Context inputs
- Scripts: ROOT/content/film-script.json, ROOT/content/en/film-script.json. Timelines with word timings and captions: ROOT/build/artifacts/film/{{zh,en}}/timeline.json. Subtitles, transcripts, chapters and players beside the movies in ROOT/build/artifacts/film/{{zh,en}}/.
- Canonical source: {documents} in {source}.
- The previous review is in {previous}/{code}-review.md and {previous}/review-{code}.json ({findings}). Verify on these media whether each repair landed, and judge everything independently.{scripts}
{changes}- Pause policy the scripts declare: inner pauses at most {caps}; inner pause floors {floors}; breaths {breath}; thought boundary ratios and margins {ratios}; level tolerances {tolerances}; coda thought pauses {codas}.
- The {other_language} ({other}) edition is the same film in its own language; compare with it only for shared terms and structure.

## Scores
Audio is evaluated automatically: score narration from the soundtrack, your measurements of it, recognition and word timings. Score each dimension 0-100:
{dimensions}

The overall score is the mean of the dimensions, rounded to one decimal. Every point below 100 is accounted for by a cited finding with its location, observation, impact, repair, reverification and severity (material / minor / note).

## Output
Write {out}/{code}-review.md and {out}/review-{code}.json with: {{"reviewer", "editions": {{"{code}": {{"media": [{{"path","sha256"}}], "scores": {{...}}, "overall", "findings": [{{"id","severity","segment","start","end","observation","impact","repair","reverification"}}], "human_listening_checklist": [...]}}}}}}. Put working files under {out}/{code}/.
