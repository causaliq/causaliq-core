"""
Functional tests of r/convert.py datafile writing
"""

import numpy as np
import pandas as pd
import pytest

from causaliq_core.r.convert import write_r_datafile


# Check a CSV datafile is created with the expected header.
def test_write_r_datafile_creates_csv(tmp_path):
    path = tmp_path / "data.csv"
    sample = np.array([[0, 1], [1, 0]], dtype="uint8")
    write_r_datafile(sample, ["A", "B"], str(path))
    assert path.is_file()
    assert path.read_text().splitlines()[0] == "A,B"


# Check written values round-trip through pandas unchanged.
def test_write_r_datafile_values_round_trip(tmp_path):
    path = tmp_path / "data.csv"
    sample = np.array([[1.5, 0.25], [2.5, 0.5]], dtype="float32")
    write_r_datafile(sample, ["A", "B"], str(path))
    frame = pd.read_csv(path)
    assert list(frame.columns) == ["A", "B"]
    assert frame["A"].tolist() == [1.5, 2.5]


# Check every sample row is written to the file.
def test_write_r_datafile_writes_all_rows(tmp_path):
    path = tmp_path / "data.csv"
    write_r_datafile(np.zeros((7, 1), dtype="uint8"), ["A"], str(path))
    assert len(pd.read_csv(path)) == 7


# Check column names with spaces are preserved verbatim.
def test_write_r_datafile_preserves_column_names(tmp_path):
    path = tmp_path / "data.csv"
    write_r_datafile(np.zeros((3, 1), dtype="uint8"), ["a b"], str(path))
    assert pd.read_csv(path).columns.tolist() == ["a b"]


# Check mismatched column count raises ValueError.
def test_write_r_datafile_column_mismatch_raises(tmp_path):
    path = tmp_path / "data.csv"
    with pytest.raises(ValueError):
        write_r_datafile(np.zeros((3, 2), dtype="uint8"), ["A"], str(path))
