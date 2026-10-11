#
#   Conditional Probability Table for discrete distribution
#

from itertools import combinations
from typing import Any, Dict, List, Optional, Tuple, Union

from causaliq_core.utils.random import random_generator
from causaliq_core.utils.same import values_same

from ..bnfit import BNFit
from .cnd import CND

try:
    from data.pandas import Pandas  # type: ignore
except ImportError:
    Pandas = None


class CPT(CND):
    """Base class for conditional probability tables.

    Args:
        pmfs: A pmf of {value: prob} for parentless nodes OR
            list of tuples ({parent: value}, {value: prob}).
        estimated: How many PMFs were estimated.

    Attributes:
        cpt: Internal representation of the CPT.
            {node_values: prob} for parentless node, otherwise
            {parental_values as frozenset: {node_values: prob}}.
        estimated: Number of PMFs that were estimated.
        values: Values which node can take.

    Raises:
        TypeError: If arguments are of wrong type.
        ValueError: If arguments have invalid or conflicting values.
    """

    def __init__(
        self,
        pmfs: Union[
            Dict[str, float], List[Tuple[Dict[str, str], Dict[str, float]]]
        ],
        estimated: int = 0,
    ) -> None:

        self.estimated = estimated
        _check_cpt_args(pmfs, estimated)
        if isinstance(pmfs, dict):
            # parentless node with simple CPT
            self._init_parentless(pmfs)
        else:
            # node with parents - multi-entry CPT
            self._init_parented(pmfs)

    def _init_parentless(self, pmfs: Dict[str, float]) -> None:
        """Record a parentless node's simple CPT.

        Args:
            pmfs: PMF of the node's values.

        Raises:
            ValueError: If the PMF is malformed or does not sum to 1.
        """
        _check_pmf(pmfs)
        self.cpt: Dict[Any, Any] = pmfs
        self.has_parents = False
        self.free_params = len(pmfs) - 1
        self.values = set(self.cpt.keys())

    def _init_parented(
        self, pmfs: List[Tuple[Dict[str, str], Dict[str, float]]]
    ) -> None:
        """Record a parented node's multi-entry CPT.

        Args:
            pmfs: CPT entries ({parent: value}, {value: prob}).

        Raises:
            ValueError: If the entries are malformed or inconsistent.
        """
        if len(pmfs) < 2:
            raise ValueError("CPT has fewer than two entries")
        self.cpt = {}
        self.has_parents = True
        prev_parents: Optional[frozenset] = None
        prev_values: Optional[frozenset] = None

        for entry in pmfs:
            prev_parents, prev_values = _add_cpt_entry(
                self.cpt, entry, prev_parents, prev_values
            )

        # compute number of free params
        self.free_params = (len(prev_values) - 1) * len(  # type: ignore
            self.cpt
        )
        self.values = prev_values  # type: ignore

    @classmethod
    def fit(
        cls,
        node: str,
        parents: Optional[Tuple[str, ...]],
        data: Union[BNFit, Any],
        autocomplete: bool = True,
    ) -> Tuple[Tuple[type, Dict[str, Any]], Optional[int]]:
        """Constructs a CPT (Conditional Probability Table) from data.

        Args:
            node: Node that CPT applies to.
            parents: Parents of node.
            data: Data to fit CPT to.
            autocomplete: Whether to ensure CPT data contains entries for
                combinations of parental values that don't occur in the data.

        Returns:
            Tuple of (cnd_spec, estimated_pmfs) where
            cnd_spec is (CPT class, cpt_spec for CPT())
            estimated_pmfs is int, # estimated pmfs.
        """
        if not isinstance(data, BNFit if Pandas is None else (Pandas, BNFit)):
            raise TypeError("CPT.fit() bad arg type")

        if parents is None:
            return (_parentless_cpt_spec(node, data), 0)

        cptdata, estimated_pmfs = _fit_parented_cpt(
            node, parents, data, autocomplete
        )
        return ((CPT, cptdata), estimated_pmfs)  # type: ignore[return-value]

    def cdist(
        self, parental_values: Optional[Dict[str, str]] = None
    ) -> Dict[str, float]:
        """Return conditional probabilities of node values for specified
        parental values.

        Args:
            parental_values: Parental values for which pmf required
                for non-orphans.

        Raises:
            TypeError: If args are of wrong type.
            ValueError: If args have invalid or conflicting values.
        """
        if (not self.has_parents and parental_values is not None) or (
            self.has_parents and not isinstance(parental_values, dict)
        ):
            raise TypeError("CPT.cdist() CPT/parental values mismatch")

        if not self.has_parents:
            return self.cpt
        else:
            pvs = frozenset(
                [(k, v) for k, v in parental_values.items()]  # type: ignore
            )
            if pvs not in self.cpt:  # type: ignore
                raise ValueError("Unknown parental values for cdist call")
            return self.cpt[pvs]  # type: ignore

    def random_value(self, pvs: Optional[Dict[str, str]]) -> str:
        """Generate a random value for a node given the value of its parents.

        Args:
            pvs: Parental values, {parent1: value1, ...}.

        Returns:
            Random value for node.
        """
        pmf = self.cdist(pvs)
        values = list(pmf.keys())
        random = random_generator().random()
        cum_prob = 0.0
        for idx, value in enumerate(values):
            cum_prob += pmf[value]
            if random <= cum_prob:
                return value
        return values[-1]

    def node_values(self) -> List[str]:
        """Return node values (states) of node CPT relates to.

        Returns:
            Node values in alphabetical order.
        """
        return (
            sorted(list(self.cpt.keys()))
            if not self.has_parents
            else sorted(
                list(next(iter(self.cpt.values())).keys())  # type: ignore
            )
        )

    def parents(self) -> List[str]:
        """Return parents of node CPT relates to.

        Returns:
            Parent node names in alphabetical order.
        """
        if not self.has_parents:
            return None  # type: ignore[return-value]
        else:
            return sorted([t[0] for t in (list(self.cpt.keys()))[0]])

    def to_spec(self, name_map: Dict[str, str]) -> Dict[str, Any]:
        """Returns external specification format of CPT,
        renaming nodes according to a name map.

        Args:
            name_map: Map of node names {old: new}.

        Returns:
            CPT specification with renamed nodes.

        Raises:
            TypeError: If bad arg type.
            ValueError: If bad arg value, e.g. coeff keys not in map.
        """
        if (
            not isinstance(name_map, dict)
            or not all([isinstance(k, str) for k in name_map])
            or not all([isinstance(v, str) for v in name_map.values()])
        ):
            raise TypeError("CPT.to_spec() bad arg type")

        if self.has_parents:
            print({nv[0] for nv in tuple(self.cpt)[0]})

        if (
            self.has_parents
            and len({nv[0] for nv in tuple(self.cpt)[0]} - set(name_map)) != 0
        ):
            raise ValueError("CPT.to_spec() bad arg value")

        if self.has_parents is False:
            spec = self.cpt
        else:
            spec = [
                (
                    self._map_keys({t[0]: t[1] for t in pvs}, name_map),
                    pmf,
                )  # type: ignore
                for pvs, pmf in self.cpt.items()
            ]
        return spec

    def param_ratios(self) -> None:
        """
        Returns distribution of parameter ratios across all parental
        values for each combination of possible node values.

        :returns dict: {(node value pair): (param ratios across parents)
        """
        pairs = tuple(combinations(iterable=self.node_values(), r=2))

        ratios = {}
        for pvs, pmf in (
            self.cpt
            if self.has_parents
            else {None: self.cdist()}  # type: ignore
        ).items():
            _ratios = {p: pmf[p[0]] / pmf[p[1]] for p in pairs}  # type: ignore
            ratios[pvs] = pmf
            print("*** {} --> {}: ratios {}".format(pvs, pmf, _ratios))

    def __str__(self) -> str:
        """Human-friendly description of the contents of the CPT.

        Returns:
            String representation of the CPT contents.
        """
        if not self.has_parents:
            return "{}".format({v: round(p, 6) for v, p in self.cpt.items()})
        else:
            str = [
                "{} -> {}".format(
                    {t[0]: t[1] for t in pvs},
                    {v: round(p, 6) for v, p in pmf.items()},  # type: ignore
                )
                for pvs, pmf in self.cpt.items()
            ]
            return "\n".join(str)

    def __eq__(self, other: object) -> bool:
        """
        Return whether two CPTs are the same allowing for probability
        rounding errors

        :param other: CPT to compared to self
        :type other: CPT

        :returns: whether CPTs are PRACTICALLY the same
        :rtype: bool
        """

        def _pmfs_same(
            pmf1: Dict[str, float], pmf2: Dict[str, float]
        ) -> bool:  # compare two PMFs to 6 sig. figures
            return pmf1.keys() == pmf2.keys() and all(
                [values_same(v, pmf2[k], sf=6) for k, v in pmf1.items()]
            )

        if not isinstance(other, CPT):
            return False

        if (
            self.has_parents != other.has_parents
            or self.free_params != other.free_params
            or self.cpt.keys() != other.cpt.keys()
        ):
            return False

        return (
            _pmfs_same(self.cpt, other.cpt)
            if not self.has_parents
            else all(
                [
                    _pmfs_same(v, other.cpt[k])  # type: ignore
                    for k, v in self.cpt.items()
                ]
            )
        )

    def validate_parents(
        self,
        node: str,
        parents: Dict[str, List[str]],
        node_values: Dict[str, List[str]],
    ) -> None:
        """Checks every CPT's parents and parental values are consistent
        with other relevant CPTs and the DAG structure.

        Args:
            node: Name of node.
            parents: Parents of all nodes {node: parents}.
            node_values: Values of each cat. node {node: values}.

        Raises:
            ValueError: If parent mismatch or missing parental
                value combinations.
        """

        # Check parents defined in CPT keys match those defined in parents
        # arg (i.e. tha DAG)

        _check_cpt_declared_parents(self, node, parents)

        if not self.has_parents:
            return

        # check values in CPT keys are valid for the parents specified

        _check_cpt_parent_values(self.cpt, node_values)

        # Check CPT has expected number of entries - one for each possible
        # combination of parental Values

        if len(self.cpt) != _cpt_row_count(parents[node], node_values):
            raise ValueError(
                "CPT.validate_parents() non-orphan"
                + " has missing parental value combos"
            )


