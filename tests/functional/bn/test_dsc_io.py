#
#   Functional tests for DSC format BN file I/O operations
#

from pathlib import Path
from random import random

import pytest

from causaliq_core.bn import BN, read_bn, write_bn
from causaliq_core.utils import FileFormatError

# Use proper testdata directory structure
TESTDATA_DIR = Path("tests/data/functional/bn")
TMP_DIR = TESTDATA_DIR / "tmp"


@pytest.fixture(scope="function")
def tmpfile():
    """Temporary DSC file fixture, automatically cleaned up."""
    _tmpfile = TMP_DIR / f"{int(random() * 10000000)}.dsc"
    yield str(_tmpfile)
    if _tmpfile.exists():
        _tmpfile.unlink()


# Test read_bn with missing input argument
def test_read_bn_missing_argument():
    with pytest.raises(TypeError):
        read_bn()


# Test read_bn with incorrect argument types
def test_read_bn_incorrect_types():
    with pytest.raises(TypeError):
        read_bn(1)
    with pytest.raises(TypeError):
        read_bn(0.7)
    with pytest.raises(TypeError):
        read_bn(False)


# Test read_bn with non-existent file
def test_read_bn_nonexistent_file():
    with pytest.raises(FileNotFoundError):
        read_bn("doesnotexist.dsc")


# Test read_bn with binary file
def test_read_bn_binary_file():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "misc" / "null.sys.dsc"))


# Test read_bn with empty file
def test_read_bn_empty_file():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "dsc" / "empty.dsc"))


# Test read_bn with network line format errors
def test_read_bn_network_format_errors():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "dsc" / "ab_bad_network1.dsc"))
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "dsc" / "ab_bad_network2.dsc"))
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "dsc" / "ab_missing_network.dsc"))
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "dsc" / "ab_duplicate_network.dsc"))
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "dsc" / "ab_missplaced_network.dsc"))


# Test read_bn with missing node section
def test_read_bn_missing_node_section():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "dsc" / "ab_only_network.dsc"))


# Test read_bn with node section format errors
def test_read_bn_node_section_errors():
    with pytest.raises(FileFormatError):
        read_bn(f"{TESTDATA_DIR}/dsc/ab_bad_node1.dsc")
    with pytest.raises(FileFormatError):
        read_bn(f"{TESTDATA_DIR}/dsc/ab_duplicate_node.dsc")
    with pytest.raises(FileFormatError):
        read_bn(f"{TESTDATA_DIR}/dsc/ab_bad_type1.dsc")
    with pytest.raises(FileFormatError):
        read_bn(f"{TESTDATA_DIR}/dsc/ab_bad_type2.dsc")
    with pytest.raises(FileFormatError):
        read_bn(f"{TESTDATA_DIR}/dsc/ab_bad_type3.dsc")
    with pytest.raises(FileFormatError):
        read_bn(f"{TESTDATA_DIR}/dsc/ab_bad_node_value1.dsc")
    with pytest.raises(FileFormatError):
        read_bn(f"{TESTDATA_DIR}/dsc/ab_duplicate_node_value.dsc")
    with pytest.raises(FileFormatError):
        read_bn(f"{TESTDATA_DIR}/dsc/ab_node_bad_num_values.dsc")


# Test read_bn with probability node errors
def test_read_bn_probability_node_errors():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "dsc" / "ab_bad_prob_node.dsc"))


# Test read_bn with conditional probability node errors
def test_read_bn_conditional_prob_node_errors():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "dsc" / "ab_bad_prob_cond_node1.dsc"))
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "dsc" / "ab_bad_prob_cond_node2.dsc"))


# Test read_bn with probability value errors
def test_read_bn_probability_value_errors():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "dsc" / "ab_bad_prob1.dsc"))
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "dsc" / "ab_bad_prob2.dsc"))
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "dsc" / "ab_bad_prob3.dsc"))


