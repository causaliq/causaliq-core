#
#   Functional tests for XDSL format BN discrete network I/O operations
#

from pathlib import Path
from random import random

import pytest

from causaliq_core.bn import read_bn, write_bn

TESTDATA_DIR = Path("tests/data/functional/bn")
TMP_DIR = Path(__file__).parent.parent / "data" / "functional" / "bn" / "tmp"


@pytest.fixture(scope="function")
def tmpfile():
    """Temporary XDSL file fixture, automatically cleaned up."""
    _tmpfile = TMP_DIR / f"{int(random() * 10000000)}.xdsl"
    yield str(_tmpfile)
    if _tmpfile.exists():
        _tmpfile.unlink()


# Test read_bn successfully reads simple AB network from XDSL
def test_read_bn_ab_success():
    bn_xdsl = read_bn(str(TESTDATA_DIR / "xdsl" / "ab.xdsl"))
    bn_dsc = read_bn(str(TESTDATA_DIR / "dsc" / "ab.dsc"))
    assert bn_xdsl == bn_dsc


# Test read_bn successfully reads A_B_C network from XDSL
def test_read_bn_a_b_c_success():
    bn_xdsl = read_bn(str(TESTDATA_DIR / "xdsl" / "a_b_c.xdsl"))
    bn_dsc = read_bn(str(TESTDATA_DIR / "discrete" / "tiny" / "a_b_c.dsc"))
    assert bn_xdsl == bn_dsc


# Test read_bn successfully reads ABC network from XDSL
def test_read_bn_abc_success():
    bn_xdsl = read_bn(str(TESTDATA_DIR / "xdsl" / "abc.xdsl"))
    bn_dsc = read_bn(str(TESTDATA_DIR / "discrete" / "tiny" / "abc.dsc"))
    assert bn_xdsl == bn_dsc


# Test read_bn successfully reads AB_CB network from XDSL
def test_read_bn_ab_cb_success():
    bn_xdsl = read_bn(str(TESTDATA_DIR / "xdsl" / "ab_cb.xdsl"))
    bn_dsc = read_bn(str(TESTDATA_DIR / "discrete" / "tiny" / "ab_cb.dsc"))
    assert bn_xdsl == bn_dsc


# Test read_bn successfully reads AND4_10 network from XDSL
def test_read_bn_and4_10_success():
    bn_xdsl = read_bn(str(TESTDATA_DIR / "xdsl" / "and4_10.xdsl"))
    bn_dsc = read_bn(str(TESTDATA_DIR / "discrete" / "tiny" / "and4_10.dsc"))
    assert bn_xdsl == bn_dsc


# Test read_bn successfully reads Cancer network from XDSL
def test_read_bn_cancer_success():
    bn_xdsl = read_bn(str(TESTDATA_DIR / "xdsl" / "cancer.xdsl"))
    bn_dsc = read_bn(str(TESTDATA_DIR / "discrete" / "small" / "cancer.dsc"))
    assert bn_xdsl == bn_dsc


# Test read_bn successfully reads Asia network from XDSL
def test_read_bn_asia_success():
    bn_xdsl = read_bn(str(TESTDATA_DIR / "xdsl" / "asia.xdsl"))
    bn_dsc = read_bn(str(TESTDATA_DIR / "asia" / "asia.dsc"))
    assert bn_xdsl == bn_dsc


# Test read_bn successfully reads Sports network from XDSL
def test_read_bn_sports_success():
    bn = read_bn(str(TESTDATA_DIR / "xdsl" / "sports.xdsl"))
    assert bn.free_params == 1049
    assert [
        "ATgoals",
        "ATshots",
        "ATshotsOnTarget",
        "HDA",
        "HTgoals",
        "HTshotOnTarget",
        "HTshots",
        "RDlevel",
        "possession",
    ] == bn.dag.nodes
    assert {
        ("RDlevel", "HTgoals"),
        ("RDlevel", "HTshotOnTarget"),
        ("RDlevel", "HTshots"),
        ("RDlevel", "possession"),
        ("RDlevel", "ATshots"),
        ("RDlevel", "ATshotsOnTarget"),
        ("RDlevel", "ATgoals"),
        ("possession", "HTshots"),
        ("possession", "ATshots"),
        ("HTshots", "HTshotOnTarget"),
        ("ATshots", "ATshotsOnTarget"),
        ("HTshotOnTarget", "HTgoals"),
        ("ATshotsOnTarget", "ATgoals"),
        ("HTgoals", "HDA"),
        ("ATgoals", "HDA"),
    } == set(bn.dag.edges)
    assert bn.cnds["HDA"].cdist({"HTgoals": "x_", "ATgoals": "x_"}) == {
        "H": 0.3234421364985163,
        "D": 0.5014836795252225,
        "A": 0.1750741839762611,
    }