class NodeValueCombinations:
    """
    Iterable over all combinations of node values

    :param dict node_values: allowed values for each node {node: [values]}
    :param bool sort: whether to sort node names and values into
                      alphabetic order
    """

    def __init__(
        self, node_values: Dict[str, List[str]], sort: bool = True
    ) -> None:

        # store node values, optionally sorting them

        self.node_values = {
            n: sorted(s) if sort else s for n, s in node_values.items()
        }

        # store node names, optionally sorting them

        self.nodes = (
            sorted(list(node_values.keys()))
            if sort
            else list(node_values.keys())
        )

        # store number of possible values for each node

        self.cards = [len(node_values[n]) for n in self.nodes]

    def __iter__(self) -> "NodeValueCombinations":
        """
        Returns the initialised iterator

        :returns NodeValueCombinations: the iterator
        """

        # Initialises indices which define current combination of values -
        # each index value is a pointer into the values in node_values

        self.indices = len(self.cards) * [0]
        self.indices[len(self.cards) - 1] = -1
        return self

    def __next__(self) -> Dict[str, str]:
        """
        Generate the next node value combination

        :raises StopIteration: when all combinations have been returned

        :returns dict: next node value combination {node: value}
        """

        # move on to next combination by incrementing lowest order index
        self.indices[len(self.cards) - 1] += 1

        # if lowest order index has gone past number of possible states then
        # perform a "carry-over" operation by zeroing it and incrementing the
        # next highest order index.
        # Repeat if necessary up the index order (just like in arithmetic)

        for j in range(len(self.cards) - 1, -1, -1):
            if self.indices[j] == self.cards[j]:

                # perform "carry-over" operation

                if j == 0:

                    # if we're attempting a carry over from highest order
                    # index then we've exhausted possible combinations
                    raise StopIteration

                self.indices[j] = 0
                self.indices[j - 1] += 1
            else:
                break

        # Convert the indices to a dictionary {parent: value} and return

        return {
            self.nodes[p]: self.node_values[self.nodes[p]][v]
            for p, v in enumerate(self.indices)
        }


