#
# Linear Guassian implementation of Conditional Node Distribution


from math import sqrt
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import numpy as np
from numpy import sum as npsum
from pandas import DataFrame
from sklearn.linear_model import LinearRegression  # type: ignore

from causaliq_core.utils.math import rndsf
from causaliq_core.utils.random import random_generator
from causaliq_core.utils.same import dicts_same, values_same


class LinGauss():
    """Conditional Linear Gaussian Distribution.

    Args:
        lg (dict): Specification of Linear Gaussian in following form:
            {'coeffs': {node: coeff}, 'mean': mean, 'sd': sd}

    Attributes:
        coeffs (dict): Linear coefficient of parents {parent: coeff}.
        mean (float): Mean of Gaussian noise (aka intercept, mu).
        sd (float): S.D. of Gaussian noise (aka sigma).

    Raises:
        TypeError: If called with bad arg types.
        ValueError: If called with bad arg values.
    """

    MAX_SF = 10  # max no of significant
    _model = None

    def __init__(self, lg: Dict[str, Any]) -> None:

        if (not isinstance(lg, dict)
            or set(lg) != {'coeffs', 'mean', 'sd'}
            or not isinstance(lg['coeffs'], dict)
            or not all([isinstance(c, str) and isinstance(v, float)
                        for c, v in lg['coeffs'].items()])
            or not isinstance(lg['mean'], float)
                or not isinstance(lg['sd'], float)):
            raise TypeError('LinGauss() bad arg types')

        if lg['sd'] < 0.0:
            raise ValueError('LinGauss() bad arg value')

        self.coeffs = lg['coeffs']
        self.mean = lg['mean']
        self.sd = lg['sd']
        self.has_parents = True if len(self.coeffs) > 0 else False
        self.free_params = 2 + len(self.coeffs)

    @classmethod
    def fit(cls,
            node: str,
            parents: Optional[Tuple[str, ...]],
            data: Union[DataFrame, Any],  # Accept DataFrame or legacy Pandas
            autocomplete: bool = True
            ) -> Tuple[Tuple[type, Dict[str, Any]], None]:
        """Fit a Linear Gaussian to data.

        Args:
            node (str): Node that Linear Gaussian applies to.
            parents (tuple, optional): Parents of node.
            data (DataFrame or Data): Data to fit Linear Gaussian to.
            autocomplete (bool): Not used for Linear Gaussian.

        Returns:
            tuple: (lg_spec, None) where lg is (LinGauss class, lg_spec).

        Raises:
            TypeError: With bad arg types.
            ValueError: With bad arg values.
        """
        # Accept both pandas DataFrame and legacy Pandas wrapper
        is_dataframe = isinstance(data, DataFrame)
        is_legacy_pandas = data.__class__.__name__ == 'Pandas'

        if (not isinstance(node, str)
            or (parents is not None
                and (not isinstance(parents, tuple) or len(parents) == 0
                     or not all([isinstance(p, str) for p in parents])))
            or not (is_dataframe or is_legacy_pandas)
                or autocomplete is not True):
            raise TypeError('LinGauss.fit() bad arg type')

        # Helper function to get values from either DataFrame or legacy Pandas
        def get_values(columns: Tuple[str, ...]) -> np.ndarray:
            if is_dataframe:
                # Standard pandas DataFrame
                values = data[list(columns)].values
                return cast(np.ndarray, np.asarray(values))
            else:
                # Legacy Pandas wrapper - use getattr to avoid mypy issues
                values_method = getattr(data, "values", None)
                if values_method is not None:
                    result = values_method(columns)
                    return cast(np.ndarray, np.asarray(result))
                else:
                    raise ValueError(
                        "Data object does not support values() method"
                        )  # pragma: no cover

        # Validate that required columns exist in data
        columns_to_check = [node] + (list(parents) if parents else [])
        if is_dataframe:
            missing_cols = [col for col in columns_to_check
                            if col not in data.columns]
            if missing_cols:
                raise ValueError('LinGauss.fit() columns not '
                                 f'in data: {missing_cols}')
        else:
            # For legacy Pandas, let the .values() call handle validation
            pass

        if parents is not None and node in parents:
            raise ValueError('LinGauss.fit() node cannot be its own parent')

        if parents is None:

            # Just need to determine mean and sd for univariate Gaussian

            values = get_values((node, ))
            lg = {'mean': values.mean().item(), 'sd': values.std().item(),
                  'coeffs': {}}

        else:

            # Get values for child and its parents and fit a linear regression
            # model for the parents predicting the child value

            values = get_values(tuple([node] + list(parents)))
            if LinGauss._model is None:
                LinGauss._model = LinearRegression()
            LinGauss._model.fit(values[:, 1:], values[:, 0])

            # Parent coefficientsare the linear regression coefficents and
            # the regression intercept is the mean of the child Gaussian

            coeffs = {p: LinGauss._model.coef_[i].item()
                      for i, p in enumerate(parents)}
            mean = LinGauss._model.intercept_.item()

            # Use model to predict child values, calculate residuals and
            # hence noise S.D.

            residuals = values[:, 0] - LinGauss._model.predict(values[:, 1:])
            sd = sqrt(npsum(residuals ** 2) / len(residuals))

            lg = {'mean': mean, 'sd': sd, 'coeffs': coeffs}

        return ((LinGauss, lg), None)

    def cdist(self,
              parental_values: Optional[Dict[str, float]] = None
              ) -> Tuple[float, float]:
        """Return conditional distribution for specified parental values.

        Args:
            parental_values (dict, optional): Parental values for which dist.
                required for non-orphans.

        Returns:
            tuple: (mean, sd) of child Gaussian distribution.

        Raises:
            TypeError: If args are of wrong type.
            ValueError: If args have invalid or conflicting values.
        """
        if ((self.coeffs == {} and parental_values is not None)
            or (len(self.coeffs) > 0 and parental_values is None)
            or (len(self.coeffs) > 0 and parental_values is not None and
                set(self.coeffs) != set(parental_values))):
            raise TypeError(
                'lingauss.cpt() coeffs/parent values mismatch')

        if parental_values is None:
            parental_values = {}

        mean = self.mean + sum([parental_values[p] * self.coeffs[p]
                                for p in self.coeffs])
        return mean, self.sd

    def random_value(self, pvs: Optional[Dict[str, float]]) -> float:
        """Generate a random value for a node given the value of its parents.

        Args:
            pvs (dict, optional): Parental values, {parent1: value1, ...}.

        Returns:
            str or float: Random value for node.
        """
        mean, sd = self.cdist(pvs)
        return mean + random_generator().normal() * sd

    def parents(self) -> List[str]:
        """Return parents of node CND relates to.

        Returns:
            list: Parent node names in alphabetical order.
        """
        return sorted(list(self.coeffs.keys()))

    def to_spec(self, name_map: Dict[str, str]) -> Dict[str, Any]:
        """Returns external specification format of LinGauss,
        renaming nodes according to a name map.

        Args:
            name_map (dict): Map of node names {old: new}.

        Returns:
            dict: LinGauss specification with renamed nodes.

        Raises:
            TypeError: If bad arg type.
            ValueError: If bad arg value, e.g. coeff keys not in map.
        """
        if (not isinstance(name_map, dict)
                or not all([isinstance(k, str) for k in name_map])
                or not all([isinstance(v, str) for v in name_map.values()])):
            raise TypeError('LinGauss.to_spec() bad arg type')

        if len(set(self.coeffs) - set(name_map)) != 0:
            raise ValueError('LinGauss.to_spec() bad arg value')

        coeffs = {name_map[n]: v for n, v in self.coeffs.items()}
        return {'coeffs': coeffs, 'mean': self.mean, 'sd': self.sd}

    def __str__(self) -> str:
        """Human-friendly formula description of the Linear Gaussian."""
        def _term(node: str, coeff: float) -> str:
            # val = _val(coeff)
            val = rndsf(coeff, self.MAX_SF)
            return ('' if val == '0.0' else ('{}*{}'.format(val, node)
                    if coeff < 0 else '+{}*{}'.format(val, node)))

        terms = ''.join([_term(n, self.coeffs[n])
                         for n in sorted(self.coeffs)])
        terms = terms[1:] if len(terms) > 0 and terms[0] == '+' else terms
        normal = 'Normal({},{})'.format(rndsf(self.mean, self.MAX_SF),
                                        rndsf(self.sd, self.MAX_SF))
        return '{}{}'.format(terms + '+' if len(terms) else '', normal)

    def __eq__(self, other: object) -> bool:
        """Return whether two CNDs are the same allowing for
        probability rounding errors.

        Args:
            other (CND): CND to compared to self.

        Returns:
            bool: Whether LinGauss objects are the same up to 10 sf.
        """
        return (isinstance(other, LinGauss)
                and values_same(self.mean, other.mean, sf=10)
                and values_same(self.sd, other.sd, sf=10)
                and set(self.coeffs) == set(other.coeffs)
                and dicts_same(self.coeffs, other.coeffs, sf=10))

    def validate_parents(self,
                         node: str,
                         parents: Dict[str, List[str]],
                         node_values: Dict[str, List[str]]) -> None:
        """Check LinGauss coeff keys consistent with parents in DAG.

        Args:
            node (str): Name of node.
            parents (dict): Parents of all nodes defined in DAG.
            node_values (dict): Values of each cat. node [UNUSED].
        """
        if ((node not in parents and len(self.coeffs) > 0)
                or (node in parents
                    and set(parents[node]) != set(self.coeffs))):
            raise ValueError('LinGauss.validate_parents() parent mismatch')
