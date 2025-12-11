import pytest

from causaliq_core.bn.dist.cpt import CPT
from tests.functional.fixtures import example_cpts as cpt


# Test CPT constructor with no arguments
def test_cpt_type_error_1():  # no arguments
    with pytest.raises(TypeError):
        CPT()


# Test CPT constructor with invalid pmfs types
def test_cpt_type_error_2():  # bad pmfs type
    with pytest.raises(TypeError):
        CPT(23)
    with pytest.raises(TypeError):
        CPT(-9.2)
    with pytest.raises(TypeError):
        CPT(None)
    with pytest.raises(TypeError):
        CPT(True)


# Test CPT constructor with invalid estimated parameter types
def test_cpt_type_error_3():  # bad estimated type
    with pytest.raises(TypeError):
        CPT(pmfs={"1": 0.0, "0": 1.0}, estimated=1.2)
    with pytest.raises(TypeError):
        CPT(pmfs={"1": 0.0, "0": 1.0}, estimated=True)
    with pytest.raises(TypeError):
        CPT(pmfs={"1": 0.0, "0": 1.0}, estimated=[1])


# Test CPT constructor with invalid simple PMF values
def test_cpt_value_error_1():  # bad simple pmf value to constructor
    with pytest.raises(ValueError):
        CPT({})
    with pytest.raises(ValueError):
        CPT({"A": 0.25})
    with pytest.raises(ValueError):
        CPT({"A": "0.5", "B": "0.5"})
    with pytest.raises(ValueError):
        CPT({"A": -0.1, "B": 0.7, "C": 0.4})
    with pytest.raises(ValueError):
        CPT({"A": 0.2, "B": 0.799998})
    with pytest.raises(ValueError):
        CPT({"A": 0.6, "B": 0.40001})


# Test CPT constructor with invalid multi PMF values
def test_cpt_value_error_2():  # bad multi pmf value to constructor
    with pytest.raises(ValueError):
        CPT([])
    with pytest.raises(ValueError):
        CPT([(), ()])
    with pytest.raises(ValueError):
        CPT([({}, {}), ({}, {})])
    with pytest.raises(ValueError):
        CPT([({}, {"0": 0.2, "1": 0.8}), ({}, {"0": 0.7, "1": 0.3})])
    with pytest.raises(ValueError):
        CPT(
            [
                ({"A": "0"}, {"0": 2, "1": 0.8}),
                ({"A": "1"}, {"0": 0.7, "1": 0.3}),
            ]
        )
    with pytest.raises(ValueError):
        CPT(
            [
                ({"A": "0"}, {"0": 0.2, "1": 0.8, "2": 0.3}),
                ({"A": "1"}, {"0": 0.7, "1": 0.3}),
            ]
        )
    with pytest.raises(ValueError):
        CPT(
            [
                ({"A": "0"}, {"0": 0.2, "1": 0.8}),
                ({"A": 1}, {"0": 0.7, "1": 0.3}),
            ]
        )


# Test CPT constructor with additional invalid multi PMF values
def test_cpt_value_error_3():  # more bad multi pmf value to constructor
    with pytest.raises(ValueError):
        CPT(
            [
                ({"A": "0"}, {"0": 0.2, "1": 0.8}),
                ({"B": "1"}, {"0": 0.7, "1": 0.3}),
            ]
        )
    with pytest.raises(ValueError):
        CPT(
            [
                ({"A": "0"}, {"0": 0.2, "1": 0.8}),
                ({"A": "1"}, {"0": 0.7, "2": 0.3}),
            ]
        )
    with pytest.raises(ValueError):
        CPT([({"A": "0"}, {"0": 0.2, "1": 0.8}), ({"A": "1"}, {"0": 0.7})])
    with pytest.raises(ValueError):
        CPT(
            [
                ({"A": "0", "B": "1"}, {"0": 0.2, "1": 0.8}),
                ({"A": "1"}, {"0": 0.7, "1": 0.3}),
            ]
        )


# Test CPT constructor with invalid estimated values
def test_cpt_value_error_4():  # bad estimated value
    with pytest.raises(ValueError):
        CPT({"A": 0.2, "B": 0.8}, estimated=-1)
    with pytest.raises(ValueError):
        CPT({"A": 0.2, "B": 0.8}, estimated=2)


# Test pmf method called with arguments on parentless node
def test_cpt_pmf_type_error1():  # parentless node but pmf called with arg
    cpt = CPT({"A": 0.2, "B": 0.8})
    with pytest.raises(TypeError):
        cpt.cdist({"A": 1})


