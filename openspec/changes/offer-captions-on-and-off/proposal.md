# Proposal

## Why

Each film draws its captions into its picture, and every film an edition delivers shows them: the UHD master copies the rendered picture and the 1080p viewing film re-encodes it, and the engine's player offers no caption control. Two independent reviewers of the essentials film scored credits and deliverable craft 88, a material finding, because a viewer cannot turn the captions off. The owner decided that the films offer captions on and off.

## What Changes

- **A picture without captions.** `stage-picture --uncaptioned` stages the same composition and timeline with no captions in a stage of its own, `render-picture --uncaptioned` renders it with the same renderer settings to its own picture and receipt, and `validate-picture --uncaptioned` binds it. Each stage record and receipt names its picture.
- **An equivalence gate.** `produce compare-pictures` proves that the uncaptioned picture differs from the captioned one only by its captions: at the composition, frame by frame through the headless composition, and in the encoded pictures, decoded and compared outside the caption band within the encoder's measured noise. It writes the edition's record, which packaging requires.
- **Four films per edition.** `uhd` and `1080p-captioned` keep their names and contents. `uhd-uncaptioned` copies the uncaptioned picture's stream and `1080p-uncaptioned` re-encodes it as the viewing film is. All four carry the same soundtrack, chapters, metadata and cover.
- **A captions control.** The player gains one button, pressed while the captions show, that switches to the other film of the same version. The version buttons keep its state, and both keep the time and whether the film plays. The files list says of each film whether its picture draws the captions. The hidden metadata track stays for the transcript's current paragraph.
- **Delivery and verification.** The Documents delivery, the release manifest, the film verifier, the review rounds and the set-aside take all four films. The real-browser player readback exercises the captions control and fails a page whose control does not switch.
- **BREAKING**: an edition delivers four films and the delivery 25 members. A film adopts 0.13.0 by rendering and comparing its uncaptioned pictures and packaging again; its next review covers the four films.
- **Out of scope.** Moving a film to 0.13.0, which each film does in its own lane; burning captions in during packaging; offering the WebVTT track as browser captions.

## Capabilities

### New Capabilities

- `caption-equivalence`: the uncaptioned picture of each edition, staged and rendered beside the captioned one, and the gate that proves the two differ only by their captions before packaging.

### Modified Capabilities

- `film-package`: four films per edition, a captions control in the player, a files list that names each film's captions, the readback of the control, and a release manifest that names the films with and without captions.
- `review-rounds`: a set-aside moves a build's own films and pictures, so a build packaged before 0.13.0 is still set aside.
- `render-preflight`: the preflight checks the uncaptioned picture's stage beside the captioned one's.
- `sample-film`: the sample film renders, compares and delivers both pictures.

## Impact

- **Code.** `production.py` (the four renditions and each picture's places), `picture/rendering.py`, `produce.py`, a new `picture/equivalence.py` with its tool `picture/caption-equivalence.mjs`, `tools.py`, `delivery/packaging.py`, `delivery/player.py`, `delivery/player-read.mjs`, `delivery/player-verdict.mjs`, `delivery/player-check.mjs`, `delivery/documents_folder.py`, `delivery/verification.py`, `delivery/reproduction.py`, `preflight.py`, `review/set_aside.py` and `review/round.py`.
- **Films.** A film's composition needs no change when its caption painter is the only reader of the timeline's captions, as in all three films. Its output grows by two films per edition; the captioned films keep their pictures and packaging.
- **Adoption.** A stage record or receipt written before 0.13.0 names no picture and stays the captioned picture's, so no captioned picture is rendered again. A build packaged before 0.13.0 is set aside with its two films and its captioned picture. A release published before 0.13.0 is compared on its own films.
