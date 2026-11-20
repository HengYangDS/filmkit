## Why

`content/release.json` is the record a film's rebuild is compared with. The engine reads it and holds its model, its asset names and its checksum format, but no engine command writes it. The films write it with two scripts outside their repositories, and the one that writes imports a delivery module the engine renamed in 0.23.0, so on 0.24 no film can record a release. That script also restates bindings the film verifier already checks, and takes each film's PSNR floor from a default in its own code.

The draft Change `decide-before-heavy-work` leaves the release's documents to a later Change, and its decision 21 says what a release's record is for. This Change admits the first part: the engine writes the record it reads.

## What Changes

- **One command writes the record**: `python -m filmkit.delivery.release --sources <path> ... [--replace] [--dry-run]`. It stages every asset under its release name in `build/artifacts/release/` with the checksums file, and writes `content/release.json` last.
- **The command asks each fact of its owner.** The film verifier answers for each edition's bound inputs and its review, without decoding a film; the stage of a picture the record names is asked of the staging; the delivery module answers that the film's own delivery folder holds the build's bytes now.
- **Each film keeps the floor its record states.** The floor of a film the replaced record names is carried; a film it does not name gets none, and the command says so.
- **The film-bound sources are stated at every run.** `--sources` names them and is required. Which files are film-bound is declared once, in the film, and the film's task derives the paths from that declaration when it calls the command; the command carries no list from the record it replaces.
- **The release folder is not overwritten with other bytes unless the caller says so.** A folder that holds other bytes than the record's is refused by entry; `--replace` lets the command replace them; a second run on the same build changes nothing.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `film-package`: a release record is written by the engine from the reviewed, delivered build; it keeps each film's floor, records the film-bound sources its caller states, and does not replace another release's assets.

## Impact

- `src/filmkit/delivery/release.py` (new), `delivery/reproduction.py` (the manifest's rules become callable on a record that is not yet written), `delivery/verification.py` (the checks that decode nothing become callable on their own; a missing review record is a named refusal), `delivery/folder.py` (the comparison of a folder's members with the build's) and their tests; the README and the Changelog.
- An adopting film adds one task that calls the command after its delivery and names the film-bound sources from the film's one declaration of them; its test that compared the record's list with that declaration goes with the copy it guarded. Nothing it imports from `filmkit.delivery.reproduction` moves.
- Out of scope, with the reason in this Change's design: which assets a release's page carries and the comparison's local reference for a release's films (the rest of the draft's decision 21), the check of figures in a film's release documents (the draft's decision 17), and sending assets to a forge, which is not the engine's.
