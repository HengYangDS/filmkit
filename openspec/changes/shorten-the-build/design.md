## Context

The engine builds each edition from narration to verified films in one sequence of commands, none of which records how long it took except the render. The films' session assembled the cost of one build of the 25-minute film from logs and file times on 17 November 2026 (18 cores, engine 0.22.3): narration of both editions 37 to 50 min, four UHD renders 61 min (844 to 951 s each), two comparisons 30 min, packaging 22 min, verification 8 min, with the audits and the sound stage about 2 h 55 min. The proposal states the owner's request and the scope.

Two measurements and one review stand behind the decisions, all of 17 November 2026 and all kept in the films' production kit (`fk/r35/`), outside this repository:

- **bench1** (`bench1/result.txt`, one host ticket, 02:03 to 02:25 CST): a 120 s span, 7,200 UHD frames, of a film's captioned and uncaptioned stages, software rasterizer, screenshot capture.
- **The static review** (`static-review.md`): every heavy command's processes, decodes and loops read from the source at `e70a437`, with phase splits taken from the file times of the 16 November build.
- **bench2** (`bench2/bench2.sh`) was queued and had not run when this was written: two renders at once, the 1080p film by x264 against today's, one decode feeding three encodes. What waits for it is marked below and in the tasks.

A fourth, small measurement of this Change is cited where it is used: a synthetic clip derived at niceness 15 (`fk/r36/evidence/ground-ripple.txt`).

## Goals / Non-Goals

**Goals:**

- A build's time is read from records, stage by stage, with one command.
- The 25-minute film rebuilds in 90 minutes of compute or less. This Change removes one of an edition's two renders and its every-frame comparison, shortens the render that stays, and takes the 1080p encodes off the hardware encoder; each saving is to be measured on a film's build with the durations command before the budget is called met.
- A film's task list does not change, and a film that needs the native pair can still have it.

**Non-Goals:**

- A one-scene change in 20 minutes: it needs span renders and a segment cache, a later slice.
- Any change to what a frame shows. The captioned picture is rendered as before; only the worker count of its render changes, which changes no frame.
- New review thresholds.

## Decisions

Each decision states what it rests on, what was considered, why the option taken was chosen, and where it applies.

1. **Durations are recorded beside the evidence, never inside a record that another record binds.**
   - **Rests on:** the static review, whose phase splits had to be read from file times ("the sampled pass 219 and 196 s, the every-frame scan 675 and 678 s"), and on how the engine binds records: a stage record binds the assembly record by SHA-256, the film package binds the comparison record, and the readiness receipt binds every record it judged. A duration differs from run to run.
   - **Considered:** (a) the seconds inside each command's own record, as first proposed; (b) one ledger file for a build; (c) one small duration record for each command and edition, beside the edition's evidence.
   - **Chosen because:** (c). With (a), running `check-picture` or `compare-pictures` again on unchanged inputs would change the bytes of a record that a receipt or a package binds, and a harmless repeat would make the next step stale. With (b), two commands of one edition that end together would write one file. Each record of (c) has one writer and binds nothing.
   - **Applies to:** every action of `filmkit.produce` and `narrate`. The render receipt keeps its `elapsed_seconds`. A phase is named by the owner of the work: the comparison's validation, composition report, sampled frames and every-frame scan; each film of a package; each audit of `check-picture`; each step of `narrate`. The verifier's contract is that it writes nothing, so it states each film's seconds in the report it prints, and the reproduction in the report it writes, which no record binds.
2. **The render's worker count comes from the host.**
   - **Rests on:** bench1. Eight workers took 184.2 s cold and 141.2 s warm, 12 took 127.5 s, 16 took 114.1 s, the renderer's `auto` 124.8 s, and every picture was identical to the 8-worker picture frame for frame (PSNR infinite). About eight cores were busy whatever the count (CPU seconds over wall seconds 7.7 to 8.1).
   - **Considered:** keeping 8; the renderer's `auto`; a value in the film's declaration; a value from the host.
   - **Chosen because:** the count is a property of the host, not of the film, and it changes no frame, so a declaration would only copy a host's number into every film. `auto` was slower than 16 on the one host measured. The rule, the logical cores less two, never under 8 nor over 16, gives 16 on the 18-core host and today's 8 on a host of ten cores or fewer; `FILMKIT_RENDER_WORKERS` overrides it for a measurement.
   - **Applies to:** the pictures and the draft. One host is measured; the range between 8 and 16 on other hosts is an interpolation, which is why the receipt records the count.
