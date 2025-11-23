"""
Test random number utilities for CausalIQ Core.

Tests for stable, repeatable random number sequences and RandomIntegers class.
"""

from pathlib import Path

import pytest

from causaliq_core.utils.random import (
    STABLE_RANDOM_SEQUENCE,
    RandomIntegers,
    Randomise,
    generate_stable_random,
    init_stable_random,
    random_generator,
    set_random_seed,
    stable_random,
)

# Path to test data
TEST_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "experiments"
TEST_STABLE_RANDOM_FILE = TEST_DATA_DIR / "stable_random.dat"


@pytest.fixture
def test_sequence():
    """Returns the 5-element test sequence from test data file."""
    with open(TEST_STABLE_RANDOM_FILE, "r") as file:
        sequence = file.readlines()
    return [float(i.strip()) for i in sequence]


@pytest.fixture
def mock_stable_sequence(test_sequence, monkeypatch):
    """Mock embedded sequence to use test data for testing offset behavior."""
    monkeypatch.setattr(
        "causaliq_core.utils.random.STABLE_RANDOM_SEQUENCE", test_sequence
    )
    return test_sequence


# Test Randomise enum


def test_randomise_enum_values():
    """Test that Randomise enum contains expected values."""
    assert Randomise.ORDER.value == "order"
    assert Randomise.NAMES.value == "names"
    assert Randomise.KNOWLEDGE.value == "knowledge"
    assert Randomise.ROWS.value == "rows"
    assert Randomise.SAMPLE.value == "sample"


# Test stable random number sequences


def test_stable_random_2_ok(mock_stable_sequence):
    """Check init_stable_random resets properly."""
    test_sequence = mock_stable_sequence
    N = 5

    # Get random numbers one at a time checking they are the ones expected
    init_stable_random()
    for i in range(N):
        assert stable_random() == test_sequence[i]

    # Reset random number cache and check get same sequence again
    init_stable_random()
    for i in range(N):
        assert stable_random() == test_sequence[i]

    # After getting all numbers from sequence, next call should raise
    # StopIteration
    with pytest.raises(StopIteration):
        stable_random()


def test_stable_random_3_ok(mock_stable_sequence):
    """Check different sequence with offset 1."""
    test_sequence = mock_stable_sequence
    N = 5

    # Retrieve and check sequence with offset 0
    init_stable_random()
    for i in range(N):
        assert stable_random() == test_sequence[i]

    with pytest.raises(StopIteration):
        stable_random()

    # Reset random number cache with offset 1
    init_stable_random(offset=1)
    assert stable_random() == test_sequence[1]
    assert stable_random() == test_sequence[3]
    assert stable_random() == test_sequence[4]
    assert stable_random() == test_sequence[0]
    assert stable_random() == test_sequence[2]

    with pytest.raises(StopIteration):
        stable_random()


def test_stable_random_4_ok(mock_stable_sequence):
    """Check different sequence with offset 2."""
    test_sequence = mock_stable_sequence
    init_stable_random(offset=2)
    assert stable_random() == test_sequence[2]
    assert stable_random() == test_sequence[4]
    assert stable_random() == test_sequence[0]
    assert stable_random() == test_sequence[3]
    assert stable_random() == test_sequence[1]

    with pytest.raises(StopIteration):
        stable_random()


def test_stable_random_5_ok(mock_stable_sequence):
    """Check different sequence with offset 3."""
    test_sequence = mock_stable_sequence
    init_stable_random(offset=3)
    assert stable_random() == test_sequence[3]
    assert stable_random() == test_sequence[0]
    assert stable_random() == test_sequence[4]
    assert stable_random() == test_sequence[2]
    assert stable_random() == test_sequence[1]

    with pytest.raises(StopIteration):
        stable_random()


def test_stable_random_6_ok(mock_stable_sequence):
    """Check different sequence with offset 4."""
    test_sequence = mock_stable_sequence
    init_stable_random(offset=4)
    assert stable_random() == test_sequence[4]
    assert stable_random() == test_sequence[2]
    assert stable_random() == test_sequence[0]
    assert stable_random() == test_sequence[1]
    assert stable_random() == test_sequence[3]

    with pytest.raises(StopIteration):
        stable_random()


# Test RandomIntegers class


def test_common_random_integers_type_error_1():
    """Test TypeError when no arguments provided."""
    with pytest.raises(TypeError):
        RandomIntegers()


def test_common_random_integers_type_error_2():
    """Test TypeError for non-integer n."""
    with pytest.raises(TypeError):
        RandomIntegers([4])
    with pytest.raises(TypeError):
        RandomIntegers("invalid")


def test_common_random_integers_type_error_3():
    """Test TypeError for non-integer subsample."""
    with pytest.raises(TypeError):
        RandomIntegers(5, [4])
    with pytest.raises(TypeError):
        RandomIntegers(10, "invalid")


def test_common_random_integers_type_error_4():
    """Test TypeError for non-string path."""
    with pytest.raises(TypeError):
        RandomIntegers(5, path=10)
    with pytest.raises(TypeError):
        RandomIntegers(10, path=["invalid"])


def test_common_random_integers_value_error_1():
    """Test ValueError for invalid n values."""
    with pytest.raises(ValueError):
        RandomIntegers(0)
    with pytest.raises(ValueError):
        RandomIntegers(-1)
    with pytest.raises(ValueError):
        RandomIntegers(1001)


