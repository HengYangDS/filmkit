## 1. Durations

- [x] 1.1 Add `filmkit.durations`: a run for a command and an edition, phases named by the code that does the work, one record written when the run ends whether it completed or not, and the command that prints an edition's records with their sum; verify `tests/test_durations.py`.
- [x] 1.2 Start a run for every action of `filmkit.produce` and for `narrate`, each step a phase, and name the phases of `compare-pictures`, `package-film` and `check-picture`; verify `tests/test_durations.py` (an action's record, a refused action's record) and `tests/narration/test_narrate.py` (a run's record, none for a dry run).
- [ ] 1.3 State each film's seconds in the verifier's report, which writes nothing, and in the reproduction's report; verify `tests/delivery/test_verification.py` and `tests/delivery/test_reproduction.py`.

## 2. Render settings

- [x] 2.1 Take the render's worker count from the host or from `FILMKIT_RENDER_WORKERS`, for the pictures and the draft, and record it in the receipt; verify `tests/picture/test_workers.py` (18 cores give 16, 10 give 8, a named count is passed and recorded, a value that is no count is refused) and `tests/picture/test_capture.py`.

## 3. The derived uncaptioned picture

- [x] 3.1 Add the tool `band-audit`: at every thirtieth of a second, each caption paint within the painted rows, no other paint reaching them, and the stretches without a caption; verify `tests/picture/band-audit.test.mjs` on a composition that passes, one whose scene draws into the band, one whose caption leaves it and the sample film.
- [x] 3.2 Add `filmkit.picture.derivation`: the ground read from a frame without a caption, the encode with the band painted and the captioned band measured in the same decode, the ground check on every frame without a caption, the receipt and its validation; verify `tests/picture/test_derivation.py`, which derives a short synthetic clip with the host FFmpeg and refuses one whose band is not the ground, and `tests/picture/test_derived_pair.py` for the receipt and each refusal.
- [x] 3.3 Make `render-picture --uncaptioned` derive unless `--native` is given, and let `validate-picture --uncaptioned`, the verifier and packaging read either receipt; verify `tests/test_produce.py`, `tests/picture/test_derived_pair.py` and `tests/delivery/test_derived_verification.py`.
- [x] 3.4 Make `compare-pictures` compare a derived pair by its derivation's receipt without decoding, and bind a derived picture without a stage document; verify `tests/picture/test_derived_pair.py` (a current derived pair passes without a decode, a captioned picture rendered again is refused, a derived pair is no case for `repair-pictures`).
- [x] 3.5 Run the band audit read-only on the three films' current compositions; verify that each of the six editions passes and lists stretches without a caption (`fk/r36/films.log` in the films' kit).

## 4. The 1080p films

- [x] 4.1 Encode the 1080p films with x264 at named settings and force the keyframe grid by the interval, its minimum and no scene cuts, with no VideoToolbox decoder; verify `tests/delivery/test_packaging.py` and `tests/delivery/test_viewing_encode.py`, one case encoding four seconds that change whole at frame 50 with the host FFmpeg and reading keyframes at frames 0 and 120 alone.
- [ ] 4.2 Fix the 1080p rate factor and preset from bench3 (`fk/r35/bench3/result.txt` in the films' kit, pending: the whole span at rate factors 16, 14, 12 and 10 and three presets), by the lowest frame not under VideoToolbox's 51.8 dB at the smallest time, and state the figures in the design; verify that decision 7 cites them. Until then the constant is 12, from bench2 and this Change's own 30 s measurement.
- [x] 4.3 Decide from bench2 whether one decode of the captioned picture feeds the three derived encodes of an edition: it does not, being slower (43.6 s) than three separate passes (32.2 s); verify `fk/r35/bench2/result.txt` in the films' kit.
- [ ] 4.4 Encode the 1080p uncaptioned film of a derived pair from the captioned picture, painted as the derivation painted it and scaled in the same pass; verify `tests/delivery/test_viewing_encode.py`.
- [ ] 4.5 Decide from bench3 whether an edition's derived passes and the two editions' renders run at once, the renders with the renderer's own switch `HYPERFRAMES_RENDER_LOCK=off` set by the caller and recorded in the receipt; verify by the durations of a sample build before and after.

## 5. Renderer qualification and the sample film

- [ ] 5.1 Add `qualify-renderer`: render the edition's captioned stage again to a work file, compare every decoded frame with the picture's, write the record and refuse a difference by its first frame; verify `tests/picture/test_qualification.py`.
- [ ] 5.2 Give the sample film one picture task for each language, the Chinese one qualifying the renderer and rendering its uncaptioned picture with `--native`, the English one deriving it, and add the task that prints the sample's durations; verify `mise tasks` lists them and the Markdown check passes on the README.

## 6. Side by side and small savings

- [ ] 6.1 Run `check-picture`'s frame, motion and detail audits at the same time, the whole-turn check after the frame audit; verify `tests/picture/test_gates.py` (the same record as in sequence, and a failing audit named).
- [ ] 6.2 Verify up to four films at the same time and print the reports in the films' order; verify `tests/delivery/test_verification_media.py` and `tests/delivery/test_verification.py`.
- [ ] 6.3 Compare the reproduction's film pairs side by side; verify `tests/delivery/test_reproduction.py`.
- [ ] 6.4 Cache each recording's transcript by its SHA-256, the recognizer's revision and the language, and load a speech model only when a record misses its cache; verify `tests/narration/test_transcription.py` and `tests/narration/test_alignment.py`.
- [ ] 6.5 Decode a draft once for both phases of its still scan; verify `tests/picture/test_still_scan.py`.
- [ ] 6.6 Speed up the on-demand every-frame comparison (the static review's changes 1, 2 and 8: parallel time segments, the sampled measures off the scan's decode, band differences in 8 bits); verify that a delivered native pair's record is unchanged.

## 7. Measurements and acceptance

- [x] 7.1 Run bench2 under a host ticket and record its result beside bench1's; verify that task 4.3 can be decided from it (`fk/r35/bench2/result.txt`, 03:40 to 03:53 CST on 17 November 2026).
- [ ] 7.2 Run bench3 (`fk/r35/bench3/bench3.sh` in the films' kit) under a host ticket: narration in one and several processes with every take's SHA-256 against the sequential run, two renders at once, the x264 rates and presets, the derived passes at once; verify that `fk/r35/bench3/result.txt` decides tasks 4.2 and 4.5 and whether a later slice builds narration workers.
- [ ] 7.3 Run `mise run check` and the proof's static lint on the lane's head; verify that the Node suite, the Markdown check, the Python suite and the lint pass.
- [ ] 7.4 Build the sample film with `mise run sample:build`; verify that the Chinese pair passes `qualify-renderer` and the every-frame comparison, the English pair is derived and compared by its record, all eight films verify, and `mise run sample:durations` lists every stage.
- [ ] 7.5 Build one film's edition with the engine before and after this Change and print both builds' durations; verify the sum against the budget of 90 minutes for both editions of the 25-minute film, and state the measured figures in the Changelog.
- [ ] 7.6 State the duration records, the worker count, the derived picture with `--native`, `qualify-renderer` and the 1080p encoder in the README and the Changelog; verify the repository's Markdown check on both files.
