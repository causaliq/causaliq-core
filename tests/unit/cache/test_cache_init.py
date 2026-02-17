"""Unit tests for cache module initialisation."""


# Verify cache module can be imported.
def test_cache_module_imports() -> None:
    import causaliq_core.cache

    assert hasattr(causaliq_core.cache, "__all__")


# Verify compressors submodule can be imported.
def test_compressors_module_imports() -> None:
    import causaliq_core.cache.compressors

    assert hasattr(causaliq_core.cache.compressors, "__all__")
