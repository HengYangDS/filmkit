# Proposal

## Why

The committee's round-2 review of the ETHOS film found two English caption breaks that the engine sets against its own rules (M3-04 and M3-05, minor, which hold acceptance of that edition). The film declares the caption term Evidence-grounded Trust for Human-Agent Operational Stewardship, and the phrasing still splits it after "Trust": a break inside a declared term costs 90, as much as a line that ends on "for", the only break that keeps the term whole, so the split wins on line length although the caption-text requirement says a declared term stays on one line. And the quotation "Done. All tests pass." spans two cues, because the sentence splitter ends a caption sentence at "Done." inside the quotation, although the sentence that holds it is 57 characters. The DDWG film meets the first defect too: it declares fact, authorization or responsibility, and its captions split the list after "fact,".

## What Changes

- **A declared term stands whole wherever it fits.** A break inside a declared caption term costs more than every layout that keeps the term on one line, so a term that fits a caption line is never split. A term longer than a line still takes the cheapest breaks.
- **A short quotation stays on one line.** A sentence end inside an open double quotation does not end an English caption sentence while the sentence that closes the quotation still fits on one caption line with it; a longer quotation divides at its sentences as before.
- **Output bytes.** A film's captions change only where a declared term was split or a quotation's sentences fit one line. On each film's current English script: the ETHOS film's segments 01, 03 and 09, the DDWG film's segment 28 and none of the essentials film's. Its subtitles, transcript and captioned pictures change where its captions do; its soundtracks and uncaptioned pictures do not.
- **Out of scope.** Chinese captions, whose sentences end inside a quotation by design; authored caption phrases, which a film sets itself; caption timing.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `caption-text`: a declared caption term stays on one line wherever it fits, whatever the other breaks cost, and a short English quotation of several sentences stays on one caption line.

## Impact

- **Code.** `captions/english.py`.
- **Films.** A film adopts the release by refreshing its captions and, where they change, staging, checking and rendering its captioned picture again in its own lane; its narration and its uncaptioned picture stay.
