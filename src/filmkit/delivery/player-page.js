/* The player page's behaviour; filmkit.delivery.player inlines this script into each edition's page.
 *
 * A version button and the captions control switch to another film and keep the time and whether the film plays.
 * A switch never loads the chosen film into the video the page shows, which would paint the poster until the film's
 * frame decodes. It makes the chosen film ready in a second video, hidden and transparent after the shown one in the
 * same grid cell, aimed at the shown film's time, or while the film plays a lead ahead of it. Once the second video
 * holds its frame there and a playing film has reached that time, the page shows it over the shown video, plays it if
 * the film played, and two animation frames later gives it the shown video's id, volume and mute and lets the shown
 * video go. A time button plays the shown film from its time, and the hidden track's active cue marks the thought it
 * belongs to as the current paragraph. */
const status = document.getElementById("playback-status");
const versions = [...document.querySelectorAll("[data-captioned]")];
const captions = document.getElementById("captions");
const state = captions.querySelector("span");
const thoughts = [...document.querySelectorAll("#transcript p[data-from]")];
/* How far ahead of a playing film the chosen one is aimed, in seconds of film; how far a playing film may have passed
 * the aim, in seconds, when the chosen one shows its frame there; and for how many animation frames both stay. */
const LEAD = 0.25,
  PASSED = 0.034,
  OVERLAP = 2;
let film = document.getElementById("film");
let version = versions.find((button) => button.getAttribute("aria-pressed") === "true");
let pending = null;
const shown = () => captions.getAttribute("aria-pressed") === "true";
const unplayable = () => {
  status.textContent = status.dataset.unplayable;
};

/* The shown film's active cue marks the thought it belongs to. */
function mark({ target }) {
  const cue = target === film.textTracks[0] && target.activeCues[0];
  if (!cue) return;
  const current = thoughts.findLast((p) => Number(p.dataset.from) <= cue.startTime + 0.002);
  for (const p of thoughts) p.toggleAttribute("aria-current", false);
  current?.setAttribute("aria-current", "true");
}
function watch(video) {
  video.textTracks[0].addEventListener("cuechange", mark);
  video.addEventListener("error", ({ target }) => target === film && unplayable());
}

/* Let a video go: off the page, stopped and without its film. */
function release(video) {
  video.remove();
  video.pause();
  video.replaceChildren();
  video.removeAttribute("src");
  video.load();
}

/* Switch to the chosen film, keeping a frame of the film on the screen throughout. */
function show() {
  pending?.settle();
  const old = film,
    next = old.cloneNode(false);
  for (const name of ["id", "poster", "src"]) next.removeAttribute(name);
  Object.assign(next.style, { visibility: "hidden", background: "transparent" });
  next.append(old.querySelector("track").cloneNode());
  watch(next);
  Object.assign(next, {
    preload: "auto",
    muted: true,
    defaultPlaybackRate: old.defaultPlaybackRate,
  });
  next.src = shown() ? version.dataset.captioned : version.dataset.uncaptioned;
  Object.assign(next, { volume: old.volume, playbackRate: old.playbackRate });
  old.after(next);
  status.textContent = `${version.textContent} · ${captions.textContent}`;
  let lead = LEAD,
    aim = null,
    from = null,
    overlap = -1;
  const still = () => old.paused || old.ended;
  // Aim at the shown film's time, ahead of it while it plays; aim again whenever the shown film moves otherwise.
  const aimAt = (now) => {
    from = { time: old.currentTime, still: still(), at: now };
    aim = Math.min(from.time + (from.still ? 0 : lead * old.playbackRate), next.duration);
    next.currentTime = aim;
  };
  const moved = () =>
    still() !== from.still ||
    (from.still ? old.currentTime !== from.time : old.seeking || old.currentTime < from.time);
  const handOver = () => {
    pending = null;
    const focused = document.activeElement === old;
    Object.assign(next.style, { visibility: "", background: "" });
    old.removeAttribute("id");
    next.id = "film";
    Object.assign(next, { muted: old.muted, volume: old.volume });
    if (document.pictureInPictureElement === old) next.requestPictureInPicture().catch(() => {});
    release(old);
    film = next;
    if (focused) next.focus({ preventScroll: true });
  };
  const reveal = () => {
    next.style.visibility = "";
    if (!still()) next.play().catch(() => {});
    overlap = 0;
  };
  const switching = {
    settle() {
      if (overlap >= 0) return handOver();
      pending = null;
      release(next);
    },
  };
  function step(now) {
    if (pending !== switching) return;
    if (next.error) {
      handOver();
      return unplayable();
    }
    if (overlap >= 0) {
      if (++overlap >= OVERLAP) return handOver();
    } else if (next.readyState >= 1 && (aim === null || moved())) aimAt(now);
    else if (aim !== null && !next.seeking && next.readyState >= 2) {
      if (from.still) reveal();
      else if (old.currentTime > aim + PASSED) {
        // Missed: aim ahead by twice the lead, or by twice what making the film ready took.
        lead = Math.max(2 * lead, (now - from.at) / 500);
        aimAt(now);
      } else if (old.currentTime >= aim - PASSED / 4) reveal();
    }
    requestAnimationFrame(step);
  }
  pending = switching;
  requestAnimationFrame(step);
}

watch(film);
for (const button of versions)
  button.addEventListener("click", () => {
    version = button;
    for (const other of versions) other.setAttribute("aria-pressed", String(other === button));
    show();
  });
captions.addEventListener("click", () => {
  captions.setAttribute("aria-pressed", String(!shown()));
  state.textContent = shown() ? captions.dataset.on : captions.dataset.off;
  show();
});
for (const button of document.querySelectorAll("[data-time]"))
  button.addEventListener("click", () => {
    film.currentTime = Number(button.dataset.time);
    film.play().catch(() => {});
  });
const transcript = document.querySelector("#transcript details");
for (const link of document.querySelectorAll('a[href="#transcript"]'))
  link.addEventListener("click", () => {
    transcript.open = true;
  });
if (location.hash === "#transcript") transcript.open = true;
