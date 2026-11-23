/* The sample film as a delivery binding names it (`filmkit.delivery.folder.bound_film`): its file prefix, each
 * edition's runtime, and its editions in the declared order, each with its code, its language's tag and its members. */
const members = (slug, code) => [
  `${slug}-${code}-uhd.mp4`,
  `${slug}-${code}-1080p-captioned.mp4`,
  `${slug}-${code}-uhd-uncaptioned.mp4`,
  `${slug}-${code}-1080p-uncaptioned.mp4`,
  `${slug}-cover.png`,
  `${slug}-cover.jpg`,
  `${slug}-${code}.srt`,
  `${slug}-${code}.vtt`,
  `${slug}-${code}-transcript.md`,
  "chapters.json",
  "chapters.ffmeta",
  "index.html",
];

/* A bound film of the given editions, each as [code, tag, runtime]. */
export const boundFilm = (slug, editions) => ({
  slug,
  runtimes: Object.fromEntries(editions.map(([code, , runtime]) => [code, runtime])),
  editions: editions.map(([code, tag]) => ({ code, tag, members: members(slug, code) })),
});

export const SAMPLE_FILM = boundFilm("sample-reel", [
  ["zh", "zh-CN", 1636],
  ["en", "en", 1476],
]);
