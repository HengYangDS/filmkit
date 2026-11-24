/* The engine's classes of characters, read from scripts.json beside this module, the one file that
 * filmkit.languages reads in Python too. Each class is a script a language writes (`han`, `latin`) or a set of
 * marks named by its purpose; `characterClass(name)` gives its members as the body of a RegExp character class
 * with the `u` flag, and `classTest(name)` a test of one character. A name the file does not hold is refused. */
import { readFileSync } from "node:fs";

const DATA = JSON.parse(readFileSync(new URL("./scripts.json", import.meta.url), "utf8"));
/* Every class by its name, scripts first. */
export const CLASSES = Object.freeze({ ...DATA.scripts, ...DATA.marks });

const escaped = (point) => `\\u{${point.toString(16)}}`;
const member = (range) => {
  const [first, last] = range.split("-").map((hex) => Number.parseInt(hex, 16));
  return first === last ? escaped(first) : `${escaped(first)}-${escaped(last)}`;
};

/* The body of a character class that holds exactly a class's members. */
export function characterClass(name) {
  const entry = CLASSES[name];
  if (!entry) throw new Error(`scripts.json holds no class ${name}`);
  if (entry.of) return entry.of.map(characterClass).join("");
  if (entry.ranges) return entry.ranges.map(member).join("");
  return [...entry.characters].map((ch) => escaped(ch.codePointAt(0))).join("");
}

/* A test of whether one character, or any character of a text, is of a class. */
export function classTest(name) {
  const pattern = new RegExp(`[${characterClass(name)}]`, "u");
  return (text) => pattern.test(text);
}