# Test pmf method called with non-dict for node with parents
def test_cpt_pmf_type_error2():  # pmf called with non-dict for node w/ parents
    cpt = CPT(
        [
            ({"A": "0"}, {"0": 0.2, "1": 0.8}),
            ({"A": "1"}, {"0": 0.7, "1": 0.3}),
        ]
    )
    with pytest.raises(TypeError):
        cpt.cdist()
    with pytest.raises(TypeError):
        cpt.cdist(["A", 1])
    with pytest.raises(TypeError):
        cpt.cdist(2.7)


# Test pmf method called with unknown parental values
def test_cpt_pmf_value_error():  # pmf called with unknown parental values
    cpt = CPT(
        [
            ({"A": "0"}, {"0": 0.2, "1": 0.8}),
            ({"A": "1"}, {"0": 0.7, "1": 0.3}),
        ]
    )
    with pytest.raises(ValueError):
        cpt.cdist({"A": 2})
    with pytest.raises(ValueError):
        cpt.cdist({"B": 1})


# Test valid single PMF constructor with p0_v2_1
def test_p0_v2_1_ok():  # good single pmf to constructor
    cpt.p0_v2_1(cpt.p0_v2_1())


# Test valid single PMF constructor with p0_v2_2
def test_p0_v2_2_ok():  # good single pmf to constructor
    cpt.p0_v2_2(cpt.p0_v2_2())


# Test valid single PMF constructor with p0_v3_1
def test_p0_v3_1_ok():  # good single pmf to constructor
    cpt.p0_v3_1(cpt.p0_v3_1())


# Test valid multi PMF constructor with p1_v2_1
def test_p1_v2_1_ok():  # good multi pmf to constructor
    cpt.p1_v2_1(cpt.p1_v2_1())


# Test valid multi PMF constructor with p2_v2_1
def test_cpt_ok():  # good multi pmf to constructor
    cpt.p2_v2_1(cpt.p2_v2_1())


# Test equality comparison for identical p0_v2_1 CPTs
def test_cpt_p0_v2_1_eq():  # compare identical CPTs
    assert cpt.p0_v2_1() == cpt.p0_v2_1()
    assert (cpt.p0_v2_1() != cpt.p0_v2_1()) is False


# Test equality comparison for identical p0_v2_1 and p0_v2_1a CPTs
def test_cpt_p0_v2_1a_eq():  # compare identical CPTs
    assert cpt.p0_v2_1() == cpt.p0_v2_1a()
    assert (cpt.p0_v2_1() != cpt.p0_v2_1a()) is False


# Test equality comparison for identical p0_v3_1 CPTs
def test_cpt_p0_v3_1_eq():  # compare identical CPTs
    assert cpt.p0_v3_1() == cpt.p0_v3_1()
    assert (cpt.p0_v3_1() != cpt.p0_v3_1()) is False


# Test equality comparison for identical p1_v2_1 CPTs
def test_cpt_p1_v2_1_eq():  # compare identical CPTs
    assert cpt.p1_v2_1() == cpt.p1_v2_1()
    assert (cpt.p1_v2_1() != cpt.p1_v2_1()) is False


# Test equality comparison for identical p2_v2_1 CPTs
def test_cpt_p2_v2_1_eq():  # compare identical CPTs
    assert cpt.p2_v2_1() == cpt.p2_v2_1()
    assert (cpt.p2_v2_1() != cpt.p2_v2_1()) is False


# Test equality comparison for identical p2_v2_1 and p2_v2_1a CPTs
def test_cpt_p2_v2_1a_eq():  # compare identical CPTs
    assert cpt.p2_v2_1() == cpt.p2_v2_1a()
    assert (cpt.p2_v2_1() != cpt.p2_v2_1a()) is False


# Test equality comparison for nearly identical p0_v2_1 CPTs
def test_cpt_p0_v2_1b_eq():  # compare NEARLY identical CPTs
    assert cpt.p0_v2_1() == cpt.p0_v2_1b()
    assert cpt.p0_v2_1a() == cpt.p0_v2_1b()
    assert (cpt.p0_v2_1() != cpt.p0_v2_1b()) is False
    assert (cpt.p0_v2_1a() != cpt.p0_v2_1b()) is False


