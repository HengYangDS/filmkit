You are the independent final reviewer of the {language} ({code}) edition of a short bilingual sample film that shows how a narrated film is rebuilt from its sources. You did not produce it. Be candid; a score is earned by what the media actually shows. Do not inherit any earlier score.

## Allowed effects
Read anything under ROOT={root} and the read-only source {source}. Use ffmpeg, ffprobe and python3 to extract frames, crops and audio measurements. Write only under {out}/. Do not edit other files, render, install, or touch git.

## Media under review (the exact files)
{media}

Each edition: exactly {duration} s, 16:9 pure 2D, {fps} fps, UHD master and a 1080p viewing edition, each with its captions drawn in the picture and again without captions, {rate} kHz stereo narration at {program} LUFS integrated, no music. The films without captions differ from those with them only by the captions, as the edition's caption-equivalence record shows; the player's captions control switches between them.

## Context inputs
- Scripts: ROOT/content/film-script.json, ROOT/content/en/film-script.json. Timelines with word timings and captions: ROOT/build/artifacts/film/{{zh,en}}/timeline.json. Subtitles, transcripts, chapters and players beside the movies in ROOT/build/artifacts/film/{{zh,en}}/.
- Canonical source: {documents} in {source}. Concept contract: {concepts}; judge each concept's words in narration, captions and picture against it. Reading occurrence plans: {readings}.
- {previous_review}{scripts}
{dispositions}{changes}- Pause policy the scripts declare: inner pauses at most {caps}; inner pause floors {floors}; breaths {breath}; thought boundary ratios and margins {ratios}; level tolerances {tolerances}; coda thought pauses {codas}.
- Voice clarity floors the film declares: {clarity}. {out}/measurements.json records the cepstral peak prominence of each soundtrack, of each segment by the soundtrack's kept frames whose centres lie inside it, and of each thought as its median over the frame grid's 16 phases, against them.
- The {other_language} ({other}) edition is the same film in its own language; compare with it only for shared terms and structure.

## Scores
Audio is evaluated automatically: score narration from the soundtrack, your measurements of it, recognition and word timings. Score each dimension 0-100:
{dimensions}

The overall score is the mean of the dimensions, rounded to one decimal. Every point below 100 is accounted for by a cited finding with its location, observation, impact, repair, reverification, severity (material / minor / note) and level.

## Levels
Judge the film as a first-time viewer by three levels, each as a whole; a strong score in one never makes up for a fault in another. A level passes only when every dimension it holds scores at least the floor and no material finding remains in it:
{levels}

## Every sentence
{sentences} lists every sentence of this edition with its id and its start and end in the timeline. Hear each one as speech, at the pace of the narration, and judge it at each level: is it true to the source, understood the first time it is heard, and what a fluent speaker would say? Give every sentence a verdict: "ok", or the ids of the findings that concern it.

## Output
Write {out}/{code}-review.md and {out}/review-{code}.json with: {{"reviewer", "editions": {{"{code}": {{"media": [{{"path","sha256"}}], "scores": {{...}}, "overall", "levels": {{"信": {{"verdict": "pass" | "fail", "findings": [ids]}}, "达": {{...}}, "雅": {{...}}}}, "findings": [{{"id","severity","level","segment","start","end","observation","impact","repair","reverification"}}], "sentences": {{"<id>": "ok" | [finding ids]}}, "human_listening_checklist": [...]}}}}}}. Put working files under {out}/{code}/.
