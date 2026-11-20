## Why

The still scan's own text says that it "refuses a draft before the final render and confirms the final film before it is reviewed". No command, task or gate ever ran it on a final film. It is asked only of a draft, and only of a film that declares drafts, which none of the three films does.

A released edition carries the consequence. On 18 November 2026 the engine's scan read the released 1080p film of the ETHOS film's Chinese edition (2.0.1) and found one still run over the limit: 842.7 to 847.4 s with 3.86 s of speech, against a limit of 3.5 s. Three things had let it pass:

- No gate asked. `preflight` asks for a draft's scan only of a film that declares drafts.
- A draft would have passed it. Both a browser's and a native canvas's draft at 1920x1080 end that run at 845.5 s with 2.32 s of speech, because one label steps by one pixel there at the draft's size, and the film holds the label still.
- The review stated no still picture over 2.2 s under speech, by the reviewers' own measure.

`design.md` names the records of each.

## What Changes

- **A step of every edition's build:** `filmkit.produce scan-film --language zh|en` scans the edition's packaged 1080p captioned film against its timeline, by the scan as it stands (the same two rules, the same two phases, the same limit), and writes `build/evidence/editions/<edition>/film-stills.json`. The record binds the film, the timeline and the composition by SHA-256, names the engine's version and states the rules it was written under and the frames each phase read. A film that holds a still run with 3.5 s of speech or more is refused after its record is written, with each run's time and speech. A film that cannot be read, that changes while it is read, or that does not decode to the frames of its timeline's seconds is refused and leaves no record.
- **One reader of both records:** `filmkit.picture.still_record.answer` reads an edition's film record and its draft record. It answers only from a record that has the scan's shape, binds what stands, states the engine's own rules (its limit, the filters of its decode and the cut of speech among them), read the whole film and agrees with itself. Whatever else stands at a record's place, a record cut short or nested too deep included, is named with the part that fails and with the command that writes a new one, and no reader ends with an error of its own. `scan-film` then scans again: the command a refusal names repairs any record.
- **A gate every release passes:** the delivery's verification, in both its scopes, refuses an edition whose film record does not answer or lists such a run. It names `scan-film` or the run. **BREAKING** for a film's build: a task list that runs no `scan-film` after `package-film` is refused at its verification.
- **Delivery asks the same:** `filmkit.delivery.folder` asks that requirement of both editions before it copies anything, in a dry run too, so `package-film` followed by a delivery does not deliver an unscanned film. It refuses a root that is not the film the command runs in, whose scans it reads.
- **A round is not prepared for a film the verifier would refuse:** a round's preparation, `filmkit.review.round prepare`, asks the same requirement of both editions among the checks that only read, before it derives or writes anything.
- **One owner:** `filmkit.picture.still_scan.require_film_scan` decides whether an edition passes; the verifier's check of an edition's bound inputs, the delivery and a round's preparation call it, and the release record's writer asks it with those bound inputs. The draft's question in `preflight` reads the draft's record by the film record's reader, so a draft scanned under another limit states other rules than the engine's and admits no render.
- **An unchanged film is decoded once:** a second `scan-film` answers from a record that answers for the film as it stands, and its line and its duration record say that nothing was decoded.
- **Speech at the limit:** a run's speech is recorded cut to whole hundredths, so 3.496 s is recorded as 3.49 s and is not at the limit. The messages and both capabilities say "3.5 s of speech or more". The scan's command refuses a `--limit` that is not in whole hundredths.
- **A set-aside moves the record with its films:** `film-stills.json` goes with the edition's films as their scan record, whatever it says.
- **What the scan cannot read is refused by its name:** an answer of ffprobe that is no frame rate, a decode that fails after some frames, a timeline whose words or duration cannot be read. A draft that does not decode to its timeline's seconds is refused as a film is.
- **The draft's scan is unchanged and described truly:** it is an early warning. The scan's module text, the pre-render check's and the draft's say that a draft at half the size the film's picture is drawn at can pass a run the film holds, and that the film's scan decides.
- **One decode for both phases:** a film of 60 fps was decoded once a phase; one decode now keeps the frames of both, dealt to their phases in turn. What a phase reads is unchanged.
- **The sample film:** its package task runs `scan-film` for each edition, after its two final films read at least 0.5 s under the limit (`tasks.md` 2.1). Its Chinese film reads 0.18 s under it by two earlier builds, so its first scene changes first, in a step of this Change (`tasks.md` 2.3).
- No declaration of exceptions. `design.md`, decision 7, says what would admit one.

## Capabilities

### New Capabilities

- `final-film-scan`: the command that scans an edition's packaged film, its record and the one rule by which a record answers, the answer from an unchanged record, the verifier's requirement and the delivery's.

### Modified Capabilities

- `render-preflight`: one requirement is added, that a draft's record settles nothing about the film. Two are restated for the limit's one wording and for the reader a draft record is read by: the pre-render check's and the draft command's, the second as `draw-pictures-natively` leaves it, which is archived before this Change.
- `review-rounds`: two requirements are added: a round's preparation waits for both films' passing scan, and a set-aside moves a film's record with the film.
- `sample-film`: one requirement is added, that the sample's package task scans its packaged films.

## Impact

- **Code:** `src/filmkit/picture/still_scan.py` (the film's scan and its requirement), `picture/still_record.py` (the one reader of a scan's record), `repository.py` (an entry nested too deep is one that cannot be read), `production.py` (the record's place), `produce.py` (the action), `delivery/verification.py` (one call), `delivery/folder.py` (one call, and its root), `review/prompts.py` (one call), `review/set_aside.py` (one member), `preflight.py` and `picture/draft.py` (the shared rules and the draft's wording), and `.config/mise/config.toml` (the sample's package task).
- **What a build pays:** one decode of the 1080p film. With a decode a phase, the scan's earlier form, four released editions took, on 18 November 2026 at a 1-minute load of 21 to 41: 107 and 111 s for editions of 600 s, 96 and 126 s for editions of 900 s. What one decode takes is measured by `tasks.md` 5.2 and not stated before. A second run on an unchanged film decodes nothing.
- **Records of an earlier form:** a record that the scan's general form wrote before this Change states no rules and no frames of its phases; at the film record's place it is named as one that cannot be read. A draft record of that form cannot be read either, and `render-draft` draws the draft again; of the three films and the sample, only the sample declares drafts.
- **A film that adopts this engine:** its package task gains `scan-film` for each edition, after `package-film`. Until then its verification and its delivery refuse both editions as having no still scan record. An edition whose film holds a run at the limit is refused until its picture changes inside that run: by the engine's scan of its released film, the ETHOS film's Chinese edition is such an edition (842.7 to 847.4 s), so its next edition changes that scene before it can be verified. The other three editions measured read 2.56, 3.06 and 2.90 s; the DDWG film's two editions are not measured.
- **Released editions are not rebuilt.** An edition keeps its tag's engine, and that engine's verification asks for no film record.
- **A film that declares drafts** keeps its draft step as it is. Its draft record admits a render and no longer reads as a statement about the film.
- **Not proved by this Change's tests:** that the sample film's two final films read at least 0.5 s under the limit on this engine's head. `tasks.md` 2.1 holds the step that requires it until they are read; `design.md`, decision 9, states the readings so far.

`tasks.md` is the sole progress ledger.
