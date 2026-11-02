# Design

## Context

See [proposal.md](proposal.md). The engine refuses a renderer whose installed version differs from `RENDERER_VERSION`. `filmkit.supply` installs the browser build that the locked renderer declares and checks it against `BROWSER_SHA256`. When a cast declares a repetition penalty below the floor of 1.5 that mlx-audio's public generator applies, narration calls mlx-audio's private ICL generator instead. The casts of the films now in production do.

## Goals / Non-Goals

**Goals:**

- Each lock at the newest release its declared ranges admit, mlx-audio and HyperFrames at their newest stable releases, and no advisory from OSV for any locked package.
- A review prompt for every script that the pause policy admits.
- A film owner who narrates through the in-context path learns why its takes lose their endings and what keeps them whole.

**Non-Goals:**

- Changing the speech engine's decode. mlx-audio owns it, and filmkit neither patches nor wraps it.
- Moving any film's pin.

## Decisions

- **Not declared, not an error.** Each optional pause field in the prompt falls back to "not declared", as the inner floors and the breath already do. A script that declares the fields gets the same prompt as before.
- **The non-streaming decode stays.** mlx-audio's streaming decoder applies no length trim. On Chinese takes, though, it differs from the reference decode by a log-spectral distance of 3 to 4.7 dB, which a film's accepted voice would hear. Auditions already reach whole endings under the trim. A take whose own quiet absorbs the trim ends naturally, and a run-on take moves the trim onto the words that are cut away. The narration therefore keeps the reference decode and documents the defect until a release carries the upstream fix.
- **mlx-audio 0.6.4 keeps the takes.** Its non-streaming ICL path differs from 0.6.3 only in the streaming decoder's priming. Seven takes that 0.6.4 narrated from their recorded seeds matched their 0.6.3 recordings byte for byte. A film that moves to 0.6.4 keeps its accepted takes.
- **The renderer follows the newest release.** HyperFrames 0.9.4 and 0.9.5 change three things: how a snapshot handles errors, a capture's refusal when every composition script fails, and how long a scene keeps its WebGL context. The engine renders its 2D compositions with `hyperframes render`, and the sample film is built and verified again before the release.
- **Minor, not patch.** A film that adopts 0.5.0 must raise its own `hyperframes` pin to 0.9.5, and the new renderer can change the frames it renders.
- **Hosted checks precede the tag.** As for 0.4.0, the release head passes both peers' CI on dev and main before `ethos land --release --tag v0.5.0` signs the tag.

## Risks / Trade-offs

- [The new renderer changes a film's frames] → Each film moves its pin only after it builds, compares and accepts an edition.
- [The upstream fix changes the ending of every in-context take] → A release that carries the fix changes the bytes of every take whose reference or own pauses hold id-0 frames. A film therefore adopts it only with a new edition.
- [HyperFrames ships several releases a day] → The next supply recheck moves it again.
