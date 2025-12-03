#
# Conditional Node Distribution at a node which will have concrete
# implementations as CPT or LinearGuassian etc.

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union


class CND(ABC):
    """Conditional Node Distribution for a node conditional on parental values.

    Concrete subclasses support specific kinds of distributions,
    for example, CPT (multinomial), LinearGaussian etc.

    Attributes:
        has_parents (bool): Whether CND is for a node with parents.
        free_params (int): Number of free params in CND.
    """

    has_parents: bool
    free_params: int

    def __init__(self) -> None:
        pass

    @classmethod
    @abstractmethod
    def fit(cls,
            node: str,
            parents: Optional[Tuple[str, ...]],
            data: Any,
            autocomplete: bool = True
            ) -> Tuple[Tuple[type, Dict[str, Any]], Optional[int]]:
        """Constructs a CND (Conditional Node Distribution) from data.

        Args:
            node (str): Node that CND applies to.
            parents (tuple): Parents of node.
            data (Data): Data to fit CND to.
            autocomplete (bool): Whether complete CPT tables.

        Returns:
            tuple: (cnd_spec, estimated_pmfs) where
                cnd_spec is (CPT class, cpt_spec for CPT())
                estimated_pmfs int/None - only for CPTs.
        """
        pass

    @abstractmethod
    def cdist(self, parental_values: Optional[Dict[str, Any]] = None) -> Any:
        """Return conditional distribution for specified parental values.

        Args:
            parental_values (dict, optional): Parental values for which dist.
                required for non-orphans.

        Raises:
            TypeError: If args are of wrong type.
            ValueError: If args have invalid or conflicting values.
        """
        pass

    @abstractmethod
    def random_value(self, pvs: Optional[Dict[str, Any]]) -> Union[str, float]:
        """Generate a random value for a node given the value of its parents.

        Args:
            pvs (dict, optional): Parental values, {parent1: value1, ...}.

        Returns:
            str or float: Random value for node.
        """

    @abstractmethod
    def parents(self) -> List[str]:
        """Return parents of node CND relates to.

        Returns:
            list: Parent node names in alphabetical order.
        """
        pass

    @abstractmethod
    def to_spec(self, name_map: Dict[str, str]) -> Dict[str, Any]:
        """Returns external specification format of CND,
        renaming nodes according to a name map.

        Args:
            name_map (dict): Map of node names {old: new}.

        Returns:
            dict: CND specification with renamed nodes.
        """
        pass

    @abstractmethod
    def __str__(self) -> str:
        """Human-friendly description of the contents of the CND."""
        pass

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        """Return whether two CNDs are the same allowing for
        probability rounding errors.

        Args:
            other (CND): CND to compared to self.

        Returns:
            bool: Whether CPTs are PRACTICALLY the same.
        """
        pass

    @abstractmethod
    def validate_parents(self,
                         node: str,
                         parents: Dict[str, List[str]],
                         node_values: Dict[str, List[str]]) -> None:
        """Checks every CND's parents and (categorical) parental values
        are consistent.

        Validates consistency with the other relevant CNDs
        and the DAG structure.

        Args:
            node (str): Name of node.
            parents (dict): Parents of all nodes {node: parents}.
            node_values (dict): Values of each cat. node {node: values}.
        """
        pass

    @classmethod
    def validate_cnds(cls,
                      nodes: List[str],
                      cnds: Dict[str, 'CND'],
                      parents: Dict[str, List[str]]) -> None:
        """Checks that all CNDs in graph are consistent with one another
        and with graph structure.

        Args:
            nodes (list): BN nodes.
            cnds (dict): Set of CNDs for the BN, {node: cnd}.
            parents (dict): Parents of non-orphan nodes, {node: parents}.

        Raises:
            TypeError: If invalid types used in arguments.
            ValueError: If any inconsistent values found.
        """

        # check 1:1 mapping between node and CNDs keys

        if sorted(list(cnds.keys())) != sorted(nodes):
            raise ValueError('CND.validate_cnds() bad/missing nodes in cnds')

        # collect values (states) for all categorical nodes

        values = {}
        for node, cnd in cnds.items():
            if (cnd.__class__.__name__ == 'CPT' and
                    hasattr(cnd, 'values')):
                values[node] = cnd.values

        # check each node's CPT consistent with parents and parent values

        for node, cnd in cnds.items():
            cnd.validate_parents(node, parents, values)

    @classmethod
    def _map_keys(cls,
                  odict: Dict[str, Any],
                  name_map: Dict[str, str]) -> Dict[str, Any]:
        """Renames some keys in a dict, re-ordering it by new key names.

        Args:
            odict (dict): Some of keys of this dict will be renamed.
            name_map (dict): Name mapping for some keys in odict.

        Returns:
            dict: With keys renamed, and re-ordered.
        """
        ndict = {name_map[k] if k in name_map else k: v
                 for k, v in odict.items()}
        return {k: ndict[k] for k in sorted(ndict)}