# Test equality comparison for nearly identical p2_v2_1 CPTs
def test_cpt_p2_v2_1b_eq():  # compare NEARLY identical CPTs
    assert cpt.p2_v2_1() == cpt.p2_v2_1b()
    assert cpt.p2_v2_1a() == cpt.p2_v2_1b()
    assert (cpt.p2_v2_1() != cpt.p2_v2_1b()) is False
    assert (cpt.p2_v2_1a() != cpt.p2_v2_1b()) is False


# Test inequality comparison for CPTs with different probabilities
def test_cpt_ne1():  # compare simple CPTs with different probs
    assert cpt.p0_v2_1() != cpt.p0_v2_2()
    assert (cpt.p0_v2_1() == cpt.p0_v2_2()) is False


# Test inequality comparison for CPTs with different node values
def test_cpt_ne2():  # compare simple CPTs with different node values
    assert cpt.p0_v2_1() != cpt.p0_v2_3()
    assert (cpt.p0_v2_1() == cpt.p0_v2_3()) is False


# Test inequality comparison for different multi-parent CPTs
def test_cpt_ne3():  # compare different CPTs
    assert cpt.p2_v2_1() != cpt.p2_v2_2()
    assert (cpt.p2_v2_1() == cpt.p2_v2_2()) is False


# Test inequality comparison for different multi-parent CPT variants
def test_cpt_ne4():  # compare different CPTs
    assert cpt.p2_v2_1a() != cpt.p2_v2_2()
    assert (cpt.p2_v2_1a() == cpt.p2_v2_2()) is False


# test to_spec function including name mapping


# Test to_spec method with missing arguments
def test_to_spec_type_error_1():  # no arguments
    with pytest.raises(TypeError):
        cpt.p0_v2_1().to_spec()
    with pytest.raises(TypeError):
        cpt.p2_v2_1().to_spec()


# Test to_spec method with invalid name_map type
def test_to_spec_type_error_2():
    with pytest.raises(TypeError):
        cpt.p0_v2_1().to_spec(False)
    with pytest.raises(TypeError):
        cpt.p2_v2_1().to_spec(None)
    with pytest.raises(TypeError):
        cpt.p0_v2_1().to_spec(1)
    with pytest.raises(TypeError):
        cpt.p2_v2_1().to_spec(23.2)
    with pytest.raises(TypeError):
        cpt.p2_v2_1().to_spec(["A"])


# Test to_spec method with non-string keys in name_map
def test_to_spec_type_error_3():
    with pytest.raises(TypeError):
        cpt.p0_v2_1().to_spec({1: "A", "B": "S"})
    with pytest.raises(TypeError):
        cpt.p2_v2_1().to_spec({1: "A", "B": "S"})


# Test to_spec method with non-string values in name_map
def test_to_spec_type_error_4():
    with pytest.raises(TypeError):
        cpt.p0_v2_1().to_spec({"A": "A", "B": 0.05})
    with pytest.raises(TypeError):
        cpt.p2_v2_1().to_spec({"A": "A", "B": 0.05})


# Test to_spec method with incomplete name_map
def test_to_spec_value_error_1():
    with pytest.raises(ValueError):
        cpt.p2_v2_1().to_spec({"A": "X", "C": "Y"})


# Test to_spec method with identity name mapping
def test_to_spec_1_ok():
    name_map = {"A": "A", "B": "B"}
    spec = cpt.p2_v2_1().to_spec(name_map)
    print("\n\nSpec is:\n{}".format("\n".join([s.__str__() for s in spec])))

    cpt.p2_v2_1(CPT(spec))  # check spec against original definition


# Test to_spec method name mapping on orphan CPT
def test_to_spec_2_ok():
    name_map = {"A": "AA", "B": "BB"}
    spec = cpt.p0_v2_1().to_spec(name_map)
    print("\n\nSpec is {}".format(spec))

    cpt.p0_v2_1(CPT(spec))  # check spec against original definition


# Test to_spec method with name mapping and reordering
def test_to_spec_3_ok():
    name_map = {"A": "ZA", "B": "YB", "C": "ignored"}
    spec = cpt.p2_v2_1().to_spec(name_map)
    print("\n\nSpec is:\n{}".format("\n".join([s.__str__() for s in spec])))

    assert spec == [
        ({"YB": "0", "ZA": "0"}, {"0": 0.2, "1": 0.8}),
        ({"YB": "1", "ZA": "0"}, {"0": 0.7, "1": 0.3}),
        ({"YB": "0", "ZA": "1"}, {"0": 0.5, "1": 0.5}),
        ({"YB": "1", "ZA": "1"}, {"1": 0.9, "0": 0.1}),
    ]


