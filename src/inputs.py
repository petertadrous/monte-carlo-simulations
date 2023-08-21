from dataclasses import dataclass, field
import copy
from typing import List, Optional


import numpy as np
from numpy.random import PCG64
import pandas as pd


@dataclass(frozen=True)
class ParametricOptimizationInputs:
    order: List[str] = field(default_factory=lambda: copy.deepcopy(['stocks', 'bonds', 'cash']))
    arithmetic_means: np.ndarray = field(default_factory=lambda: copy.deepcopy(np.array([8.70, 2.52, 0.69]) / 100), repr=False)
    geometric_means: np.ndarray = field(default_factory=lambda: copy.deepcopy(np.array([6.62, 2.28, 0.61]) / 100), repr=False)
    means: np.ndarray = field(init=False)
    stds: np.ndarray = field(default_factory=lambda: copy.deepcopy(np.array([20.39, 6.84, 3.90]) / 100))
    corr_matrix: np.ndarray = field(default_factory=lambda: copy.deepcopy(np.array([
        [1.0, 0.08, 0.09],
        [0.08, 1.0, 0.71],
        [0.09, 0.71, 1.0]])))
    cov_matrix: np.ndarray = field(init=False, repr=False)
    seed: Optional[int] = field(default=None, repr=False)
    cash_negative: bool = False
        
    def __post_init__(self):
        object.__setattr__(self, 'means', self.arithmetic_means)
        object.__setattr__(self, 'cov_matrix', np.outer(self.stds, self.stds) * self.corr_matrix)
        object.__setattr__(self, '_rand_gen', np.random.Generator(PCG64(self.seed)))
        
    def generate_normal(self, size: int = 30) -> np.ndarray:
        r = self._rand_gen.multivariate_normal(
            mean=self.means,
            cov=self.cov_matrix,
            size=size,
        )
        if not self.cash_negative:
            r[:,2] = np.clip(r[:,2], 0, 1)
        return r

    def reset(self):
        object.__setattr__(self, '_rand_gen', np.random.Generator(PCG64(self.seed)))


@dataclass
class HistoricalInputs:
    filepath: str = '/mnt/c/Users/peter/Documents/annual_real_returns_1871-2021.xlsx'
    sheetname: str = 'annual real returns'
    start_year: int = 1930
    cycle: bool = False
    def __post_init__(self):
        dataset = pd.read_excel(self.filepath, sheet_name=self.sheetname)
        if 'bills' not in dataset.columns:
            dataset['bills'] = 0.0
        dataset = dataset[dataset['year'] >= self.start_year]
        self.years_arr = dataset['year'].values
        self.historical_data = dataset[['stocks', 'bonds', 'bills']].values
        self.pointer = 0
        
    def generate_normal(self, size: int = 30) -> np.ndarray:
        if (self.cycle == False) and (self.pointer + size > self.historical_data.shape[0]):
            raise ValueError('Not enough historical data!')
        r = self.historical_data.take(range(self.pointer, self.pointer+size), mode='wrap', axis=0)
        self.pointer += 1
        return r
    
    def get_n_sims(self, size: int = 30) -> int:
        if self.cycle == False:
            return self.historical_data.shape[0] - size + 1
        return self.historical_data.shape[0]

    def reset(self):
        self.pointer = 0