def _check_cpt_args(pmfs: Any, estimated: int) -> None:
    """Validate the arguments of the CPT constructor.

    Args:
        pmfs: PMFs supplied to the constructor.
        estimated: Number of estimated PMFs supplied.

    Raises:
        TypeError: If arguments are of wrong type.
        ValueError: If arguments have invalid values.
    """
    if (
        (not isinstance(pmfs, dict) and not isinstance(pmfs, list))
        or not isinstance(estimated, int)
        or isinstance(estimated, bool)
    ):
        raise TypeError("bad arg type for CPT")
    if (
        estimated < 0
        or (isinstance(pmfs, list) and estimated > len(pmfs))
        or (isinstance(pmfs, dict) and estimated > 1)
    ):
        raise ValueError("CPT has bad estimated value")


def _check_pmf(pmf: Dict[str, float]) -> None:
    """Validate a probability mass function.

    Args:
        pmf: Probability mass function {value: prob}.

    Raises:
        ValueError: If the PMF is too small, holds bad probabilities or
            does not sum to 1.
    """
    if len(pmf) < 2:
        raise ValueError("PMF too few entries")
    for prob in pmf.values():
        if not isinstance(prob, float) or prob < 0.0 or prob > 1.0:
            raise ValueError("Bad PMF probability")
    total = sum(pmf.values())
    if 0.999999 > total or total > 1.000001:
        raise ValueError("PMF probability does not sum to 1")


