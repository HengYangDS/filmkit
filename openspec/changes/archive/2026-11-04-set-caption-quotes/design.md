# Design

## Context

`filmkit.captions.chinese.caption_phrases` splits a Chinese passage into clauses with one pattern, a run of text up to and including at most one clause mark (，。；：！？、), and sets the clauses as lines. A closing quotation mark is not a clause mark, so in 。” the quote opens the next clause, and with it the next line and the next cue. The English phrasing already keeps closing marks with their sentence: its tests cover it, and the cue timing's `SENTENCE_END` reads a sentence end followed by any of `CLOSING_MARKS`. `filmkit.captions.timing.typeset` makes the display copy of a segment, which the cues, the subtitles and the transcript show; it sets only an apostrophe as a typographic quote, and it must keep the text's length, because each cue slices its display copy at the cue text's offsets.

## Goals / Non-Goals

**Goals:**

- No Chinese caption line begins with a closing quotation mark or bracket.
- The display copy sets straight double quotes as typographic ones.
- Every caption whose text holds neither stays as it is.

**Non-Goals:**

- Opening single quotes: an apostrophe stays a right single quote, as before, and no script uses single quotes as quotation marks.
- Chinese corner brackets 「」 and other closing marks the shared `CLOSING_MARKS` does not name.
- Changing a cue's text, its timing or the soundtrack.

## Decisions

### 1. Closing marks ride on their clause

The clause pattern takes any run of `CLOSING_MARKS` after its clause mark, the role `filmkit.narration.spoken_units` already names for closing quotes and brackets that belong to the sentence before them. Where the phrasing asks whether a clause ends a line or a line ends inside an enumeration, it reads the clause without its trailing closing marks, so 。” ends a line as 。 does. The cue timing reads a line end the same way, so a brief cue that ends in 。” takes the early start a brief cue that ends in 。 takes. Every other clause stays as it was, so a passage without such marks sets the same lines.

### 2. Typographic double quotes by position

`typeset` sets a straight double quote as “ where it begins the text or follows whitespace, an opening bracket or a dash, and as ” elsewhere; it then sets apostrophes as before. Each replacement is one character for one, so the display copy keeps the text's length and every cue's slice of it. Alternatives considered: tracking open and closed quotes across a segment would also handle a quote that follows a letter, but no script needs it, and a quote that spans segments would break it.

## Risks / Trade-offs

- [A film's captions change when it adopts 0.8.1] → Only cues that hold such quotes change; the film refreshes its captions and checks them before it renders.
- [A Chinese script that types straight quotes] → Position cannot tell its opening quotes from its closing ones: the phrasing reads one after a mark as closing, and the display copy sets one after a Chinese mark or character as closing. The films' Chinese scripts set typographic quotes, and none holds a straight one.
- [A straight double quote used as an inch mark] → It follows a digit, so it becomes ”, which is how such a film would set it in prose; none of the films uses one.

## Migration Plan

ETHOS v2 adopts 0.8.1 before its render and refreshes its captions; DDWG 1.2.0 keeps 0.5.0, and its captions hold neither case. Rollback is the previous pin.

## Open Questions

None.
