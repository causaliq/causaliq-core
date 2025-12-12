#
#   Functional tests for XDSL format BN read error handling
#

from pathlib import Path

import pytest

from causaliq_core.bn.io import read_bn
from causaliq_core.utils import FileFormatError

TESTDATA_DIR = Path("tests/data/functional/bn")


# Test read_bn with missing input argument
def test_read_bn_missing_argument():
    with pytest.raises(TypeError):
        read_bn()


# Test read_bn with incorrect argument types
def test_read_bn_type_errors():
    with pytest.raises(TypeError):
        read_bn(1)
    with pytest.raises(TypeError):
        read_bn(0.7)
    with pytest.raises(TypeError):
        read_bn(False)


# Test read_bn fails on non-existent file
def test_read_bn_nonexistent_file():
    with pytest.raises(FileNotFoundError):
        read_bn("doesnotexist.xdsl")


# Test read_bn with invalid file extension
def test_read_bn_invalid_extension():
    with pytest.raises(ValueError):
        read_bn(str(TESTDATA_DIR / "misc" / "null.sys"))


# Test read_bn with invalid file extension from text file
def test_read_bn_invalid_text_extension():
    with pytest.raises(ValueError):
        read_bn(str(TESTDATA_DIR / "misc" / "empty.txt"))


# Test read_bn fails on non-XML file
def test_read_bn_non_xml_file():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "dsc" / "ab_bad_network1.dsc"))


# Test read_bn fails on invalid XML root
def test_read_bn_invalid_root():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "ab_invalid_root.xdsl"))


# Test read_bn fails on too many top level elements
def test_read_bn_too_many_top_level():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "ab_too_many_top_level.xdsl"))


# Test read_bn fails on no top level elements
def test_read_bn_no_top_level():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "ab_no_top_level.xdsl"))


# Test read_bn fails when first top level is not nodes
def test_read_bn_not_nodes():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "ab_not_nodes.xdsl"))


# Test read_bn fails when second top level is not extensions
def test_read_bn_not_extensions():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "ab_not_extensions.xdsl"))


# Test read_bn fails when nodes contains invalid child
def test_read_bn_not_cpt():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "ab_not_cpt.xdsl"))


# Test read_bn fails when cpt has no id attribute
def test_read_bn_cpt_no_id():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "ab_no_id.xdsl"))


# Test read_bn fails when equation has no id attribute
def test_read_bn_equation_no_id():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "xy_no_id.xdsl"))


# Test read_bn fails when cpt has no state
def test_read_bn_cpt_no_state():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "ab_no_state.xdsl"))


# Test read_bn fails when cpt has only single state
def test_read_bn_cpt_single_state():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "ab_single_state.xdsl"))


# Test read_bn fails when cpt has too many parents
def test_read_bn_cpt_too_many_parents():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "ab_too_many_parents.xdsl"))


# Test read_bn fails when equation has too many parents
def test_read_bn_equation_too_many_parents():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "xy_too_many_parents.xdsl"))


# Test read_bn fails when cpt has no probabilities
def test_read_bn_cpt_no_probabilities():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "ab_no_probabilities.xdsl"))


# Test read_bn fails when equation has no definition
def test_read_bn_equation_no_definition():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "xy_no_definition.xdsl"))


# Test read_bn fails when cpt has too many probabilities
def test_read_bn_cpt_too_many_probabilities():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "ab_too_many_probabilities.xdsl"))


# Test read_bn fails when state has no id
def test_read_bn_state_no_id():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "ab_state_no_id.xdsl"))


# Test read_bn fails when parents element is empty
def test_read_bn_empty_parents():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "ab_empty_parents.xdsl"))


# Test read_bn fails when equation parents element is empty
def test_read_bn_equation_empty_parents():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "xy_empty_parents.xdsl"))


# Test read_bn fails when probabilities element is empty
def test_read_bn_empty_probabilities():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "ab_empty_probabilities.xdsl"))


# Test read_bn fails when definition element is empty
def test_read_bn_empty_definition():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "xy_empty_definition.xdsl"))


# Test read_bn fails when probabilities has too many entries
def test_read_bn_too_many_probabilities_1():
    with pytest.raises(FileFormatError):
        read_bn(
            str(TESTDATA_DIR / "xdsl" / "ab_too_many_probabilities_1.xdsl")
        )


