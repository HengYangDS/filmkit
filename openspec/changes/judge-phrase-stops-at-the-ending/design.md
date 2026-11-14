## Context

`final_fall` judges how a take's last loud syllable falls silent: on 1 ms RMS frames, from the last frame at or above −40 dBFS to the first later frame at or below −65 dBFS, as the median over the grid's phases, with both bounds lowered by each gain judged. An ending stops when the shortest of these falls is under 6 ms and the 15 ms before the fall are voiced. `ending`, `phrase_ends`, the audition and the review's delivered endings all read it.

A probe over the six delivered soundtracks of the three films (`build/evidence/ending-calibration/`) finds two phrase ends with a fall under 6 ms at any judged gain. Essentials English 01.2 "overnight,": 5 ms at the take's level into the closure of /t/, voiced on 37 of 48 phases, then a release that peaks at −40.4 dBFS on the take's scale and falls in 19 ms at every lowered bound. DDWG English 14.4 "person,": 9.5 ms at the take's level, 5 ms at the delivered gain, nothing after it; read where that fall begins the voicing is 0.83 as the median over the phases (0.75 to 0.86), read where the take-level fall begins it is 0.44.

## Goals / Non-Goals

**Goals:**

- One verdict for one sound, wherever its recording or soundtrack starts.
- A closure before a heard release is not judged as the ending; a cut is, also when a click follows it.
- The two phrase ends of the delivered films keep the verdicts their reviewers gave: "overnight," passes, "person," stops.

**Non-Goals:**

- A release that follows its closure after 80 ms or more of heard quiet.
- A declared exception for a single ending, and any change to `voicing`, to the bounds or to the 6 ms line.

## Decisions

- **Each gain is judged whole.** For each gain the function takes, on every phase, the last loud frame, the fall after it and the voicing of the 15 ms before that frame ends, and reduces each to its median. Reading the voicing at another gain's place judged a different sound than the fall. The alternative, a longer voicing window, steadies the number at the vowel but still reads the wrong place when the judged fall lies later.
- **A fall after which the sound rises again is not the ending.** The greatest gain judged has the lowest bound, so its last loud frame is the last sound a listener can hear as loud. When that frame ends after a lesser gain's stop, the sound rose by at least 19 dB after that stop. If its own fall is natural, the earlier fall was a closure and the later sound its release, and only the release is judged. If the later sound stops at once it is a click or a second cut, and the earlier fall keeps its verdict. A rule by spelling (a word that ends in a stop consonant) was rejected: it is one language's orthography, and the sound itself shows the release.
- **An ending stops when any gain that is the ending's shows a voiced fall under 6 ms.** The reported fall, gain and voicing are those of the stopping gain with the shortest fall, or else of the shortest fall. Before, the shortest fall was reported with a voicing that could belong to another place.
- **`voicing` itself is unchanged**, so the numbers stay comparable with earlier records; the function is called once per phase, which costs about 70 ms an ending and adds under two minutes to an edition's measurement.

## Risks / Trade-offs

- A take that the films hold could change its verdict and with it a selection or an assembly. Every recorded take behind the six delivered editions, 7,611 in all, and the takes of one film's next edition were judged by the old and the new function (`build/evidence/ending-calibration/`): two verdicts change. An audition take of DDWG English segment 19 that no film binds was refused on a voicing of 0.83 read at another place and is natural at 0.29. The bound take of essentials English 01.1 was natural on a voicing of 0.74 read where the take-level fall begins; its voice fades to −44 dBFS and is then cut to silence within 2 ms, which the bounds lowered by 5 dB show with a voicing of 0.94. The next edition's lane binds the same take. That film's assembly will refuse the thought until it is auditioned again or its join declares a release. As delivered, at the program gain of 4.4 dB, the thought's ending is natural by the old and the new function.
- The delivered phrase ends keep their reviewers' verdicts: "overnight," does not stop on the delivered or on the shifted soundtrack, and "person," stops with any lead of silence; under the old function it stopped at one lead of five tried.
- A real cut followed inside 80 ms by a sound that dies away slowly would pass as a release. The comparison found no ending that the new rule excuses except the closure above.
- A sound after a cut that is loud at the take's own level and stops at once is the last loud frame at every gain, so the cut before it is not judged. This was so before this Change and stays so.
