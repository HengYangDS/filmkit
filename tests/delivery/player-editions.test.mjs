/** The player's verdict on its language links for a film of any number of editions: each other edition's player, in
 * the declared order, then the entry page. */
import test from "node:test";
import assert from "node:assert/strict";

import { playerProblems } from "../../src/filmkit/delivery/player-verdict.mjs";

/* What the verdict reads of an edition to judge its links alone: its code, the film's editions and its file prefix. */
const ZH = { code: "zh", codes: ["zh", "en"], slug: "sample-reel" };

test("a player of a film of three editions is judged by its links to the two others, in order", () => {
  const three = { ...ZH, codes: ["zh", "en", "xb"] };
  const links = ["../en/index.html", "../xb/index.html", "../index.html"];
  assert.deepEqual(playerProblems({ language_links: links }, three), []);
  assert.deepEqual(playerProblems({ language_links: [links[1], links[0], links[2]] }, three), [
    "the language links do not lead to every other edition's player and the entry page",
  ]);
  assert.deepEqual(
    playerProblems({ language_links: ["../index.html"] }, { ...ZH, codes: ["zh"] }),
    [],
  );
});
