/** A stage's frame contract: its picture's width, height, seconds and frames a second, as the stage's record states
 * them. `filmkit.picture.rendering.stage_picture` writes the record, `stage.json`, beside the page it stages. The page
 * sizes itself by three attributes of its own and states no rate, so a tool that opens the page takes the frame here,
 * and a stage whose page states another size or length than its record is refused: a restaging that was cut short
 * leaves the two apart. This module imports no browser, so the contract can be read where none is installed. */
import { readFile } from "node:fs/promises";
import { join } from "node:path";

export const RECORD = "stage.json";
export const PAGE = "index.html";
const FRAME = ["width", "height", "duration", "fps"];
const AGAIN = "run stage-picture again";

/** A stage that states no frame, or two: its message names the file, what is wrong with it and the repair. */
export class StageError extends Error {}

async function held(path, what) {
  try {
    return await readFile(path, "utf8");
  } catch (error) {
    const why =
      error.code === "ENOENT" ? "is absent" : `cannot be read (${error.code ?? error.message})`;
    throw new StageError(`The stage's ${what} ${path} ${why}; ${AGAIN}`);
  }
}

/** The stage's width, height, seconds and frames a second, each a whole positive number of its record, with which
 * the page's own width, height and seconds agree. Throws `StageError` otherwise. */
export async function frameContract(workspace) {
  const path = join(workspace, RECORD);
  let record = null;
  try {
    record = JSON.parse(await held(path, "record"));
  } catch (error) {
    if (error instanceof StageError) throw error;
    throw new StageError(`The stage's record ${path} holds no JSON (${error.message}); ${AGAIN}`);
  }
  const lacking = FRAME.filter((name) => !(Number.isInteger(record?.[name]) && record[name] > 0));
  if (lacking.length)
    throw new StageError(
      `The stage's record ${path} states no whole positive ${lacking.join(", ")}; ${AGAIN}`,
    );
  // The page's own statement is the film element's: the stylesheet and the picture's data stand in the page's text
  // too, and a figure there is none of the frame's.
  const entry = join(workspace, PAGE);
  const film = (await held(entry, "page")).match(/<[a-z]+\b[^>]*\bid="film"[^>]*>/)?.[0];
  if (film === undefined)
    throw new StageError(`The stage's page ${entry} holds no film element; ${AGAIN}`);
  for (const name of FRAME.slice(0, 3)) {
    const stated = film.match(new RegExp(`\\bdata-${name}="([^"]*)"`))?.[1];
    if (Number(stated) !== record[name]) {
      const said = stated === undefined ? `no ${name}` : `a ${name} of ${stated}`;
      throw new StageError(
        `The stage's page ${entry} states ${said} where its record states ${record[name]}; ${AGAIN}`,
      );
    }
  }
  return FRAME.map((name) => record[name]);
}