3. **The renderer's determinism is proven once for each supply, in the sample build.**
   - **Rests on:** what the per-build comparison guards against. Its every-frame scan was added for the one-frame faults of 10 to 12 November, which were traced to GPU rasterization; since 0.20.0 the films draw in the software rasterizer. bench1's six renders of one stage, at four worker counts and two capture paths, were identical frame for frame.
   - **Considered:** keeping two native renders and the every-frame comparison in every film build (30 of 61 render minutes and all 30 comparison minutes for the 25-minute film); dropping the proof; proving it where the renderer, the browser and the capture are pinned, at the engine's release.
   - **Chosen because:** the fault the comparison guards against belongs to the renderer supply, which only an engine release changes, and the sample build runs for every release. There it renders one stage twice and requires every decoded frame identical (`qualify-renderer`), and compares a natively rendered pair at every frame.
   - **Applies to:** films that draw in the software rasterizer. A film that declares another capture, or an owner who wants the proof for an edition, runs `render-picture --uncaptioned --native` and `compare-pictures`, which then compares at every frame as before.
4. **The uncaptioned picture is the captioned picture with its band painted.**
   - **Rests on:** bench1: derived by one x264 encode (veryfast, CRF 14) in 17.8 s against 141.2 s for the native render of the span, 10.1 MB against 18.9 MB; the band identical to the native uncaptioned render's in all 7,200 frames; above the band 59.0 dB on average and 52.1 dB at the lowest frame from the native render, where the two native renders stand 64.8 and 56.1 dB apart and the engine's floor for a compared frame is 45 dB. VideoToolbox derived the same picture in 97.5 s.
   - **Considered:** (a) the native second render; (b) the renderer's `--variables` batch, which still renders every frame twice; (c) a lossless intermediate from which both pictures are encoded, which changes the captioned picture's path too; (d) painting the band of the captioned picture and encoding once.
   - **Chosen because:** (d) is the only one that removes the second render, and it leaves the captioned picture, the one every review reads, untouched. The paint is the ground as the captioned picture itself encodes it, read from one of its frames in YUV and laid over the band's rows without a colour conversion; bench1 painted by RGB colour, which matched that film's ground and need not match another's. The time of this form of the paint is to be measured in the sample build.
   - **Applies to:** a film whose captions stand on a flat ground that nothing else draws on, which decision 5 proves for each derivation. The derived picture is a second encode of the frames above the band; a film that wants its uncaptioned master as a first encode asks for `--native`.
5. **A derivation proves that the band holds only captions on the ground, in the work it does anyway.**
   - **Rests on:** what the every-frame comparison proved for a native pair, that the pictures differ by the captions alone. For a derived picture the frames above the band are the captioned picture's by construction, so what remains to prove is about the band: that the composition paints nothing but captions there, and that what the paint replaces is the ground.
   - **Considered:** (a) decoding both pictures again after the encode, which is the comparison this Change removes; (b) the composition's report at every half second alone, which a mark shown for a third of a second passes; (c) a headless pass at every thirtieth of a second, the frame audit's own step, with a measure of the captioned band taken in the encode's decode.
   - **Chosen because:** (c) costs no decode. The headless pass refuses a caption paint that leaves the painted rows and any other paint that reaches them, and lists the stretches without a caption. The encode's filter graph measures the captioned band's lowest and highest sample of each plane at every frame, and the derivation refuses unless every frame of those stretches, less two audit steps at each end, stands within 3 levels of the ground. A caption or a mark departs by tens to hundreds of levels; the encoder's ripple in a flat band reached 2 levels below busy synthetic content and none on bench1's film span. Run read-only on the three films' six current editions at niceness 15, the headless pass took 7 to 21 s and passed each, and listed 18.8 to 127.4 s without a caption in 9 to 160 stretches (`fk/r36/films.log`).
   - **Applies to:** every derivation. Not seen by it: a rectangle the composition fills with `fillRect` under a caption, which the headless stand-in does not report; the derived picture paints over it. No film draws one.
6. **A derived pair is compared by its record.**
   - **Rests on:** decision 5: the proofs are made when the picture is derived and recorded in its receipt.
   - **Considered:** a separate command for the derived pair; leaving `compare-pictures` out of a derived build.
   - **Chosen because:** packaging and the verifier ask for one comparison record of every edition, and a film's task list should not depend on how its uncaptioned picture was made. `compare-pictures` runs the composition report as for any pair, requires the derivation's receipt to bind the current captioned picture, composition, timeline and engine with both proofs passed and the same band, and writes the same record with the pair marked derived.
   - **Applies to:** a pair whose uncaptioned receipt says derived. A natively rendered pair is compared at every frame, and `repair-pictures` serves that pair alone.
