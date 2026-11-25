/** How an engine tool ends where it cannot finish (design decision 19 of build-a-film-by-its-verbs).
 *
 * `filmkit.tools.run` loads this module before every tool (`--import` in `NODE_OPTIONS`). An error that nothing
 * catches, a top-level await that rejects, a rejection that nothing handles and a module that throws as it loads then
 * end the tool with status 2, where Node's own end would give 1, the status every tool gives a finding. The engine reads
 * 1 as the tool's refusal, and 2 or a signal as a failure to finish, which no refusal of a gate may stand on. */

/** The status of a tool that could not finish. */
export const UNFINISHED = 2;

/** End the tool, once its error is written, with `UNFINISHED`. */
export function unfinished(error) {
  process.exitCode = UNFINISHED;
  process.stderr.write(`${error?.stack ?? error}\n`, () => process.exit(UNFINISHED));
}

process.on("uncaughtException", unfinished);
