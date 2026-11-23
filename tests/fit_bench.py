"""What the benches of the runtime's count share, in the soundtrack's own tests and in the tests of
the convergence that asks it: the pause contract, and a stand-in for the assembly's count.

The module loads no speech runtime, so a test module that is collected where that runtime does
not load may import it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from filmkit.soundtrack.fit import FITS, MEASURES
from filmkit.soundtrack.pauses import PauseError, mean_preserving_pauses
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


def design_refusal() -> PauseError:
    """The design's own refusal of thought pauses whose floors the declared mean cannot fund."""
    return refusal_of(mean_preserving_pauses, [1], 0.0, 1.0, 1.0)


@dataclass
class Count:
    """A stand-in for the assembly's measure of one policy (`filmkit.soundtrack.fit.measured`).

    The edition's count, the speech with its thought pauses, the designed gaps, the closing quiet
    and the credits, is `counted` seconds at the contract's thought pause, and each second off
    that pause shortens it `joins` times as much, counted in whole samples as the assembly
    counts. The runtime is the count rounded up to the whole second; the gaps take the
    rounding's fraction up to their `room` seconds, and the credits the rest. `undesigned` says
    of a thought pause whether its design is refused, which is asked of its owner. `tried`
    holds the thought pauses that were measured, in order. No count misses a runtime.
    """

    counted: float = 1475.14
    room: float = 2.4
    joins: int = 2
    undesigned: Callable[[float], bool] = lambda _pause: False
    tried: list[float] = field(default_factory=list)

    def measured(
        self, name: str, policy: dict, _releases: object, _bound: object
    ) -> tuple[dict, PauseError | None]:
        pause = policy["pauses"]["thought"]
        self.tried.append(pause)
        if self.undesigned(pause):
            refusal = design_refusal()
            return {"policy": name, **dict.fromkeys(MEASURES), "verdict": str(refusal)}, refusal
        count = round(self.counted * RATE) - self.joins * round((THOUGHT_PAUSE - pause) * RATE)
        runtime = -(-count // RATE)
        fraction = runtime * RATE - count
        gaps = min(fraction, round(self.room * RATE))
        line = {
            "policy": name,
            **dict.fromkeys(MEASURES),
            "runtime_seconds": runtime,
            "free_seconds": gaps / RATE,
            "credits_free_seconds": (fraction - gaps) / RATE,
            "verdict": FITS,
        }
        return line, None