# Test read_bn successfully reads Heart Disease network from XDSL
def test_read_bn_heartdisease_success():
    bn = read_bn(str(TESTDATA_DIR / "xdsl" / "heartdisease.xdsl"))
    assert bn.dag.nodes == [
        "Angina",
        "Atherosclerosis",
        "Diet",
        "ECG",
        "Exercise",
        "Family_History",
        "Heart_Attack",
        "Heart_Disease",
        "High_blood_pressure",
        "High_cholestrol_level",
        "High_triglyceride_levels",
        "Low_protein_concentration",
        "Obesity",
        "Smoking",
        "Stroke",
    ]
    assert set(bn.dag.edges) == {
        ("Exercise", "Obesity"),
        ("High_cholestrol_level", "Atherosclerosis"),
        ("High_blood_pressure", "Heart_Disease"),
        ("Heart_Disease", "Heart_Attack"),
        ("Exercise", "Atherosclerosis"),
        ("Diet", "Obesity"),
        ("Heart_Disease", "ECG"),
        ("Obesity", "High_blood_pressure"),
        ("Diet", "High_triglyceride_levels"),
        ("Heart_Disease", "Stroke"),
        ("Atherosclerosis", "Heart_Disease"),
        ("Smoking", "High_blood_pressure"),
        ("Heart_Disease", "Angina"),
        ("Family_History", "Heart_Disease"),
        ("Diet", "High_cholestrol_level"),
        ("Diet", "Low_protein_concentration"),
        ("Exercise", "High_blood_pressure"),
        ("Low_protein_concentration", "Heart_Disease"),
        ("High_triglyceride_levels", "Atherosclerosis"),
    }


# Test read_bn successfully reads Property network from XDSL
def test_read_bn_property_success():
    bn = read_bn(str(TESTDATA_DIR / "xdsl" / "property.xdsl"))
    assert bn.free_params == 3056
    assert (
        sorted(
            [
                "propertyManagement",
                "otherPropertyExpenses",
                "rentalIncomeLoss",
                "rentalIncome",
                "propertyPurchaseValue",
                "propertyExpensesGrowth",
                "rentalGrowth",
                "capitalGrowth",
                "incomeTax",
                "interestRate",
                "borrowing",
                "otherInterestFees",
                "actualRentalIncome",
                "rentalGrossYield",
                "rentalIncomeT1",
                "LTV",
                "stampDutyTaxBand",
                "stampDutyTax",
                "capitalGains",
                "otherPropertyExpensesT1",
                "interest",
                "propertyExpenses",
                "rentalGrossProfit",
                "rentalNetProfitBeforeInterest",
                "propertyValueT1",
                "interestTaxRelief",
                "netProfit",
            ]
        )
        == bn.dag.nodes
    )


# Test read_bn successfully reads Formed network from XDSL
def test_read_bn_formed_success():
    bn = read_bn(str(TESTDATA_DIR / "xdsl" / "formed.xdsl"), correct=True)
    assert len(bn.dag.nodes) == 88
    assert len(bn.dag.edges) == 138
    assert bn.free_params == 910


# Test read_bn successfully reads COVID network from XDSL
def test_read_bn_covid_success():
    bn = read_bn(
        str(TESTDATA_DIR / "xdsl" / "covid_knowledge_k-means.xdsl"),
        correct=True,
    )
    assert len(bn.dag.nodes) == 17
    assert len(bn.dag.edges) == 37
    assert bn.free_params == 7834


# Test write_bn fails when writing to non-existent directory
def test_write_bn_nonexistent_directory():
    bn = read_bn(str(TESTDATA_DIR / "dsc" / "ab.dsc"))
    with pytest.raises(FileNotFoundError):
        write_bn(bn, str(TESTDATA_DIR / "nonexistent" / "ab.xdsl"))


