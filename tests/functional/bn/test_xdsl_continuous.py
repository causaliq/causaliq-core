#
#   Functional tests for XDSL format continuous/linear
#   Gaussian BN I/O operations
#

from pathlib import Path
from random import random

import pytest

from causaliq_core.bn.io import read_bn, write_bn
from tests.functional.fixtures import example_bns as ex_bn

TESTDATA_DIR = Path("tests/data/functional/bn")
TMP_DIR = TESTDATA_DIR / "tmp"


@pytest.fixture(scope="function")
def tmpfile():
    """Temporary XDSL file fixture, automatically cleaned up."""
    _tmpfile = TMP_DIR / f"{int(random() * 10000000)}.xdsl"
    yield str(_tmpfile)
    if _tmpfile.exists():
        _tmpfile.unlink()


# Test read_bn successfully reads simple X continuous network
def test_read_bn_x_success():
    x = read_bn(str(TESTDATA_DIR / "xdsl" / "x.xdsl"))
    assert x.dag.to_string() == "[X]"
    assert x.cnds["X"].__str__() == "Normal(0.0,1.0)"


# Test read_bn successfully reads XY continuous network
def test_read_bn_xy_success():
    xy = read_bn(str(TESTDATA_DIR / "xdsl" / "xy.xdsl"))
    assert xy.dag.to_string() == "[X][Y|X]"
    assert xy.cnds["X"].__str__() == "Normal(2.0,1.0)"
    assert xy.cnds["Y"].__str__() == "1.5*X+Normal(0.5,0.5)"


# Test read_bn successfully reads XYZ continuous network
def test_read_bn_xyz_success():
    xyz = read_bn(str(TESTDATA_DIR / "xdsl" / "xyz.xdsl"))
    assert xyz.dag.to_string() == "[X][Y|X][Z|Y]"
    assert xyz.cnds["X"].__str__() == "Normal(0.0,1.0)"
    assert xyz.cnds["Y"].__str__() == "1.5*X+Normal(0.5,0.5)"
    assert xyz.cnds["Z"].__str__() == "-2.0*Y+Normal(-2.0,0.2)"


# Test read_bn successfully reads XY_ZY continuous network
def test_read_bn_xy_zy_success():
    xy_zy = read_bn(str(TESTDATA_DIR / "xdsl" / "xy_zy.xdsl"))
    assert xy_zy.dag.to_string() == "[X][Y|X:Z][Z]"
    assert xy_zy.cnds["X"].__str__() == "Normal(0.0,1.0)"
    assert xy_zy.cnds["Y"].__str__() == "1.5*X-2.2*Z+Normal(0.5,0.5)"
    assert xy_zy.cnds["Z"].__str__() == "Normal(-2.0,0.2)"


# Test read_bn successfully reads Gauss continuous network
def test_read_bn_gauss_success():
    gauss = read_bn(str(TESTDATA_DIR / "xdsl" / "gauss.xdsl"))
    assert gauss.dag.to_string() == "[A][B][C|A:B][D|B][E][F|A:D:E:G][G]"
    assert gauss.cnds["A"].__str__() == "Normal(1.0,1.0)"
    assert gauss.cnds["B"].__str__() == "Normal(2.0,3.0)"
    assert gauss.cnds["C"].__str__() == "2.0*A+2.0*B+Normal(2.0,0.5)"
    assert gauss.cnds["D"].__str__() == "1.5*B+Normal(6.0,0.33)"
    assert gauss.cnds["E"].__str__() == "Normal(3.5,2.0)"
    assert (
        gauss.cnds["F"].__str__() == "2.0*A+1.0*D+1.0*E+1.5*G+Normal(0.0,1.0)"
    )
    assert gauss.cnds["G"].__str__() == "Normal(5.0,2.0)"


# Test write_bn successfully writes and reads back X continuous network
def test_write_bn_x_roundtrip(tmpfile):
    bn = ex_bn.x()
    write_bn(bn, tmpfile)
    bn_read = read_bn(tmpfile)
    assert bn == bn_read


# Test write_bn successfully writes and reads back XY continuous network
def test_write_bn_xy_roundtrip(tmpfile):
    bn = ex_bn.xy()
    write_bn(bn, tmpfile)
    bn_read = read_bn(tmpfile)
    assert bn == bn_read


# Test write_bn successfully writes and reads back X_Y continuous network
def test_write_bn_x_y_roundtrip(tmpfile):
    bn = ex_bn.x_y()
    write_bn(bn, tmpfile)
    bn_read = read_bn(tmpfile)
    assert bn == bn_read


# Test write_bn successfully writes and reads back XYZ continuous network
def test_write_bn_xyz_roundtrip(tmpfile):
    bn = ex_bn.xyz()
    write_bn(bn, tmpfile)
    bn_read = read_bn(tmpfile)
    assert bn == bn_read


# Test write_bn successfully writes and reads back XY_ZY continuous network
def test_write_bn_xy_zy_roundtrip(tmpfile):
    bn = ex_bn.xy_zy()
    write_bn(bn, tmpfile)
    bn_read = read_bn(tmpfile)
    assert bn == bn_read
