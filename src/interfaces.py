from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime as dt
from typing import Optional


import numpy as np


@dataclass
class RetireeClass(ABC):
    age: int
    current_income: float
    desired_retirement_income: float
    year: int = field(default_factory=lambda: dt.today().year)
    life_expectancy: int = 120
    retirement_age: int = 67
    raise_rate: float = 0.03
    max_income: Optional[float] = None
    max_contrib_pct: float = 1.0
    min_net_income: float = 0.
    effective_tax_rate: float = 0.35
    income_history: Optional[np.array] = field(default=None, repr=False)
    inflation_rate: float = 0.0
