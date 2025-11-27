"""
Functional tests of utils/io.py
"""

import pytest

from causaliq_core.utils import is_valid_path


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
