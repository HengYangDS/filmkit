## 1. Leveling

- [ ] 1.1 Accept `segment_level_tolerance_db` from 0.1 to 3.0 in the pause policy; done when a value in the range is held under `segment_level_tolerance`, a value outside it is refused with the range, and a script without it holds null.
- [ ] 1.2 Level each segment within the tolerance of its chapter's median before the chapters are leveled, and record each segment's gain; done when a segment under its chapter is raised to the tolerance's edge, a chapter of one segment has no gain, and a film without the declaration assembles the same soundtrack and timeline bytes.

## 2. Calibration

- [ ] 2.1 Assemble the film that showed the gap with the tolerance declared and a film that declares none; done when the first film's largest step between adjacent thoughts across a segment boundary stands within its reviewers' line and the second film's soundtrack and timeline keep their SHA-256.

## 3. Release

- [ ] 3.1 State the key in the README, record the change in the Changelog and set the version to 0.22.3; done when `mise run check` passes.
