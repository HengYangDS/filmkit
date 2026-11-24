"""The host class of a node's run, measured as host rule 3 measures it."""

import subprocess

import pytest

from filmkit.graph import host


@pytest.mark.parametrize(("cpu", "expected"), [(3.8, "light"), (4.2, "heavy")])
def test_cpu_time_over_wall_time_above_two_cores_is_heavy(cpu, expected):
    measured = host.measured(cpu, 2.0, [])
    assert measured.cpu_per_wall == pytest.approx(cpu / 2.0)
    assert host.host_class(measured, gpu=False, previous=None) == expected


@pytest.mark.parametrize(
    ("samples", "above", "expected"),
    [([150.0, 250.0, 150.0, 250.0], 1, "light"), ([150.0, 250.0, 260.0, 100.0], 2, "heavy")],
)
def test_two_consecutive_samples_above_two_cores_are_heavy(samples, above, expected):
    measured = host.measured(1.0, 10.0, samples)
    assert (measured.samples, measured.above) == (len(samples), above)
    assert host.host_class(measured, gpu=False, previous=None) == expected


def test_model_work_is_gpu_and_heavy_stays_heavy():
    light = host.measured(1.0, 10.0, [])
    assert host.host_class(light, gpu=True, previous=None) == "gpu"
    assert host.host_class(light, gpu=False, previous="heavy") == "heavy"
    assert host.host_class(light, gpu=False, previous="light") == "light"


def test_the_process_tree_is_summed_from_ps():
    listing = "  1     0 50.0\n 10     1 120.5\n 11    10 90.0\n 12     1 300.0\n 13    11  4.5\n"
    assert host.tree_percent(listing, 10) == pytest.approx(215.0)
    assert host.tree_percent(listing, 99) == 0.0


def test_a_short_real_child_is_measured_light_with_no_sample():
    meter = host.start()
    subprocess.run(["nice", "-n", "15", "sleep", "1"], check=True)
    measured = meter.stop()
    assert measured.samples == 0
    assert measured.cpu_per_wall < host.LIGHT_CORES
    assert host.host_class(measured, gpu=False, previous=None) == "light"
