## 1. Sound

- [x] 1.1 Lower the floor of `thought_level_tolerance_db` to 0.25 dB; done when a policy of 0.25 is accepted and 0.2 is refused with the range.
- [x] 1.2 Add the production action `check-sound` with its record `sound-gates.json`; done when its tests show a pass, each refusal with its place and figure, and a film without a floor not judged on clarity.
- [x] 1.3 Measure segment clarity on the whole soundtrack's grid and threshold and record each thought over the grid's sixteen phases; done when the engine's segment figures stand within 0.05 dB of the reviewers' on a delivered soundtrack.
- [ ] 1.4 Run `check-sound` in the sample film's build and state it in the README's stages; done when the sample film's acceptance runs it and passes. The gate refused the sample's English soundtrack at its first run (16.68 dB against a declared 17 dB), so the sample declares the floor its first takes hold, 16 dB.

## 2. Captions

- [x] 2.1 Typeset the caption cues a timeline holds; done when a built English timeline holds no straight apostrophe or quote in a cue and verification refuses one that does.

## 3. Picture

- [x] 3.1 Record the clear gap between neighbouring names on one row in the geometry check and gate it with `--gate-row-gaps`; done when the measure finds every pair the reviewers' notes name on the delivered films and the check fails for them only when gated.
- [x] 3.2 Record every stretch of glides and flows over the pace line in the motion audit and gate those over a film's declared `picture.motion.pace_limit`; done when the audit's stretches cover the glides the notes name and a film without a limit is not refused.
- [x] 3.3 Test one-frame transients and edge slivers in the comparison of an edition's two masters; done when a synthetic one-frame fault refuses and the delivered masters' events stay under the declared bound.

## 4. Reproduction

- [x] 4.1 Report a rebuilt film that holds its published film's bytes as identical without decoding it; done when no decode runs for such a film, a one-byte difference takes the full comparison, and a film without a floor still does not pass.

## 5. Release

- [ ] 5.1 Check every changed measure against the delivered films' records; done when each gate's hits on the three films are listed beside the notes they answer, with no unexplained hit.
- [ ] 5.2 Record the release in the Changelog and set the version to 0.22.0; done when `mise run check` passes.
