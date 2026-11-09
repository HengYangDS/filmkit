## Context

The motion audit renders the composition headlessly, follows every visible mark from frame to frame (`motion-audit/follow.mjs`) and reports halts, starts, races and pops; `check-picture` refuses them outside a stage cut. A frame is a stage cut for a scene when 35% of its firm marks change, or when the composition declares one (`declaredCuts`). At a cut the follower stops: it restarts every mark there and judges no pop.

The DDWG film's round-34 reviewers measured the delivered films at 60 fps with their own scripts (`build/evidence/reviews/round-34/en/fine_all.py`, `fine_an.py`, `jumps2.py`; `zh/scripts/scan34.py`, `classify34.py`) and found five changes the gate had passed:

- EN34-2 and Z34-1: 04.2's field and its name moved 354 px within one frame (English 165.783 s, Chinese 161.017 s), 0.59 s into the thought, at a declared cut that kept every mark; the English 05.2's case moved 224 px at 256.8 s. `jumps2.py` calls a change a jump when it shifts at least 8 px and at least 70% of the earlier frame's bright pixels reappear shifted, while at most 50% stay in place.
- EN34-1 (a) and (b): 06.2's hypothesis appeared at full ink within one frame (300.183 s, 951 px changed at 960×540, 0 and 1 px in the frames on either side), and 02.2's tie vanished as a divider appeared (54.733 s). The composition declared both frames as stage cuts.
- EN34-1 (c): 13.1's join turned from solid to 8-on, 8-off dashes within one frame (645.967 s), not at a cut.

The reviewers accepted the other one-frame changes they listed: whole or partial replacements on a thought's or a clause's first words. They noted partial removals inside a thought and asked for no repair.

## Goals / Non-Goals

**Goals:**

- Refuse before review what the reviewers found: a kept group moved at a cut, a mark brought into a standing stage at a declared cut, and a dash switch.
- Keep a cut's replacement and its removals excused, as the reviewers did.

**Non-Goals:**

- A pixel-level 60 fps scan of rendered films. The audit judges the composition's marks headlessly, before any render.
- Judging a partial removal inside a thought; the reviewers noted those and asked for no repair.

## Decisions

- **A jump is a kept group moved at one shift beyond its motion.** At a cut the audit matches the scene's firm marks across the frame by their kind, words, line width and one size, leaving out those that stand where they stood; the follower's own pairs reach only 4,500 px/s, short of a jump of hundreds of pixels. A pair whose shift, less the shift its earlier mark moved by in the frame before (none at rest or newly drawn), is 8 px or more is a moved mark. The audit groups those marks by a shared shift, within 2 px, and reports a jump when the group's ink, weighed by box area times ink level, is at least half of the scene's firm ink before the cut. This is `jumps2.py`'s rule on marks instead of pixels, and judging the shift beyond each mark's motion keeps it from depending on the frame rate: at 30 fps a glide of 240 px/s moves 8 px a frame, and the calibration found ten glides through declared cuts in the DDWG and ETHOS films that a rule on the shift alone called jumps, while each jump the reviewers named set off from rest. A stage that sets off at a cut faster than it then glides still jumps by its first step. A heading that moves while the rest of its stage is replaced is not a jump. A spurious pair between unrelated like marks seldom carries half the ink.
- **A declared cut excuses what it takes away, and brings in only by replacement.** Following still stops at every declared cut, as before. For pops, a declared cut that changes less than 35% of its scene's firm marks excuses the marks that vanish and judges the marks that appear. This keeps the reviewers' accepted removals and refuses an arrival onto a standing stage, the 06.2 and 02.2 cases. Whether the cut falls at a thought's first word is not part of the rule: 04.2's jump came 0.59 s into its thought, and the reviewers still judged it.
- **A dash snap is a step in the gap share.** The headless canvas records each stroke's dash array. Its gap share is the sum of its gaps over its period, 0 for a solid stroke. A followed stroke whose gap share changes by 0.25 or more between two frames, outside a cut, is a dash snap. Drawing a dashed way on keeps its pattern, and a break eased over 0.35 s at 60 fps steps by about 0.03 a frame. Two outlines crossfading on one box, one dashed and one solid, would trade tracks at their crossover when only ink tells them apart, and read as two dash snaps; so a mark standing unchanged continues only a mark of its own pattern, and the difference of two marks' gap shares joins their miss.
- **Each rule gets its own gated measure and exception kind.** `motion_jumps` and `motion_dash_snaps` sit beside `motion_pops`, and a film can declare a kept jump or dash snap with its reason, as it declares a pop.
- **New rules in their own modules.** The cut and dash rules live beside the follower in their own modules, so each changed file stays within the proof's size limit.

## Risks / Trade-offs

- [A film has more cases than its reviews named] → The release is calibrated on the three films' current compositions, and each finding is listed with its time. A film fixes its findings, or declares the ones it keeps, before its next render.
- [The half-ink rule misses a small kept mark that jumps while its stage is replaced] → This matches the reviewers' measure, which judges a jump by the share of bright pixels that move. A smaller rule would refuse what the reviewers accept.
- [Following stops at the old declared cuts, while pops are judged in some of them] → Following needs the cut's restart. Only the pop rule changes.

## Migration Plan

Release as 0.17.0. Each film adopts it before its next render, gates both editions, and fixes or declares each new finding. Rollback pins 0.16.0.

## Open Questions

None.
