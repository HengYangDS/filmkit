"""Lines in the form of the pinned CMUdict, written for the tests that hear English words by their
pronunciations (`filmkit.narration.cmudict`).

They hold the words of the Change's scenarios. Where the Change's readings read a word in the
pinned file (labelled, tiers, tears, their, an, and, or, are, a, ai, catalogue, to and its
homophones), its lines state what they read; the others are written for the tests. The test over
the pinned file itself is marked `cmudict` (`test_cmudict.py`). A test that stands the lines in
for the supplied file writes them where the supply step places it and pins their own SHA-256 and
size (`supplied`).
"""

import hashlib

import filmkit.narration.cmudict as cmudict
import filmkit.repository as repository

LINES = """\
a AH0
a(2) EY1
ahn AA1 N
ai AY1
ai(2) EY1 AY1
an AE1 N
an(2) AH0 N
and AH0 N D
and(2) AE1 N D
ann AE1 N
anne AE1 N
are AA1 R
are(2) ER0
catalog K AE1 T AH0 L AO0 G
catalogue K AE1 T AH0 L AO2 G
d'artagnan D AH0 R T AE1 NG Y AH0 N # foreign french
delivery D IH0 L IH1 V ER0 IY0
eye AY1
get G EH1 T
get(2) G IH1 T
git G IH1 T
half HH AE1 F
i AY1
labeled L EY1 B AH0 L D
labelled L EY1 B AH0 L D
or AO1 R
or(2) ER0
read R EH1 D
read(2) R IY1 D
red R EH1 D
tears T EH1 R Z
tears(2) T IH1 R Z
tew T Y UW1
tew(2) T UW1
their DH EH1 R
there DH EH1 R
they're DH EH1 R
thuy T UW1
tiers T IY1 R Z
to T UW1
to(2) T IH0
to(3) T AH0
too T UW1
tu T UW1
tue T UW1
two T UW1
uh AH1
"""
RAW = LINES.encode()


def supplied(monkeypatch, root=None) -> cmudict.Dictionary:
    """Write the fixture where the supply step places the pinned file, below `root` or the
    repository's, pin its SHA-256 and size, and return it as the reader reads it."""
    monkeypatch.setattr(cmudict, "SHA256", hashlib.sha256(RAW).hexdigest())
    monkeypatch.setattr(cmudict, "BYTES", len(RAW))
    path = (root or repository.ROOT) / cmudict.PLACE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(RAW)
    return cmudict.parse(RAW)