# Test write_bn successfully writes and reads back AB network
def test_write_bn_ab_roundtrip(tmpfile):
    from causaliq_core.bn.io import xdsl

    bn = read_bn(str(TESTDATA_DIR / "dsc" / "ab.dsc"))
    xdsl.write(bn, tmpfile, genie=False)  # Use genie=False for exact roundtrip
    bn_xdsl = read_bn(tmpfile)
    assert bn == bn_xdsl


# Test write_bn successfully writes ABC network and reads back
def test_write_bn_abc_roundtrip(tmpfile):
    from causaliq_core.bn.io import xdsl

    bn = read_bn(str(TESTDATA_DIR / "dsc" / "abc.dsc"))
    xdsl.write(bn, tmpfile, genie=False)  # Use genie=False for exact roundtrip
    bn_xdsl = read_bn(tmpfile)
    assert bn == bn_xdsl


# Test write_bn successfully writes AB_CB network and reads back
def test_write_bn_ab_cb_roundtrip(tmpfile):
    from causaliq_core.bn.io import xdsl

    bn = read_bn(str(TESTDATA_DIR / "dsc" / "ab_cb.dsc"))
    xdsl.write(bn, tmpfile, genie=False)  # Use genie=False for exact roundtrip
    bn_xdsl = read_bn(tmpfile)
    assert bn == bn_xdsl


# Test write_bn successfully writes AND4_10 network and reads back
def test_write_bn_and4_10_roundtrip(tmpfile):
    from causaliq_core.bn.io import xdsl

    bn = read_bn(str(TESTDATA_DIR / "discrete" / "tiny" / "and4_10.dsc"))
    xdsl.write(bn, tmpfile, genie=False)  # Use genie=False for exact roundtrip
    bn_xdsl = read_bn(tmpfile)
    assert bn == bn_xdsl


# Test write_bn successfully writes Cancer network and reads back
def test_write_bn_cancer_roundtrip(tmpfile):
    from causaliq_core.bn.io import xdsl

    bn = read_bn(str(TESTDATA_DIR / "discrete" / "small" / "cancer.dsc"))
    xdsl.write(bn, tmpfile, genie=False)  # Use genie=False for exact roundtrip
    bn_xdsl = read_bn(tmpfile)
    assert bn == bn_xdsl

    # Manually check the CPT entries
    cpt = bn_xdsl.cnds["Pollution"]
    assert cpt.cdist() == {"low": 0.9, "high": 0.1}

    cpt = bn_xdsl.cnds["Smoker"]
    assert cpt.cdist() == {"True": 0.3, "False": 0.7}

    cpt = bn_xdsl.cnds["Cancer"]
    assert cpt.cdist({"Pollution": "low", "Smoker": "True"}) == {
        "True": 0.03,
        "False": 0.97,
    }
    assert cpt.cdist({"Pollution": "high", "Smoker": "True"}) == {
        "True": 0.05,
        "False": 0.95,
    }
    assert cpt.cdist({"Pollution": "low", "Smoker": "False"}) == {
        "True": 0.001,
        "False": 0.999,
    }
    assert cpt.cdist({"Pollution": "high", "Smoker": "False"}) == {
        "True": 0.02,
        "False": 0.98,
    }

    cpt = bn_xdsl.cnds["Dyspnoea"]
    assert cpt.cdist({"Cancer": "True"}) == {"True": 0.65, "False": 0.35}
    assert cpt.cdist({"Cancer": "False"}) == {"True": 0.3, "False": 0.7}

    cpt = bn_xdsl.cnds["Xray"]
    assert cpt.cdist({"Cancer": "True"}) == {"positive": 0.9, "negative": 0.1}
    assert cpt.cdist({"Cancer": "False"}) == {"positive": 0.2, "negative": 0.8}


# Test write_bn successfully writes Asia network and reads back
def test_write_bn_asia_roundtrip(tmpfile):
    from causaliq_core.bn.io import xdsl

    bn = read_bn(str(TESTDATA_DIR / "discrete" / "small" / "asia.dsc"))
    xdsl.write(bn, tmpfile, genie=False)  # Use genie=False for exact roundtrip
    bn_xdsl = read_bn(tmpfile)
    assert bn == bn_xdsl
