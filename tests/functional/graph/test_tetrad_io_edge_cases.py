"""Additional functional tests for tetrad module - edge case coverage."""

from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from causaliq_core.graph.io.tetrad import read
from causaliq_core.utils import FileFormatError

# Path to test data
TEST_DATA_DIR = Path("tests/data/functional/graphs")


# Test read fails on empty file
def test_tetrad_read_fileformat_error_empty_file():
    with patch(
        "causaliq_core.graph.io.tetrad.is_valid_path", return_value=True
    ):
        with patch("builtins.open", mock_open(read_data="")):
            with pytest.raises(FileFormatError, match="is empty"):
                read(str(TEST_DATA_DIR / "empty.tetrad"))


# Test read fails on unicode decode error
def test_tetrad_read_fileformat_error_unicode_decode(monkeypatch):
    def mock_open_unicode_error(*args, **kwargs):
        mock_file = mock_open(read_data="some content")()
        mock_file.__iter__.side_effect = UnicodeDecodeError(
            "utf-8", b"\xff\xfe", 0, 1, "invalid start byte"
        )
        return mock_file

    with patch(
        "causaliq_core.graph.io.tetrad.is_valid_path", return_value=True
    ):
        with patch("builtins.open", mock_open_unicode_error):
            with pytest.raises(FileFormatError, match="not text"):
                read(str(TEST_DATA_DIR / "binary.tetrad"))


# Test read ignores score lines
def test_tetrad_read_ignores_score_lines():
    test_content = """Graph Nodes:
A;B

Graph Edges:
Score: 123.456
1. A --> B
BIC: 789.123
"""
    with patch(
        "causaliq_core.graph.io.tetrad.is_valid_path", return_value=True
    ):
        with patch("builtins.open", mock_open(read_data=test_content)):
            graph = read(str(TEST_DATA_DIR / "test_with_scores.tetrad"))
            assert graph is not None
            assert len(graph.nodes) == 2
            assert set(graph.nodes) == {"A", "B"}
            assert graph.is_DAG()
