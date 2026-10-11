#
#   Bayesian Network class
#

from typing import Any, Dict, List, Optional, Tuple, Union

from pandas import DataFrame

from causaliq_core.graph import DAG
from causaliq_core.utils import write_dataframe
from causaliq_core.utils.random import set_random_seed

from .bnfit import BNFit
from .dist import CPT, LinGauss, NodeValueCombinations
from .dist.cnd import CND
from .marginals import (
    MarginalsCache,
    _accumulate_marginals,
    _check_lnprob_args,
    _check_marginal_distribution_args,
    _check_marginal_nodes,
    _marginal_frame,
    _marginals_frame,
    _node_lnprob,
    _ordered_required_nodes,
    _parental_marginal_frame,
    _parental_values_for,
)


class BN:
    """Base class for Bayesian Networks.

    Bayesian Networks have a DAG and an associated probability distribution
    defined by CPTs.

    Args:
        dag: DAG for the Bayesian Network.
        cnd_specs: Specification of each conditional node distribution.
        estimated_pmfs: Number of PMFs that had to be estimated for each node.

    Attributes:
        dag: BN's DAG.
        cnds: Conditional distributions for each node {node: CND}.
        free_params: Total number of free parameters in BN.
        estimated_pmfs: Number of estimated pmfs for each node.

    Raises:
        TypeError: If arguments have invalid types.
        ValueError: If arguments have invalid values.
    """

    def __init__(
        self,
        dag: DAG,
        cnd_specs: Dict[str, Any],
        estimated_pmfs: Dict[str, Any] = {},
    ) -> None:

        if not isinstance(dag, DAG) or not isinstance(cnd_specs, dict):
            raise TypeError("BN() bad arg type      ")

        self.dag = dag

        if sorted(self.dag.nodes) != sorted(list(cnd_specs.keys())):
            raise ValueError("Different nodes in DAG and cnd_specs")

        self.cnds = {}
        self.free_params = 0
        self.estimated_pmfs = estimated_pmfs
        for node in self.dag.nodes:
            self.cnds[node] = (cnd_specs[node][0])(cnd_specs[node][1])
            self.free_params += self.cnds[node].free_params

        self.cached_marginals = MarginalsCache()

        CND.validate_cnds(self.dag.nodes, self.cnds, self.dag.parents)

    @classmethod
    def fit(cls, dag: DAG, data: BNFit) -> "BN":
        """Alternative instantiation of BN using data to implicitly define the
        conditional probability data.

        Args:
            dag: DAG for the Bayesian Network.
            data: Data to fit CPTs to.

        Returns:
            A new BN instance fitted to the data.

        Raises:
            TypeError: If arguments have invalid types.
            ValueError: If arguments have invalid values.
        """
        if not isinstance(dag, DAG) or not isinstance(data, BNFit):
            raise TypeError("bn.fit() arguments have invalid types")

        if sorted(list(data.nodes)) != dag.nodes:
            raise ValueError("data empty, col mismatch or missing data")

        if any([(len(data.sample[c].unique()) == 1) for c in data.nodes]):
            raise ValueError("Some variables have only one value")

        cnd_specs = {}
        estimated_pmfs = {}
        for node in dag.nodes:
            parents = tuple(dag.parents[node]) if node in dag.parents else None
            cnd = CPT if data.node_types[node] == "category" else LinGauss
            cnd_specs[node], estimated_pmfs[node] = cnd.fit(
                node, parents, data
            )
        estimated_pmfs = {
            n: c for n, c in estimated_pmfs.items() if c is not None and c > 0
        }

        return cls(dag, cnd_specs, estimated_pmfs)

    def rename(self, name_map: Dict[str, str]) -> None:
        """Rename nodes in place according to name map.

        Args:
            name_map: Name mapping {name: new name}.

        Raises:
            TypeError: With bad arg type.
            ValueError: With bad arg values e.g. unknown node names.
        """

        def _map(odict: Dict[str, Any]) -> Dict[str, Any]:
            # rename and re-sort dict keys
            ndict = {
                name_map[k] if k in name_map else k: v
                for k, v in odict.items()
            }
            return {k: ndict[k] for k in sorted(ndict)}

        # rename variables in DAG - which checks validity of name_map

        old_names = self.dag.nodes
        self.dag.rename(name_map)

        # Generate CND specifications with renamed nodes

        cnd_specs = {}
        for node in old_names:
            cnd = self.cnds[node]
            cnd_specs.update({node: (type(cnd), cnd.to_spec(name_map))})

        # Rename and re-order the keys of the dict of {node: cnd}

        cnd_specs = _map(cnd_specs)

        # re-instantiate BN with new DAG and CPT data

        self.__init__(self.dag, cnd_specs)  # type: ignore[misc]

    def global_distribution(self) -> DataFrame:
        """Generate the global probability distribution for the BN.

        Returns:
            Global distribution in descending probability (and then by
            ascending values).
        """

        # Generate possible values at every node {node: [poss values]}

        node_values = {n: c.node_values() for n, c in self.cnds.items()}

        # Loop over all possible combinations of node values (i.e. a "case")
        # and collect the probability of each one

        values: Dict[str, List[Any]] = {n: [] for n in self.dag.nodes}
        probs = []
        for case in NodeValueCombinations(node_values):
            for node, value in case.items():
                values[node].append(value)
            lnprob = self.lnprob_case(case)
            probs.append(0.0 if lnprob is None else 10**lnprob)

        # return DataFrame with correct dtypes and sorted by descending
        # probability, and then ascending value order

        result: DataFrame = (
            DataFrame(values, dtype="category")
            .join(DataFrame({"": probs}, dtype="float64"))
            .sort_values(
                [""] + self.dag.nodes,
                ignore_index=True,
                ascending=[False] + [True] * len(self.dag.nodes),
            )
        )
        return result

    def marginal_distribution(
        self, node: str, parents: Optional[List[str]] = None
    ) -> DataFrame:
        """Generate a marginal probability distribution for a specified node
        and its parents in same format returned by Panda crosstab function.

        Args:
            node: Node for which distribution required.
            parents: Parents of node.

        Returns:
            Marginal distribution with parental value combos as columns,
            and node values as rows.
        """
        _check_marginal_distribution_args(self.dag.nodes, node, parents)

        # Generate possible values at every node {node: [poss values]}
        node_values = {n: c.node_values() for n, c in self.cnds.items()}

        # Loop through every possible combination of all variable values,
        # get its probability of occurrence and add it in to the running
        # marginal probability for that value of parental values and node value
        marginals = _accumulate_marginals(self, node, parents, node_values)

        # reconfigure the marginal probabilities into the Dataframe format
        # produced by Pandas crosstab so compatible with rest of code base
        if parents is None:
            return _marginal_frame(node, node_values[node], marginals[node])
        return _parental_marginal_frame(
            node, parents, node_values[node], marginals
        )

    def _dist(
        self,
        dist: List[Tuple[Dict[str, Any], float]],
        required: set,
        node: str,
        cpt: CPT,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Merge a node's CPT into marginal distribution.

        Args:
            dist: Current marginal distribution, format is
                [({n: v, ....}, pr), ...].
            required: Nodes to include in distribution.
            node: Node being added to distribution.
            cpt: CPT for node being added.

        Returns:
            Updated marginal distribution with node in.
        """
        # print('_dist: dist={}, required={}, node={}'
        #       .format(dist, required, node))
        parents = cpt.parents()
        result: Dict[Any, Any] = {}
        for entry in dist:  # Loop over entries in current marginal

            # extract parental values for this entry

            parent_values = (
                None
                if parents is None
                else {n: v for n, v in entry[0].items() if n in parents}
            )

            # loop over items in PMF for this entry's parental values
            # getting this node's value and associated probability

            for value, prob in cpt.cdist(parent_values).items():

                # construct a new marginal entry key which contains
                # all required nodes including current node

                values = frozenset(
                    {(n, v) for n, v in entry[0].items() if n in required}
                    | {(node, value)}
                )

                # Accumulate the probabilities for these new marginal
                # entries - the new probability is the old marginal entry
                # probability x the probability of this node's PMF entry

                result[values] = result.get(values, 0.0) + prob * entry[1]

        result_list = [({e[0]: e[1] for e in v}, p) for v, p in result.items()]
        return result_list

    def _build_marginals(
        self, nodes: List[str]
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Build the marginal distribution of a set of nodes.

        Args:
            nodes: Nodes for which the marginal distribution is required.

        Returns:
            Marginal distribution as [({node: value, ...}, prob), ...].
        """
        order, parents, children = _ordered_required_nodes(self.dag, nodes)

        required: set = set()  # running set of nodes of interested
        dist: List[Tuple[Dict[str, Any], float]] = [({}, 1.0)]

        for node in order:  # go down the order
            required = required | {node}

            # children updated to include only those further down order
            children = {n: c - {node} for n, c in children.items()}

            # marginalise are those nodes we wish to marginalise out here,
            # and remove them from set of nodes of interest
            marginalise = {
                n for n in required if n not in nodes and len(children[n]) == 0
            }
            required -= marginalise

            # update the marginal distribution with current node pmfs,
            # but marginalising out those nodes no longer required
            dist = self._dist(dist, required, node, self.cnds[node])

            self.cached_marginals.put(dist)  # cache entries down order

        return dist

    def marginals(self, nodes: List[str]) -> DataFrame:
        """Return marginal distribution for specified nodes.

        Args:
            nodes: Nodes for which marginal distribution required.

        Returns:
            Marginal distribution in same format returned by Pandas
            crosstab function.

        Raises:
            TypeError: If arguments have bad type.
            ValueError: If arguments contain bad values.
        """
        _check_marginal_nodes(self.dag.nodes, nodes)

        # Construct a topological ordering of all the nodes

        nodes = list(nodes)  # nodes we are interested in

        dist = self.cached_marginals.get(nodes)
        # print('Cache {} for {}'
        #       .format('MISS' if dist is None else 'HIT', nodes))
        if not dist:
            dist = self._build_marginals(nodes)

        return _marginals_frame(nodes, dist, self.cnds)

    def lnprob_case(
        self, case_values: Dict[str, Any], base: Union[int, str] = 10
    ) -> Optional[float]:
        """Return log of probability of set of node values (case) occuring.

        Args:
            case_values: Value for each node {node: value}.
            base: Logarithm base to use - 2, 10 or 'e'.

        Returns:
            Log of probability of case occuring, or None if case has zero
            probability.

        Raises:
            TypeError: If arguments wrong type.
            ValueError: If arguments have invalid values.
        """
        _check_lnprob_args(self.dag.nodes, case_values, base)

        lnprob = 0.0
        for node in self.dag.ordered_nodes():
            pvs = _parental_values_for(self.dag.parents, node, case_values)
            node_lnprob = _node_lnprob(
                self.cnds[node], pvs, case_values[node], base
            )
            if node_lnprob is None:
                return None
            lnprob += node_lnprob

        return float(lnprob)

    def generate_cases(
        self, n: int, outfile: Optional[str] = None, pseudo: bool = True
    ) -> DataFrame:
        """Generate specified number of random data cases for this BN.

        Args:
            n: Number of cases to generate.
            outfile: Name of file to write instance to.
            pseudo: If pseudo-random (i.e. repeatable cases) to be produced,
                otherwise truly random.

        Returns:
            Random data cases.

        Raises:
            TypeError: If arguments not of correct type.
            ValueError: If invalid number of rows requested.
            FileNotFoundError: If outfile in nonexistent folder.
        """
        if (
            not isinstance(n, int)
            or isinstance(n, bool)
            or (outfile is not None and not isinstance(outfile, str))
            or not isinstance(pseudo, bool)
        ):
            raise TypeError("generate_cases called with bad arg types")

        if n < 1 or n > 100000000:
            raise ValueError("generate_cases called with bad n")

        set_random_seed(1234 if pseudo else None)  # set pseudo-random or not

        cases: Dict[str, List[Any]] = {node: [] for node in self.dag.nodes}
        for count in range(0, n):
            for node in self.dag.ordered_nodes():
                pvs = (
                    None
                    if node not in self.dag.parents
                    else {p: cases[p][count] for p in self.dag.parents[node]}
                )
                cases[node].append(self.cnds[node].random_value(pvs))

        dtype = {
            n: "category" if isinstance(cnd, CPT) else "float32"
            for n, cnd in self.cnds.items()
        }
        cases_df: DataFrame = DataFrame(cases).astype(dtype=dtype)

        if outfile is not None:
            write_dataframe(cases_df, outfile)

        return cases_df

    def __eq__(self, other: object) -> bool:
        """Compare another BN with this one.

        Args:
            other: The other BN to compare with this one.

        Returns:
            True, if other BN is same as this one.
        """
        return (
            isinstance(other, BN)
            and self.dag.nodes == other.dag.nodes
            and self.dag.edges == other.dag.edges
            and self.cnds == other.cnds
        )
