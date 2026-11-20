## Why

A review round's inputs are made by four engine commands and by scripts outside the repositories, and only those scripts hold the order. They trace the picture a second time for the sync record the measurement asks for, deliver to a preview folder to obtain the players' readback, and refuse a second run once the round's directory exists. The films' preparation script also calls a delivery module the engine renamed in 0.23.0, so on 0.24 no film can prepare a round. The whole-edition trial of 19 November 2026 walked this leg with engine commands and listed what is missing (its report, the section "The second leg, walked").

The draft Change `decide-before-heavy-work` leaves the review round's preparation to a later Change. This Change admits that slice: one command that prepares a round, with the draft's decision 20.

## What Changes

- **One command prepares a round.** `filmkit.review.round prepare --round <n>` writes the round's directory: the binding of the members a delivery would hold, the real-browser readback of their players, the listening plan, the measurements, each edition's sentences and each edition's prompt. It checks what it reads before it derives anything and writes the prompts last, so a preparation that stops leaves no prompt. **BREAKING**: `review.round prompts` and `review.round bind` are no longer commands; a film's task that calls them calls `prepare`.
- **A round is prepared again while it holds nothing but a preparation.** A round that holds a review, or anything else `prepare` did not write, is refused by name, and so is a round whose films were set aside.
- **The measurement reads the sync report the picture gate judged**, through the gate's record, as it reads the motion report. A round runs no trace.
- **The readback a reviewer reads is the round's own**: the player check's receipt and screenshots for exactly the members the round binds.
- **The round keeps what it was prepared with**: the changes note and the dispositions file, beside the prompts that state them.
- **The record derives a review's overall from its scores**; a reviewer's stated overall decides nothing.
- **A film declares the severities a review may hold**: `[review] accepted_severities`. A review that holds a finding of any other severity is refused. A film that declares none keeps today's verdicts.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `review-rounds`: a round is prepared by one command; it holds its readback, its changes note and its dispositions; its measurement reads the gate's sync report; the record derives the overall; a film declares the severities a review may hold.

## Impact

- `src/filmkit/review/round.py`, `review/prompts.py`, `review/record.py`, `review/measurement.py`, `review/motion.py`, `delivery/folder.py` (the members' plan and the players' readback, asked by the round), `delivery/verification.py` (the accepted severities), `film.py` (one declaration) and their tests; the README and the Changelog.
- An adopting film replaces its preparation script by one task that calls `prepare`, names `player-check.json` as the readback in its prompt, and declares `accepted_severities` where its rule accepts fewer findings than the engine's.
- Out of scope, and left in the draft with the reason in this Change's design: the check of evidence a changes note cites, the measured lines of a changes note, the place where a previous round's reviews outlive a checkout, dispositions written from reverification lines, and a receipt of the film verifier's verdict.
