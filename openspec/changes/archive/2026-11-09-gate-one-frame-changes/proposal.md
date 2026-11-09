## Why

The DDWG film's round-34 production review (2026-11-09) failed both editions on changes a viewer sees within one frame, all of which `check-picture` 0.16.0 had passed. Where a declared stage cut kept a group's marks, the group moved whole within one frame: 04.2's field and its name moved 354 px, and the English 05.2's case moved 224 px. The follower stops at a cut, so it never judged those moves. A label appeared at full ink within one frame of a stage that otherwise stood (06.2), and a link gave way to a divider the same way (02.2). The composition declared each of those frames a stage cut, and a declared cut excuses every pop. A join turned from solid to dashed within one frame (13.1). The audit records only whether a stroke is dashed, and it follows the stroke as one mark. The reviewers found each change with their own 60 fps frame scripts, and the build was rendered, reviewed and repaired again.

## What Changes

- The motion audit reports a jump: at a stage cut, a group of firm marks that the cut keeps but moves whole by one shift of 8 px or more beyond their own motion in the frame before, when the group holds at least half of its scene's firm ink. `check-picture` refuses it as `motion_jumps`.
- A declared stage cut excuses the marks it brings only when it changes the stage as a detected cut does, at least 35% of the scene's firm marks, counted or by ink. Otherwise each mark that appears within it at ink 60 or more is a pop; the marks it takes away stay excused.
- The headless composition records each stroke's dash pattern. The audit reports a dash snap when a followed stroke's gaps open or close by a quarter or more of its pattern within one frame, outside a stage cut, and `check-picture` refuses it as `motion_dash_snaps`.
- A film may declare a jump or a dash snap as it declares a pop (`[[picture.motion.exceptions]]`, kind `jump` or `dash`), and the review's measurements count both.
- This breaks a composition that moves the marks a cut keeps, brings a mark into a standing stage at a declared cut, or switches a stroke's dashes within one frame. The DDWG film's round-36 build has already repaired the cases its review found, and each film gates again under the release before its next render.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `picture-motion`: a declared cut excuses only what it replaces or takes away; jumps at cuts and dash snaps are reported and refused.

## Impact

`src/filmkit/picture/motion-audit/follow.mjs` and new modules beside it for the cut and dash rules, `motion-audit.mjs`, `motion-audit/report.mjs`, `headless-composition.mjs` (the dash pattern), `picture/gates.py` (the gated measures), `film.py` (the exception kinds), `review/motion.py` (the counts), their tests and the test list in `package.json`, the README's motion paragraph and the release notes. Films adopt the release before their next render; it changes no rendered byte.