def _check_parental_values(p_vals: Dict[str, str]) -> None:
    """Validate the parental values of a multi-entry CPT entry.

    Args:
        p_vals: Parental values {parent: value}.

    Raises:
        ValueError: If the parental values are missing or not strings.
    """
    if not len(p_vals) or not all(
        [isinstance(v, str) for v in p_vals.values()]
    ):
        raise ValueError("bad parental values")


def _check_cpt_entry(entry: Any) -> None:
    """Validate the contents of one multi-entry CPT entry.

    Args:
        entry: Entry to validate, ({parent: value}, {value: prob}).

    Raises:
        ValueError: If the entry has invalid types or values.
    """
    if (
        not isinstance(entry, tuple)
        or len(entry) != 2
        or not isinstance(entry[0], dict)
        or not isinstance(entry[1], dict)
    ):
        raise ValueError("Invalid CPT entry types")
    _check_parental_values(entry[0])
    _check_pmf(entry[1])


def _add_cpt_entry(
    cpt: Dict[Any, Any],
    entry: Any,
    prev_parents: Optional[frozenset],
    prev_values: Optional[frozenset],
) -> Tuple[frozenset, frozenset]:
    """Add one entry to a multi-entry CPT.

    Args:
        cpt: CPT entries accumulated so far, extended in place.
        entry: Entry to add, ({parent: value}, {value: prob}).
        prev_parents: Parents seen in earlier entries, if any.
        prev_values: Node values seen in earlier entries, if any.

    Returns:
        Tuple of (parents, node values) seen so far.

    Raises:
        ValueError: If the entry is malformed or inconsistent with the
            entries already added.
    """
    _check_cpt_entry(entry)
    parents = frozenset(entry[0].keys())
    values = frozenset(entry[1].keys())
    if prev_parents is not None and prev_parents != parents:
        raise ValueError("Parents in CPT entries vary")
    if prev_values is not None and prev_values != values:
        raise ValueError("Values in CPT entries vary")

    # make parental values a frozenset so it can be a dict key
    pvs = frozenset([(k, v) for k, v in entry[0].items()])
    cpt[pvs] = entry[1]
    return parents, values