# Test read_bn with conditional probability value errors
def test_read_bn_conditional_probability_errors():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "dsc" / "ab_bad_cond_prob1.dsc"))
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "dsc" / "ab_bad_cond_prob2.dsc"))
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "dsc" / "ab_bad_cond_prob3.dsc"))
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "dsc" / "ab_bad_cond_prob4.dsc"))
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "dsc" / "ab_bad_cond_prob5.dsc"))
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "dsc" / "ab_bad_cond_prob6.dsc"))
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "dsc" / "ab_bad_cond_prob7.dsc"))
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "dsc" / "ab_bad_cond_prob8.dsc"))


# Test read_bn successfully reads simple AB network
def test_read_bn_ab_success():
    bn = read_bn(str(TESTDATA_DIR / "dsc" / "ab.dsc"))
    assert isinstance(bn, BN)
    assert bn.free_params == 3


# Test read_bn successfully reads Cancer network
def test_read_bn_cancer_success():
    bn = read_bn(str(TESTDATA_DIR / "cancer" / "cancer.dsc"))
    assert isinstance(bn, BN)
    assert bn.free_params == 10


# Test read_bn successfully reads Asia network
def test_read_bn_asia_success():
    bn = read_bn(str(TESTDATA_DIR / "asia" / "asia.dsc"))
    assert isinstance(bn, BN)
    assert bn.free_params == 18


# Test read_bn successfully reads Alarm network
def test_read_bn_alarm_success():
    bn = read_bn(str(TESTDATA_DIR / "alarm" / "alarm.dsc"))
    assert isinstance(bn, BN)
    assert bn.free_params == 509


# Test read_bn successfully reads Pathfinder network
def test_read_bn_pathfinder_success():
    bn = read_bn(str(TESTDATA_DIR / "pathfinder" / "pathfinder.dsc"))
    assert isinstance(bn, BN)
    assert bn.free_params == 72079


# Test write_bn fails when writing to non-existent directory
def test_write_bn_nonexistent_directory():
    bn = read_bn(str(TESTDATA_DIR / "dsc" / "ab.dsc"))
    with pytest.raises(FileNotFoundError):
        write_bn(bn, str(TESTDATA_DIR / "nonexistent" / "ab.dsc"))


# Test write_bn successfully writes and reads back AB network
def test_write_bn_ab_roundtrip(tmpfile):
    bn = read_bn(str(TESTDATA_DIR / "dsc" / "ab.dsc"))
    write_bn(bn, tmpfile)
    bn_check = read_bn(tmpfile)
    assert bn == bn_check


# Test write_bn successfully writes and reads back Cancer network
def test_write_bn_cancer_roundtrip(tmpfile):
    bn = read_bn(str(TESTDATA_DIR / "cancer" / "cancer.dsc"))
    write_bn(bn, tmpfile)
    bn_check = read_bn(tmpfile)
    assert bn == bn_check


# Test write_bn successfully writes and reads back Asia network
def test_write_bn_asia_roundtrip(tmpfile):
    bn = read_bn(str(TESTDATA_DIR / "asia" / "asia.dsc"))
    write_bn(bn, tmpfile)
    bn_check = read_bn(tmpfile)
    assert bn == bn_check


# Test write_bn successfully writes and reads back Alarm network
def test_write_bn_alarm_roundtrip(tmpfile):
    bn = read_bn(str(TESTDATA_DIR / "alarm" / "alarm.dsc"))
    write_bn(bn, tmpfile)
    bn_check = read_bn(tmpfile)
    assert bn == bn_check


# Test write_bn successfully writes and reads back Pathfinder network
def test_write_bn_pathfinder_roundtrip(tmpfile):
    bn = read_bn(str(TESTDATA_DIR / "pathfinder" / "pathfinder.dsc"))
    write_bn(bn, tmpfile)
    bn_check = read_bn(tmpfile)
    assert bn == bn_check
