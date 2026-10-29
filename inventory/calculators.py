"""Pure inventory planning calculators; no UI, persistence, or database dependencies."""
from dataclasses import dataclass
import math


def _number(value, name, *, positive=False, nonnegative=False):
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a number") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    if positive and result <= 0:
        raise ValueError(f"{name} must be positive")
    if nonnegative and result < 0:
        raise ValueError(f"{name} must be nonnegative")
    return result


def calculate_eoq(annual_demand, ordering_cost, holding_cost, operating_days=365, unit_purchase_price=None):
    d = _number(annual_demand, "annual_demand", positive=True)
    s = _number(ordering_cost, "ordering_cost", positive=True)
    h = _number(holding_cost, "holding_cost", positive=True)
    days = _number(operating_days, "operating_days", positive=True)
    if not days.is_integer():
        raise ValueError("operating_days must be a whole number")
    # Log space avoids overflowing the intermediate 2*D*S for large finite inputs.
    try:
        quantity = math.exp((math.log(2) + math.log(d) + math.log(s) - math.log(h)) / 2)
    except OverflowError as exc:
        raise ValueError("EOQ results exceed the supported numeric range") from exc
    orders = d / quantity
    ordering = orders * s
    holding = (quantity / 2) * h
    result = {"eoq": quantity, "orders_per_year": orders,
            "order_interval_days": days / orders, "annual_ordering_cost": ordering,
            "annual_holding_cost": holding, "relevant_annual_cost": ordering + holding}
    if unit_purchase_price is not None:
        price = _number(unit_purchase_price, "unit_purchase_price", nonnegative=True)
        result["annual_purchase_cost"] = d * price
        result["total_annual_cost"] = result["relevant_annual_cost"] + result["annual_purchase_cost"]
    if not all(math.isfinite(value) for value in result.values()):
        raise ValueError("EOQ results exceed the supported numeric range")
    return result


def calculate_rop(average_demand, lead_time, safety_stock=0):
    demand = _number(average_demand, "average_demand", nonnegative=True)
    lead = _number(lead_time, "lead_time", nonnegative=True)
    safety = _number(safety_stock, "safety_stock", nonnegative=True)
    expected = demand * lead
    return {"rop": expected + safety, "lead_time_demand": expected, "safety_stock": safety}


@dataclass(frozen=True)
class MRPPeriod:
    period: int
    gross_requirements: float
    scheduled_receipts: float
    projected_available: float
    net_requirements: float
    planned_order_receipts: float
    planned_order_releases: float


@dataclass(frozen=True)
class MRPResult:
    rows: tuple[MRPPeriod, ...]
    releases_before_horizon: tuple[tuple[int, float], ...]


def calculate_mrp(gross_requirements, initial_on_hand, scheduled_receipts=None,
                  lead_time=0, lot_sizing="LFL", fixed_order_quantity=None,
                  poq_interval=None):
    gross = tuple(_number(v, f"gross_requirements[{i}]", nonnegative=True)
                  for i, v in enumerate(gross_requirements))
    if not gross:
        raise ValueError("Planning horizon must contain at least one period")
    initial = _number(initial_on_hand, "initial_on_hand", nonnegative=True)
    lead_value = _number(lead_time, "lead_time", nonnegative=True)
    if not lead_value.is_integer():
        raise ValueError("lead_time must be a whole number of periods")
    lead = int(lead_value)
    scheduled = tuple(scheduled_receipts or (0,) * len(gross))
    if len(scheduled) != len(gross):
        raise ValueError("scheduled_receipts must match planning horizon")
    scheduled = tuple(_number(v, f"scheduled_receipts[{i}]", nonnegative=True)
                      for i, v in enumerate(scheduled))
    method = str(lot_sizing).upper().replace("-", "")
    if method not in ("LFL", "FOQ", "POQ"):
        raise ValueError("lot_sizing must be LFL, FOQ, or POQ")
    quantity = None
    interval = None
    if method == "FOQ":
        quantity = _number(fixed_order_quantity, "fixed_order_quantity", positive=True)
    if method == "POQ":
        interval_value = _number(poq_interval, "poq_interval", positive=True)
        if not interval_value.is_integer():
            raise ValueError("poq_interval must be a whole number of periods")
        interval = int(interval_value)

    balances, nets, receipts = [], [], [0.0] * len(gross)
    available = initial
    # Net requirements are computed without planned receipts; POQ groups these
    # uncovered requirements into fixed period buckets from the first shortage.
    for i, (need, scheduled_in) in enumerate(zip(gross, scheduled)):
        net = max(0.0, need - (available + scheduled_in))
        nets.append(net)
        if net > 0:
            if method == "LFL":
                order = net
            elif method == "FOQ":
                order = math.ceil(net / quantity) * quantity
            else:
                end = min(len(gross), i + interval)
                order = max(0.0, sum(gross[i:end]) - available - sum(scheduled[i:end]))
            receipts[i] = order
        available = available + scheduled_in + receipts[i] - need
        balances.append(available)
    rows = []
    releases = [0.0] * len(gross)
    before = []
    for i in range(len(gross)):
        release_index = i - lead
        release = receipts[i]
        if release and release_index >= 0:
            releases[release_index] += release
        elif release:
            before.append((i + 1 - lead, release))
        rows.append(MRPPeriod(i + 1, gross[i], scheduled[i], balances[i], nets[i],
                              receipts[i], 0.0))
    rows = [MRPPeriod(row.period, row.gross_requirements, row.scheduled_receipts,
                      row.projected_available, row.net_requirements,
                      row.planned_order_receipts, releases[i])
            for i, row in enumerate(rows)]
    return MRPResult(tuple(rows), tuple(before))