def test_common_random_integers_value_error_2():
    """Test ValueError for invalid subsample values."""
    with pytest.raises(ValueError):
        RandomIntegers(10, -1)
    with pytest.raises(ValueError):
        RandomIntegers(10, 1001)


def test_common_random_integers_1_ok():
    """Test 5 repeatable integers, subsample 0."""
    for j in range(10):
        assert [i for i in RandomIntegers(5)] == [2, 4, 0, 3, 1]


def test_common_random_integers_2_ok():
    """Test 5 repeatable integers, subsample 1."""
    for j in range(10):
        assert [i for i in RandomIntegers(5, 1)] == [4, 1, 0, 2, 3]


def test_common_random_integers_3_ok():
    """Test 5 repeatable integers, subsample 2."""
    for j in range(10):
        assert [i for i in RandomIntegers(5, 2)] == [0, 1, 3, 4, 2]


def test_common_random_integers_4_ok():
    """Test 5 repeatable integers, subsample 3."""
    for j in range(10):
        assert [i for i in RandomIntegers(5, 3)] == [4, 2, 0, 1, 3]


def test_common_random_integers_5_ok():
    """Test 5 repeatable integers, subsample 4."""
    for j in range(10):
        assert [i for i in RandomIntegers(5, 4)] == [1, 0, 2, 4, 3]


def test_common_random_integers_6_ok():
    """Test distribution for two integers is approximately uniform."""
    dist = {}
    for subsample in range(1000):
        order = tuple([i for i in RandomIntegers(2, subsample)])
        if order not in dist:
            dist[order] = 0
        dist[order] += 1

    # Distribution of combinations approximately uniform
    assert dist[(0, 1)] == 507
    assert dist[(1, 0)] == 493


def test_common_random_integers_7_ok():
    """Test distribution for three integers is approximately uniform."""
    dist = {}
    for subsample in range(1000):
        order = tuple([i for i in RandomIntegers(3, subsample)])
        if order not in dist:
            dist[order] = 0
        dist[order] += 1

    # Distribution of combinations approximately uniform
    assert dist[(0, 1, 2)] == 187
    assert dist[(0, 2, 1)] == 152
    assert dist[(1, 0, 2)] == 175
    assert dist[(1, 2, 0)] == 146
    assert dist[(2, 0, 1)] == 174
    assert dist[(2, 1, 0)] == 166


def test_common_random_integers_8_ok():
    """Test first 600 sequences of 8 integers are unique."""
    sequences = set()
    for subsample in range(600):
        order = tuple([i for i in RandomIntegers(8, subsample)])
        assert order not in sequences
        sequences.add(order)


# Test edge cases and additional functionality


def test_stable_random_sequence_length():
    """Test that embedded sequence has expected length."""
    assert len(STABLE_RANDOM_SEQUENCE) == 1000


def test_stable_random_legacy_path_parameter():
    """Test that path parameter is ignored for backward compatibility."""
    init_stable_random()
    # Both calls should return same result regardless of path
    result1 = stable_random()

    init_stable_random()
    result2 = stable_random(path="/some/legacy/path")

    assert result1 == result2


def test_random_integers_legacy_path_parameter():
    """Test path parameter is ignored in RandomIntegers for compatibility."""
    # Both should produce same sequence regardless of path
    seq1 = [i for i in RandomIntegers(5, 0)]
    seq2 = [i for i in RandomIntegers(5, 0, path="/some/legacy/path")]

    assert seq1 == seq2


# Test random generator functions


def test_random_generator():
    """Test that random_generator returns a numpy Generator."""
    from numpy.random import Generator

    gen = random_generator()
    assert isinstance(gen, Generator)


def test_set_random_seed_valid():
    """Test set_random_seed with valid inputs."""
    import numpy as np

    # Test with int seed
    set_random_seed(42)
    gen1 = random_generator()
    val1 = gen1.random()

    # Reset with same seed - should get same value
    set_random_seed(42)
    gen2 = random_generator()
    val2 = gen2.random()

    assert val1 == val2

    # Test with None seed
    set_random_seed(None)
    gen3 = random_generator()
    assert isinstance(gen3, np.random.Generator)


def test_set_random_seed_invalid_type():
    """Test set_random_seed raises TypeError for invalid types."""
    with pytest.raises(
        TypeError, match="set_random_seed called with bad arg type"
    ):
        set_random_seed("invalid")

    with pytest.raises(
        TypeError, match="set_random_seed called with bad arg type"
    ):
        set_random_seed(3.14)

    with pytest.raises(
        TypeError, match="set_random_seed called with bad arg type"
    ):
        set_random_seed([42])


def test_generate_stable_random_valid():
    """Test generate_stable_random with valid inputs."""
    # Test generating partial sequence
    result = generate_stable_random(5)
    assert len(result) == 5
    assert result == STABLE_RANDOM_SEQUENCE[:5]

    # Test generating full sequence
    result_full = generate_stable_random(1000)
    assert len(result_full) == 1000
    assert result_full == STABLE_RANDOM_SEQUENCE

    # Test path parameter is ignored
    result_with_path = generate_stable_random(5, path="/some/path")
    assert result_with_path == result


def test_generate_stable_random_too_large():
    """Test generate_stable_random raises ValueError for N > length."""
    with pytest.raises(
        ValueError, match="Requested 1001 numbers but only 1000 available"
    ):
        generate_stable_random(1001)

    with pytest.raises(
        ValueError, match="Requested 2000 numbers but only 1000 available"
    ):
        generate_stable_random(2000)
