"""What the benches of the runtime fit share, in the soundtrack's own tests and in the tests of the
convergence that asks it: the pause contract, and a stand-in for the assembly's count.

The module loads no speech runtime, so a test module that is collected where that runtime does
not load may import it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from filmkit.soundtrack.pauses import PauseError, allocate_designed_gaps, mean_preserving_pauses
from filmkit.specification import RATE

if TYPE_CHECKING:
    from collections.abc import Callable

# A complete pause contract.
PERFORMANCE = {
    "assembly_mode": "native-speech-designed-pauses",
    "designed_pauses": {
        "thought": 0.45,
        "question": 0.7,
        "opening": 3.0,
        "paragraph": 1.6,
        "chapter": 3.4,
        "closing": 2.6,
    },
    "designed_pause_limits": {"opening": 9.0, "paragraph": 5.5, "chapter": 9.0},
    "designed_pause_weights": {"opening": 2.0, "paragraph": 1.0, "chapter": 2.5},
    "tail_guard_seconds": 0.3,
    "thought_pause_range": [0.3, 0.6],
    "paragraph_pause_range": [1.2, 2.0],
}
# The thought pause that the contract declares.
THOUGHT_PAUSE = PERFORMANCE["designed_pauses"]["thought"]


def refusal_of(ask: Callable[..., object], *arguments: object) -> PauseError:
    """The refusal that an owner of the count raises when it is asked so, in its own words."""
    try:
        ask(*arguments)
    except PauseError as refusal:
        return refusal
    message = f"{ask.__name__} refuses nothing when it is asked so"
    raise AssertionError(message)


def runtime_refusal(frames: int) -> PauseError:
    """The allocation's own refusal of a narration that is `frames` samples over the runtime."""
    nothing = {"pauses": {"closing": 0.0}, "limits": {}, "weights": {}}
    return refusal_of(allocate_designed_gaps, [], frames, nothing, RATE, 0)


def design_refusal() -> PauseError:
    """The design's own refusal of thought pauses whose floors the declared mean cannot fund."""
    return refusal_of(mean_preserving_pauses, [1], 0.0, 1.0, 1.0)


@dataclass
class Count:
    """A stand-in for the assembly's measure of one policy (`filmkit.soundtrack.fit.measured`).

    The contract's thought pause leaves `free` seconds free, and each second off it frees
    `joins` times as much, counted in whole samples as the assembly counts. `refusal` is what
    the allocation refuses an edition with that has room, and `undesigned` says of a thought
    pause whether its design is refused. A refusal for the runtime and one of the design are
    asked of their owners. `tried` holds the thought pauses that were measured, in order.
    """

    free: float = 0.8
    joins: int = 2
    refusal: str | None = None
    undesigned: Callable[[float], bool] = lambda _pause: False
    tried: list[float] = field(default_factory=list)

    def measured(
        self, name: str, policy: dict, _releases: object, _bound: object
    ) -> tuple[dict, PauseError | None]:
        pause = policy["pauses"]["thought"]
        self.tried.append(pause)
        if self.undesigned(pause):
            refusal = design_refusal()
            return {"policy": name, "free_seconds": None, "verdict": str(refusal)}, refusal
        frames = round(self.free * RATE) + self.joins * round((THOUGHT_PAUSE - pause) * RATE)
        if frames < 0:
            refusal = runtime_refusal(-frames)
        else:
            refusal = PauseError(self.refusal) if self.refusal else None
        verdict = "fits" if refusal is None else str(refusal)
        return {"policy": name, "free_seconds": frames / RATE, "verdict": verdict}, refusal
