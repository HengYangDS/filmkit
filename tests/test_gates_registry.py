"""The engine's gate registry: the sample film's source check is a gate of its own."""

import tomllib
from pathlib import Path

REGISTRY = Path(__file__).resolve().parents[1] / "system/gates.toml"


def gates() -> dict:
    return tomllib.loads(REGISTRY.read_text(encoding="utf-8"))


def test_the_sample_s_sources_are_checked_read_only_by_a_gate_outside_the_proof_sets():
    declared = gates()
    (gate,) = [gate for gate in declared["gates"] if gate["id"] == "sample-sources"]
    assert gate["command"][:4] == ["uv", "run", "--directory", "examples/sample-film"]
    assert gate["command"][-3:] == ["filmkit", "check", "--read-only"]
    assert (gate["writes_files"], gate["network_policy"]) == (False, "offline")
    # A gate joins the proof sets only after its first hosted run passes (task 10.6).
    assert all("sample-sources" not in held for held in declared["proof_sets"].values())
