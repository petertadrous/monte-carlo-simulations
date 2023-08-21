from dataclasses import dataclass


import numpy as np


from src.interfaces import RetireeClass as Retiree


def reduced_roth_ira(modified_agi: float, thresh: float = 138_000., max_limit: float = 6_500.):
    line_2 = modified_agi - thresh
    line_3 = line_2 / 15_000.
    line_4 = max_limit * line_3
    line_5 = max_limit - line_4
    return np.clip(line_5, 0, max_limit)


@dataclass
class IRA:
    retiree: Retiree
    current_total_max_lt: float = 6_500.
    current_total_max_gte: float = 7_500.
    income_limit: float = 138_000
    estimated_max_growth: float = 0.005
    estimated_max_lag: int = 10
    inflection_year: int = 50
    
    def __post_init__(self):
        self.__calc_ira_array()
        
    def __calc_ira_array(self):
        inflection_mask = self.retiree.ages_arr[self.retiree.age:self.retiree.retirement_age + 1] < self.inflection_year
        total_max_arr = np.where(inflection_mask, self.current_total_max_lt, self.current_total_max_gte)
        
        growth = np.ones_like(total_max_arr)
        growth[self.estimated_max_lag::self.estimated_max_lag] += self.estimated_max_growth
        growth = growth.cumprod()
        pad_width = (self.retiree.age, self.retiree.life_expectancy - self.retiree.retirement_age)
        
        income_limit_growth = (self.income_limit * growth).round(2)
        self.total_max_arr = total_max_arr * growth
        self.roth_max_arr = reduced_roth_ira(
            modified_agi=self.retiree.income_arr[self.retiree.age:self.retiree.retirement_age + 1],
            thresh=income_limit_growth,
            max_limit=self.total_max_arr,
        )
        
        self.total_max_arr = np.pad(self.total_max_arr, pad_width).round(2)
        self.roth_max_arr = np.pad(self.roth_max_arr, pad_width).round(2)

@dataclass
class Four01k:
    retiree: Retiree
    current_employee_max_lt: float = 22_500.
    current_employee_max_gte: float = 30_000.
    current_combined_max_lt: float = 66_000.
    current_combined_max_gte: float = 73_500.
    employer_match_rate: float = 0.06
    employer_match_ratio: float = 0.5
    estimated_max_growth: float = 0.005
    estimated_max_lag: int = 10
    inflection_year: int = 50
    
    def __post_init__(self):
        self.__calc_401k_array()
        
    def __calc_401k_array(self):
        inflection_mask = self.retiree.ages_arr[self.retiree.age:self.retiree.retirement_age + 1] < self.inflection_year
        
        self.employee_max_arr = np.where(inflection_mask, self.current_employee_max_lt, self.current_employee_max_gte)
        self.combined_max_arr = np.where(inflection_mask, self.current_combined_max_lt, self.current_combined_max_gte)
        
        growth = np.ones_like(self.employee_max_arr)
        growth[self.estimated_max_lag::self.estimated_max_lag] += self.estimated_max_growth
        growth = growth.cumprod()

        pad_width = (self.retiree.age, self.retiree.life_expectancy - self.retiree.retirement_age)
        
        self.employee_max_arr = np.pad(growth * self.employee_max_arr, pad_width).round(2)
        self.roth_max_arr = np.clip(self.retiree.desired_retirement_income - self.employee_max_arr,
                                    0., self.employee_max_arr).round(2)
        self.roth_max_arr = np.where(self.retiree.income_arr < self.retiree.desired_retirement_income,self.roth_max_arr, 0)
        self.combined_max_arr = np.pad(growth * self.combined_max_arr, pad_width).round(2)

    def employer_max_arr(self, employee_max_arr):
        return np.clip(
            employee_max_arr * self.employer_match_ratio,
            0., self.retiree.income_arr * self.employer_match_rate * self.employer_match_ratio,
        ).round(2)