# Test CPT.fit() type error (line 143)
def test_cpt_fit_type_error():
    """Test CPT.fit() raises TypeError for bad data type"""
    with pytest.raises(TypeError, match="CPT.fit\\(\\) bad arg type"):
        CPT.fit("A", None, "invalid_data_type")


# Test random_value method (lines 227-235)
def test_cpt_random_value():
    """Test random_value method returns valid values"""
    # Test with simple CPT
    simple_cpt = cpt.p0_v2_1()

    # Test multiple calls to ensure it returns valid values
    for _ in range(10):
        value = simple_cpt.random_value(None)
        assert value in ["0", "1"]

    # Test with CPT that has parents
    multi_cpt = cpt.p1_v2_1()

    # Test with different parental values
    for _ in range(10):
        value1 = multi_cpt.random_value({"A": "0"})
        value2 = multi_cpt.random_value({"A": "1"})
        assert value1 in ["0", "1"]
        assert value2 in ["0", "1"]


# Test random_value method hits early return path
def test_cpt_random_value_early_return(monkeypatch):

    # Create a CPT with known probabilities
    test_cpt = cpt.p0_v2_2()  # {"0": 0.2, "1": 0.8}

    # Try your approach - mock random_generator to return 10
    class MockRandomGenerator:
        def random(self):
            return 10  # random <= cum_prob will never be true

    # Also try with a very small value in the same test
    class MockRandomGeneratorSmall:
        def random(self):
            return 0.01  # Very small, should make random <= cum_prob true

    def mock_random_generator_large():
        return MockRandomGenerator()

    def mock_random_generator_small():
        return MockRandomGeneratorSmall()

    # Test with large value first (your suggestion)
    monkeypatch.setattr(
        "causaliq_core.bn.dist.cpt.random_generator",
        mock_random_generator_large,
    )

    value1 = test_cpt.random_value(None)

    # Test with small value
    monkeypatch.setattr(
        "causaliq_core.bn.dist.cpt.random_generator",
        mock_random_generator_small,
    )

    value2 = test_cpt.random_value(None)

    # Both should return valid values
    assert value1 in ["0", "1"]
    assert value2 in ["0", "1"]


# Test parents() method for nodes without parents (line 253)
def test_cpt_parents_none():
    """Test parents() method returns None for nodes without parents"""
    simple_cpt = cpt.p0_v2_1()
    assert simple_cpt.parents() is None


# Test __eq__ method comparisons (line 343)
def test_cpt_inequality_comparison():
    """Test CPT inequality comparisons"""
    cpt1 = cpt.p0_v2_1()
    cpt2 = cpt.p1_v2_1()

    # Test comparison with non-CPT object
    assert cpt1 != "not a cpt"
    assert cpt1 != 42
    assert cpt1 is not None

    # Test CPTs with different has_parents
    assert cpt1 != cpt2  # simple vs multi-entry CPT

    # Test CPTs with different free_params
    cpt3 = CPT({"0": 0.3, "1": 0.7})  # different probabilities
    assert cpt1 != cpt3


# Test validate_parents errors (lines 379, 388, 398)
def test_cpt_validate_parents_errors():
    """Test validate_parents method error conditions"""

    # Test parent mismatch error
    # - node has no parents but parents dict says it does
    simple_cpt = cpt.p0_v2_1()
    with pytest.raises(ValueError, match="parent mismatch"):
        simple_cpt.validate_parents(
            "A", {"A": ["B"]}, {"A": {"0": 1, "1": 1}, "B": {"0": 1, "1": 1}}
        )

    # Test parent mismatch error
    multi_cpt = cpt.p1_v2_1()
    with pytest.raises(ValueError, match="parent mismatch"):
        multi_cpt.validate_parents(
            "B", {"B": ["C"]}, {"B": {"0": 1, "1": 1}, "C": {"0": 1, "1": 1}}
        )

    # Test bad parent value error (line 388)
    with pytest.raises(ValueError, match="bad parent value"):
        multi_cpt.validate_parents(
            "B", {"B": ["A"]}, {"B": {"0": 1, "1": 1}, "A": {"2": 1, "3": 1}}
        )

    # Test missing parental value combos error (line 398)
    with pytest.raises(ValueError, match="missing parental value combos"):
        multi_cpt.validate_parents(
            "B",
            {"B": ["A"]},
            {"B": {"0": 1, "1": 1}, "A": {"0": 1, "1": 1, "2": 1}},
        )