def _parentless_cpt_spec(node: str, data: Any) -> Tuple[type, Dict[str, Any]]:
    """Return the CPT specification of a parentless node.

    Args:
        node: Name of the node.
        data: Data whose observed frequencies define the PMF.

    Returns:
        Tuple of (CPT class, PMF of the node's values).
    """
    return (CPT, {k: v / data.N for k, v in data.node_values[node].items()})


def _fit_parented_cpt(
    node: str, parents: Tuple[str, ...], data: Any, autocomplete: bool
) -> Tuple[List[Tuple[Any, Dict[str, Any]]], int]:
    """Return the CPT entries and estimate count for a parented node.

    Args:
        node: Name of the node.
        parents: Parents of the node.
        data: Data to fit the CPT to.
        autocomplete: Whether to add the entries for parental value
            combinations that are missing from the data.

    Returns:
        Tuple of (CPT entries, number of PMFs that were estimated).
    """
    cptdata: List[Tuple[Any, Dict[str, Any]]] = []
    parent_map = {node: list(parents)} if len(parents) > 0 else {}
    counts, _, rowval, colval = data.marginals(node, parent_map, True)

    for j in range(counts.shape[1]):
        N_ij = counts[:, j].sum()  # total count for jth parent combo
        cond_pmf = {
            rowval[k]: counts[k, j] / N_ij for k in range(counts.shape[0])
        }
        cptdata.append((colval[j], cond_pmf))

    if not autocomplete:
        return cptdata, 0
    return cptdata, _autocomplete_cpt_entries(node, parents, data, cptdata)


def _autocomplete_cpt_entries(
    node: str,
    parents: Tuple[str, ...],
    data: Any,
    cptdata: List[Tuple[Any, Dict[str, Any]]],
) -> int:
    """Add CPT entries for parental combinations missing from the data.

    Args:
        node: Name of the node.
        parents: Parents of the node.
        data: Data the CPT is being fitted to.
        cptdata: CPT entries found in the data, extended in place.

    Returns:
        Number of PMFs that had to be estimated.
    """
    pmf = {k: v / data.N for k, v in data.node_values[node].items()}
    parent_values = {p: list(data.node_values[p].keys()) for p in parents}
    pvs_in_data = [c[0] for c in cptdata]
    estimated = 0

    for pvs in NodeValueCombinations(parent_values):
        if pvs not in pvs_in_data:
            cptdata.append((pvs, pmf))
            estimated += 1

    return estimated


def _check_cpt_declared_parents(
    cpt: CPT, node: str, parents: Dict[str, List[str]]
) -> None:
    """Check a CPT's declared parents agree with the DAG structure.

    Args:
        cpt: CPT being validated.
        node: Name of the node.
        parents: Parents of all nodes {node: parents}.

    Raises:
        ValueError: If the declared parents do not match the DAG.
    """
    mismatched = (
        (node not in parents and cpt.has_parents is True)
        or (node in parents and cpt.has_parents is False)
        or (
            node in parents
            and cpt.has_parents is True
            and set(parents[node]) != set(cpt.parents())
        )
    )
    if mismatched:
        raise ValueError("CPT.validate_parents() parent mismatch")


def _check_cpt_parent_values(
    cpt: Dict[Any, Any], node_values: Dict[str, List[str]]
) -> None:
    """Check the values in a CPT's keys are valid for its parents.

    Args:
        cpt: CPT entries keyed by parental value combinations.
        node_values: Values of each cat. node {node: values}.

    Raises:
        ValueError: If a parental value is not valid for its parent.
    """
    for pvs, _ in cpt.items():
        for parent, value in {t[0]: t[1] for t in pvs}.items():
            if value not in node_values[parent]:
                raise ValueError(
                    "CPT.validate_parents()" + " bad parent value"
                )


def _cpt_row_count(
    parents: List[str], node_values: Dict[str, List[str]]
) -> int:
    """Return the number of parental value combinations for a node.

    Args:
        parents: Parents of the node.
        node_values: Values of each cat. node {node: values}.

    Returns:
        Number of rows an exhaustive CPT for the node requires.
    """
    cpt_num_rows = 1
    for parent in parents:
        cpt_num_rows *= len(node_values[parent])
    return cpt_num_rows
