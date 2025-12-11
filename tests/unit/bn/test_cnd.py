import pytest

from causaliq_core.bn.dist.cnd import CND
from causaliq_core.bn.dist.cpt import CPT


class ConcreteCND(CND):
    """Concrete implementation of CND for testing abstract methods."""

    def __init__(self):
        super().__init__()
        self.has_parents = False
        self.free_params = 1

    @classmethod
    def fit(cls, node, parents, data):
        """Test implementation of abstract fit method."""
        return cls()

    def cdist(self, pvs):
        """Test implementation of abstract cdist method."""
        return {"0": 0.5, "1": 0.5}

    def parents(self):
        """Test implementation of abstract parents method."""
        return None

    def random_value(self, pvs):
        """Test implementation of abstract random_value method."""
        return "0"

    def to_spec(self, name_map):
        """Test implementation of abstract to_spec method."""
        return {}

    def __str__(self):
        """Test implementation of abstract __str__ method."""
        return "ConcreteCND"

    def __eq__(self, other):
        """Test implementation of abstract __eq__ method."""
        return isinstance(other, ConcreteCND)

    def validate_parents(self, node, parents, node_values):
        """Test implementation of abstract validate_parents method."""
        pass


# Test CND __init__ method (line 24)
def test_cnd_init():
    """Test CND constructor calls pass statement"""
    cnd = ConcreteCND()
    # The __init__ method just calls pass, but we verify it works
    assert isinstance(cnd, CND)
    assert hasattr(cnd, "has_parents")
    assert hasattr(cnd, "free_params")


# Test CND.validate_cnds error for bad/missing nodes (line 153)
def test_cnd_validate_cnds_bad_missing_nodes():
    """Test validate_cnds raises ValueError for bad/missing nodes in cnds"""

    # Create some test nodes and CNDs
    nodes = ["A", "B", "C"]
    parents = {"A": [], "B": [], "C": []}

    # Case 1: Missing node in cnds
    cnds_missing = {
        "A": CPT({"0": 0.5, "1": 0.5}),
        "B": CPT({"0": 0.3, "1": 0.7}),
        # Missing node "C"
    }

    with pytest.raises(
        ValueError, match="CND.validate_cnds\\(\\) bad/missing nodes in cnds"
    ):
        CND.validate_cnds(nodes, cnds_missing, parents)

    # Case 2: Extra node in cnds
    cnds_extra = {
        "A": CPT({"0": 0.5, "1": 0.5}),
        "B": CPT({"0": 0.3, "1": 0.7}),
        "C": CPT({"0": 0.2, "1": 0.8}),
        "D": CPT({"0": 0.1, "1": 0.9}),  # Extra node not in nodes list
    }

    with pytest.raises(
        ValueError, match="CND.validate_cnds\\(\\) bad/missing nodes in cnds"
    ):
        CND.validate_cnds(nodes, cnds_extra, parents)

    # Case 3: Different node names
    cnds_different = {
        "X": CPT({"0": 0.5, "1": 0.5}),
        "Y": CPT({"0": 0.3, "1": 0.7}),
        "Z": CPT({"0": 0.2, "1": 0.8}),
    }

    with pytest.raises(
        ValueError, match="CND.validate_cnds\\(\\) bad/missing nodes in cnds"
    ):
        CND.validate_cnds(nodes, cnds_different, parents)
