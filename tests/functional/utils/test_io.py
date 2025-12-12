"""
Functional tests of utils/io.py
"""

from pathlib import Path

import pandas as pd
import pytest

from causaliq_core.utils import is_valid_path
from causaliq_core.utils.io import write_dataframe


# Check invalid arguments raise Exception
def test_fileio_common_is_valid_path_type_error():
    with pytest.raises(TypeError):
        is_valid_path()
    with pytest.raises(TypeError):
        is_valid_path(None)
    with pytest.raises(TypeError):
        is_valid_path(-3)
    with pytest.raises(TypeError):
        is_valid_path(["file.txt"], False)
    with pytest.raises(TypeError):
        is_valid_path("file", is_file=3)


# Check non-existent path raises FileNotFoundError
def test_fileio_common_is_valid_path_value_error1():
    with pytest.raises(FileNotFoundError):
        is_valid_path("doesnotexist")


# Check where path doesn't match is_file argument
def test_fileio_common_is_valid_path_value_error2():
    with pytest.raises(FileNotFoundError):
        is_valid_path(
            "tests/data/functional/utils/io/empty.txt", is_file=False
        )
    with pytest.raises(FileNotFoundError):
        is_valid_path("tests/data/functional/utils/io", is_file=True)


# Check file is found OK
def test_fileio_common_is_valid_path_file_ok():
    assert is_valid_path("tests/data/functional/utils/io/empty.txt") is True


# Check directory is found OK
def test_fileio_common_is_valid_path_dir_ok():
    assert (
        is_valid_path("tests/data/functional/utils/io", is_file=False) is True
    )


# Test write_dataframe with None zero parameter to cover line 72
def test_write_dataframe_zero_none_line72():
    """Specific test to cover line 72:
    zero = zero if zero is not None else 10 ** (-sf)"""
    df = pd.DataFrame(
        {"float_col": [1.123456789, 2.987654321], "str_col": ["x", "y"]}
    )
    output_file = Path("tests/data/functional/utils/io/tmp/test_line_72.csv")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Test with zero=None explicitly - this MUST execute line 72
        # Line 72: zero = zero if zero is not None else 10 ** (-sf)
        # Since zero is None, it should become 10 ** (-3) = 0.001
        write_dataframe(df, str(output_file), sf=3, zero=None, preserve=True)

        # Verify file was created and has expected content
        assert output_file.exists()
        result_df = pd.read_csv(output_file)
        assert len(result_df) == 2
        assert "float_col" in result_df.columns

        # Test again with no zero parameter (defaults to None)
        output_file2 = Path(
            "tests/data/functional/utils/io/tmp/test_line_72_default.csv"
        )
        write_dataframe(df, str(output_file2), sf=6)  # zero defaults to None
        assert output_file2.exists()
        if output_file2.exists():
            output_file2.unlink()

    finally:
        if output_file.exists():
            output_file.unlink()


# Test write_dataframe ValueError for invalid argument values (line 77)
def test_write_dataframe_value_error():
    df = pd.DataFrame({"A": [1, 2]})
    output_file = Path("tests/data/functional/utils/io/tmp/test_error.csv")

    # Test sf < 2 - this should trigger line 77
    with pytest.raises(
        ValueError, match="Bad argument values for write_dataframe"
    ):
        write_dataframe(df, str(output_file), sf=1)

    # Test sf > 10 - this should also trigger line 77
    with pytest.raises(
        ValueError, match="Bad argument values for write_dataframe"
    ):
        write_dataframe(df, str(output_file), sf=11)

    # Test zero < 1e-20 - this should also trigger line 77
    with pytest.raises(
        ValueError, match="Bad argument values for write_dataframe"
    ):
        write_dataframe(df, str(output_file), zero=1e-21)

    # Test zero > 0.1 - this should also trigger line 77
    with pytest.raises(
        ValueError, match="Bad argument values for write_dataframe"
    ):
        write_dataframe(df, str(output_file), zero=0.2)


# Test write_dataframe with float columns (line 82)
def test_write_dataframe_float_columns():
    df = pd.DataFrame(
        {
            "float32_col": pd.Series([1.123456, 2.789012], dtype="float32"),
            "float64_col": pd.Series([3.456789, 4.012345], dtype="float64"),
            "int_col": [1, 2],
            "str_col": ["a", "b"],
        }
    )
    output_file = Path(
        "tests/data/functional/utils/io/tmp/test_float_cols.csv"
    )
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        # This should trigger line 82:
        # if df_to_write[col].dtype in ["float32", "float64"]:
        write_dataframe(df, str(output_file), sf=3)

        # Verify file was created
        assert output_file.exists()

        # Read back and verify float columns were processed
        result_df = pd.read_csv(output_file)
        assert "float32_col" in result_df.columns
        assert "float64_col" in result_df.columns

    finally:
        if output_file.exists():
            output_file.unlink()


# Test write_dataframe TypeError for invalid argument types (line 72)
def test_write_dataframe_type_error():
    """Test that write_dataframe raises TypeError
    for invalid argument types."""
    df = pd.DataFrame({"A": [1, 2]})

    # Test invalid filename (not string)
    with pytest.raises(
        TypeError, match="Bad argument types for write_dataframe"
    ):
        write_dataframe(df, 123)  # filename should be str, not int

    # Test invalid compress (not bool)
    with pytest.raises(
        TypeError, match="Bad argument types for write_dataframe"
    ):
        write_dataframe(
            df, "test.csv", compress="yes"
        )  # compress should be bool, not str

    # Test invalid sf (not int)
    with pytest.raises(
        TypeError, match="Bad argument types for write_dataframe"
    ):
        write_dataframe(df, "test.csv", sf=3.14)  # sf should be int, not float

    # Test invalid sf (bool counts as int but should be excluded)
    with pytest.raises(
        TypeError, match="Bad argument types for write_dataframe"
    ):
        write_dataframe(df, "test.csv", sf=True)  # sf should be int, not bool

    # Test invalid zero (not float when not None)
    with pytest.raises(
        TypeError, match="Bad argument types for write_dataframe"
    ):
        write_dataframe(
            df, "test.csv", zero="0.001"
        )  # zero should be float, not str

    # Test invalid preserve (not bool)
    with pytest.raises(
        TypeError, match="Bad argument types for write_dataframe"
    ):
        write_dataframe(
            df, "test.csv", preserve=1
        )  # preserve should be bool, not int