# Test read_bn fails when probabilities has too many entries variant 2
def test_read_bn_too_many_probabilities_2():
    with pytest.raises(FileFormatError):
        read_bn(
            str(TESTDATA_DIR / "xdsl" / "ab_too_many_probabilities_2.xdsl")
        )


# Test read_bn fails when probabilities has too few entries
def test_read_bn_too_few_probabilities_1():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "ab_too_few_probabilities_1.xdsl"))


# Test read_bn fails when probabilities has too few entries variant 2
def test_read_bn_too_few_probabilities_2():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "ab_too_few_probabilities_2.xdsl"))


# Test read_bn fails when definition has no equals sign
def test_read_bn_definition_no_equals():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "xy_definition_no_equals.xdsl"))


# Test read_bn fails when definition has no left hand side
def test_read_bn_definition_no_lhs():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "xy_definition_no_lhs.xdsl"))


# Test read_bn fails when definition has no right hand side
def test_read_bn_definition_no_rhs():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "xy_definition_no_rhs.xdsl"))


# Test read_bn fails when definition has multiple equals signs
def test_read_bn_definition_multiple_equals():
    with pytest.raises(FileFormatError):
        read_bn(
            str(TESTDATA_DIR / "xdsl" / "xy_definition_multiple_equals.xdsl")
        )


# Test read_bn fails when definition LHS node name mismatch
def test_read_bn_definition_lhs_node_mismatch():
    with pytest.raises(FileFormatError):
        read_bn(
            str(TESTDATA_DIR / "xdsl" / "xy_definition_lhs_node_mismatch.xdsl")
        )


# Test read_bn fails when definition has no normal distribution
def test_read_bn_definition_no_normal():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "xy_definition_no_normal.xdsl"))


# Test read_bn fails when definition has multiple normal distributions
def test_read_bn_definition_multiple_normal():
    with pytest.raises(FileFormatError):
        read_bn(
            str(TESTDATA_DIR / "xdsl" / "xy_definition_multiple_normal.xdsl")
        )


# Test read_bn fails when definition has leading plus sign
def test_read_bn_definition_leading_plus():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "xy_definition_leading_plus.xdsl"))


# Test read_bn fails when definition has trailing plus sign
def test_read_bn_definition_trailing_plus():
    with pytest.raises(FileFormatError):
        read_bn(
            str(TESTDATA_DIR / "xdsl" / "xy_definition_trailing_plus.xdsl")
        )


# Test read_bn fails when definition has trailing minus sign (error 30)
def test_read_bn_definition_trailing_minus_30():
    with pytest.raises(FileFormatError):
        read_bn(
            str(TESTDATA_DIR / "xdsl" / "xy_definition_trailing_minus.xdsl")
        )


# Test read_bn fails when definition has trailing minus sign (error 31)
def test_read_bn_definition_trailing_minus_31():
    with pytest.raises(FileFormatError):
        read_bn(
            str(TESTDATA_DIR / "xdsl" / "xy_definition_trailing_minus.xdsl")
        )


# Test read_bn fails when normal distribution has negative standard deviation
def test_read_bn_definition_normal_negative_sd():
    with pytest.raises(FileFormatError):
        read_bn(
            str(TESTDATA_DIR / "xdsl" / "xy_definition_normal_neg_sd.xdsl")
        )


# Test read_bn fails with bad coefficient format 1
def test_read_bn_definition_bad_coeff_1():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "xy_definition_bad_coeff_1.xdsl"))


# Test read_bn fails with bad coefficient format 2
def test_read_bn_definition_bad_coeff_2():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "xy_definition_bad_coeff_2.xdsl"))


# Test read_bn fails with bad coefficient format 3
def test_read_bn_definition_bad_coeff_3():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "xy_definition_bad_coeff_3.xdsl"))


# Test read_bn fails with bad coefficient format 4
def test_read_bn_definition_bad_coeff_4():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "xy_definition_bad_coeff_4.xdsl"))


# Test read_bn fails with bad coefficient format 5
def test_read_bn_definition_bad_coeff_5():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "xy_definition_bad_coeff_5.xdsl"))


# Test read_bn fails with mixed discrete/continuous network (unsupported)
def test_read_bn_mixed_network_unsupported():
    with pytest.raises(FileFormatError):
        read_bn(str(TESTDATA_DIR / "xdsl" / "ax_mixed_unsupported.xdsl"))
