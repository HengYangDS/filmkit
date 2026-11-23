/* English's lead words as its declaration states them (src/filmkit/languages/en.toml), and the wrapping rules an
 * edition's labels are judged by, as the gate writes them (`filmkit.picture.gates.wrapping_rules`). */
import { readFileSync } from "node:fs";

import { WRAPPING } from "../../src/filmkit/picture/frame-audit/typography/breaks.mjs";

const declared = readFileSync(
  new URL("../../src/filmkit/languages/en.toml", import.meta.url),
  "utf8",
);
export const ENGLISH = JSON.parse(
  `[${/^lead_words = \[([\s\S]*?)\]/m.exec(declared)[1].replace(/,\s*$/, "")}]`,
);

/* The rules of an edition whose labels may be written in these languages, each [code, scripts, lead words]. */
export const rulesOf = (languages, shares = {}) => ({
  ...WRAPPING,
  ...shares,
  languages: languages.map(([code, scripts, lead_words]) => ({ code, scripts, lead_words })),
});

/* An English edition's rules, with the film's own lead words added for English. */
export const english = (added = []) => rulesOf([["en", ["latin"], [...ENGLISH, ...added]]]);
