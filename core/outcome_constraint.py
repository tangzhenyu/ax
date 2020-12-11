#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import annotations

import logging
from typing import Dict, Optional

from ax.core.metric import Metric
from ax.core.types import ComparisonOp
from ax.utils.common.base import Base
from ax.utils.common.logger import get_logger


logger: logging.Logger = get_logger(__name__)

CONSTRAINT_WARNING_MESSAGE: str = (
    "Constraint on {name} appears invalid: {bound} bound on metric "
    + "for which {is_better} values are better."
)
LOWER_BOUND_MISMATCH: Dict[str, str] = {"bound": "Lower", "is_better": "lower"}
UPPER_BOUND_MISMATCH: Dict[str, str] = {"bound": "Upper", "is_better": "higher"}


class OutcomeConstraint(Base):
    """Base class for representing outcome constraints.

    Outcome constraints may of the form metric >= bound or metric <= bound,
    where the bound can be expressed as an absolute measurement or relative
    to the status quo (if applicable).

    Attributes:
        metric: Metric to constrain.
        op: Specifies whether metric should be greater or equal
            to, or less than or equal to, some bound.
        bound: The bound in the constraint.
        relative: Whether you want to bound on an absolute or relative
            scale. If relative, bound is the acceptable percent change.

    """

    def __init__(
        self, metric: Metric, op: ComparisonOp, bound: float, relative: bool = True
    ) -> None:
        self._validate_metric_constraint(metric=metric, op=op)
        self._metric = metric
        self._op = op
        self.bound = bound
        self.relative = relative

    @property
    def metric(self) -> Metric:
        return self._metric

    @metric.setter
    def metric(self, metric: Metric) -> None:
        self._validate_metric_constraint(metric=metric, op=self.op)
        self._metric = metric

    @property
    def op(self) -> ComparisonOp:
        return self._op

    @op.setter
    def op(self, op: ComparisonOp) -> None:
        self._validate_metric_constraint(metric=self.metric, op=op)
        self._op = op

    def clone(self) -> OutcomeConstraint:
        """Create a copy of this OutcomeConstraint."""
        return OutcomeConstraint(
            metric=self.metric.clone(),
            op=self.op,
            bound=self.bound,
            relative=self.relative,
        )

    @staticmethod
    def _validate_metric_constraint(metric: Metric, op: ComparisonOp) -> None:
        """Ensure constraint is compatible with metric definition.

        Args:
            metric: Metric to constrain.
            op: Specifies whether metric should be greater or equal
                to, or less than or equal to, some bound.
        """
        fmt_data = None
        if metric.lower_is_better is not None:
            if op == ComparisonOp.GEQ and metric.lower_is_better:
                fmt_data = LOWER_BOUND_MISMATCH
            if op == ComparisonOp.LEQ and not metric.lower_is_better:
                fmt_data = UPPER_BOUND_MISMATCH
        if fmt_data is not None:
            fmt_data["name"] = metric.name
            logger.debug(CONSTRAINT_WARNING_MESSAGE.format(**fmt_data))

    def __repr__(self) -> str:
        op = ">=" if self.op == ComparisonOp.GEQ else "<="
        relative = "%" if self.relative else ""
        return f"OutcomeConstraint({self.metric.name} {op} {self.bound}{relative})"


class ObjectiveThreshold(OutcomeConstraint):
    """Class for representing Objective Thresholds.

    An objective threshold represents the threshold for an objective metric
    to contribute to hypervolume calculations. A list containing the objective
    threshold for each metric collectively form a reference point.

    Objective thresholds may bound the metric from above or from below.
    The bound can be expressed as an absolute measurement or relative
    to the status quo (if applicable).

    The direction of the bound is inferred from the Metric's lower_is_better attribute.

    Attributes:
        metric: Metric to constrain.
        bound: The bound in the constraint.
        relative: Whether you want to bound on an absolute or relative
            scale. If relative, bound is the acceptable percent change.
        op: automatically inferred, but manually overwritable.
            specifies whether metric should be greater or equal to, or less
            than or equal to, some bound.
    """

    def __init__(
        self,
        metric: Metric,
        bound: float,
        relative: bool = False,
        op: Optional[ComparisonOp] = None,
    ) -> None:
        if metric.lower_is_better is None and op is None:
            raise ValueError(
                (
                    f"Metric {metric} must have attribute `lower_is_better` set or "
                    f"op {op} must be manually specified."
                )
            )
        elif op is None:
            op = ComparisonOp.LEQ if metric.lower_is_better else ComparisonOp.GEQ
        super().__init__(metric=metric, op=op, bound=bound, relative=relative)

    def clone(self) -> ObjectiveThreshold:
        """Create a copy of this ObjectiveThreshold."""
        return ObjectiveThreshold(
            metric=self.metric.clone(),
            bound=self.bound,
            relative=self.relative,
            op=self.op,
        )

    def __repr__(self) -> str:
        op = ">=" if self.op == ComparisonOp.GEQ else "<="
        relative = "%" if self.relative else ""
        return f"ObjectiveThreshold({self.metric.name} {op} {self.bound}{relative})"