7. **The 1080p films are encoded by x264 on a forced keyframe grid.** This replaces the draft's decision 16 (encode again after a keyframe refusal).
   - **Rests on:** six refusals of a 1080p film on its keyframes since 13 November, at host loads from 8 to 120, with no cause found. The sixth, on 17 November at 03:34, held the grid to 102.0 s, then set keyframes at 102.85, 104.85, 105.517 and 105.967 s and every 2 s from there, 251 of 303 off the grid; another heavy step of the same session started on the host in that minute, which is one timed coincidence and not a cause, and the refusal of 16 November has none beside it. Each refusal ended a film's build, cost a host ticket's wait and needed a restart by hand: the hardware encoder's cadence is not guaranteed under this host's load. bench1: VideoToolbox is the slower encoder at UHD (74 frames a second) and x264 the faster. x264 places a keyframe exactly every `-g` frames when `-keyint_min` equals it and scene-cut detection is off.
   - **Considered:** a retry by the packager, which keeps a refusal whose cause is unknown; a VideoToolbox option that pins the cadence, of which none is documented.
   - **Chosen because:** a software encoder's keyframes depend on its options alone. The settings are named constants: preset `veryfast`, constant rate factor 16, `-g 120 -keyint_min 120 -sc_threshold 0`, the area scale as before. The rate factor, the film's size and the encode's time against today's are bench2's to give; until it has run they are bench1's reasoning by analogy, and the task that fixes them stays open.
   - **Applies to:** both 1080p films of an edition. Whether one decode of the captioned picture should feed the three derived encodes of an edition (the UHD uncaptioned picture and both 1080p films) is bench2's question; today each is its own pass.
8. **Independent checks run side by side, and the two editions may.**
   - **Rests on:** the static review: `check-picture`'s audits share no file and each is one single-threaded loop (46 + 87 s and 83 + 102 s on 16 November, before the detail audit's 40 s); the verifier decodes eight films in sequence in 482 s. bench1: one render keeps about eight of 18 cores busy.
   - **Considered:** a general worker pool in the engine; side-by-side runs only where the work is read-only or writes files of its own.
   - **Chosen because:** the three audits and the films of a verification meet that condition, and each keeps its own report, refusal and order. The two editions' renders and packages share no file either, so the sample's picture task is one task for each language, which a caller may start together; whether that is faster is bench2's to say.
   - **Applies to:** `check-picture` (three audits at once, the whole-turn check after the frame audit) and the verifier (up to four films at once).
9. **Small savings that change no result.**
   - **Rests on:** the static review's changes 9, 10 and 11: transcription has no cache and transcribed 30 recordings in 43 to 48 s when 3 were new; both phases of a still scan select the same frames of a draft and decode it twice; the reproduction compares its film pairs in sequence.
   - **Considered:** leaving them, as seconds against minutes.
   - **Chosen because:** each repeats on every iteration of a film's work, and each is exact: a transcript is a function of the recording and the pinned model, the scan's frames are the same frames, and a pair's comparison reads nothing another pair writes.
   - **Applies to:** `narrate`, the still scan and the reproduction. The static review's changes 1, 2 and 8 speed up the every-frame comparison, which now runs on demand; they stay open.
10. **Narration over several model processes is measured before it is built.**
    - **Rests on:** the static review: synthesis is 558 to 787 s of a 30-segment narration, every thought is generated from its own request and seed, and whether two MLX processes share the GPU productively cannot be read from source.
    - **Considered:** building the worker pool now.
    - **Chosen because:** the gain may be nil and the takes must stay byte-identical; one ticket decides both (`fk/r36/bench3/bench3.sh`: segments narrated alone, both languages at once, two workers of one language; times, peak memory and every take's SHA-256 against the sequential run).
    - **Applies to:** a later slice.

## Risks / Trade-offs

- A film's composition may draw in the band's rows. → The derivation refuses before it encodes and names `--native`; nothing is delivered from a refused derivation.
- The uncaptioned UHD master becomes a second-generation encode. → 59.0 dB from the native render on average on bench1's span, above the engine's own floor by 14 dB; `--native` stays.
- The 1080p settings are not yet measured at 1080p, nor the derivation's own form of the paint at UHD. → Named constants and an open task; the sample build and the verifier check every film's keyframes and strokes either way.
- More workers on a host under load. → The count is capped at 16 and recorded; the override exists.
- Side-by-side verification reaches the 240 s limits of a packet listing sooner on a loaded host. → Four films at most; the limits refuse and do not corrupt.

## Migration Plan

An adopting film bumps the engine, keeps its tasks and builds: its uncaptioned picture is derived, its comparison record says so, its 1080p films are x264's. It may drop `stage-picture --uncaptioned` only if it never asks for `--native`; `preflight` still asks for both stages. A release rebuilt from an earlier tag keeps that tag's engine and its bytes.

## Open Questions

- bench2: the 1080p rate factor and time; one decode for three encodes; two renders at once.
- bench3: narration over several processes.
- Later slices: span renders and the segment cache; a verification that does not decode again what the build proved, which changes what the verifier claims and is the owner's decision; the reviewers' measuring tools shipped by the engine.
