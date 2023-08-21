from dataclasses import dataclass, field
from datetime import datetime as dt
from typing import Optional


import numpy as np
import pandas as pd


from src.accounts import Four01k, IRA
from src.interfaces import RetireeClass
from src.ssi import calc_ssi_income_array
from src.tax_computations import IncomeTaxes


@dataclass
class Retiree(RetireeClass):
    
    def __post_init__(self):
        self.__calc_income_array()
        self.years_arr = np.arange(self.year - self.age, self.year + 1 + (self.life_expectancy - self.age))
        self.ages_arr = np.arange(0, self.life_expectancy + 1)
        self.ssi_arr = calc_ssi_income_array(self)
        self.withdrawal_arr = np.where(
            self.ages_arr <= self.retirement_age, 0., self.desired_retirement_income - self.ssi_arr
        )
        self.inflation_arr = (np.repeat([0.0, -self.inflation_rate/(1+self.inflation_rate)],
                                        [self.age, self.life_expectancy]))[:self.life_expectancy + 1]

    def __calc_income_array(self):
        if self.income_history is None:
            self.income_history = np.zeros((self.age,))
        elif self.income_history.shape[0] < self.age:
            self.income_history = np.pad(self.income_history, ((self.age) - self.income_history.shape[0], 0))
        else:
            self.income_history = self.income_history[:-(self.age)]
        
        working_income = np.array([self.current_income] * (self.retirement_age - self.age + 1))
        cumulative_raise = (np.pad(np.array([self.raise_rate] * (self.retirement_age - self.age)), (1,0)) + 1).cumprod()
        working_income = np.clip(np.concatenate((self.income_history, cumulative_raise * working_income)), 0, self.max_income)
        if self.life_expectancy + 1 > working_income.shape[0]:
            self.income_arr = np.pad(working_income, (0,self.life_expectancy + 1 - working_income.shape[0]))
        else:
            self.income_arr = working_income[:self.life_expectancy + 1]
        self.income_arr = self.income_arr.round(2)


def make_ret_df(
    ret: RetireeClass,
    ret_401k: Four01k,
    ret_ira: IRA,
    starting_roth_ira: float = 0.,
    starting_roth_401k: float = 0.,
    starting_trad_ira: float = 0.,
    starting_trad_401k: float = 0.,
    starting_trad_match_401k: float = 0.,
):
    ret_df = pd.DataFrame()

    ret_df['year'] = ret.years_arr
    ret_df['age'] = ret.ages_arr
    ret_df['earnings'] = ret.income_arr
    ret_df['net_earnings'] = 0.


    ret_df['r_401k_dep'] = 0.
    ret_df['t_401k_dep'] = 0.
    ret_df['t_401k_match_dep'] = 0.
    ret_df['r_ira_dep'] = 0.
    ret_df['t_ira_dep'] = 0.


    max_dep = np.clip( (ret.income_arr  * (1-ret.effective_tax_rate)) - ret.min_net_income, 0.0, ret.income_arr * (ret.max_contrib_pct))
    ret_df['r_ira_dep'] = np.clip(ret_ira.roth_max_arr, 0.0, max_dep ).round(2)
    max_dep = np.clip(max_dep - ret_df['r_ira_dep'].values , 0, None)
    
    ret_df['t_ira_dep'] = np.clip(
        ret_ira.total_max_arr - ret_df['r_ira_dep'].values,
        0.0, max_dep/(1+ret.effective_tax_rate)).round(2)
    max_dep = np.clip(max_dep - (ret_df['t_ira_dep'].values/(1+ret.effective_tax_rate)), 0, None)
    ret_df['r_401k_dep'] = np.clip(ret_401k.roth_max_arr, 0.0, max_dep ).round(2)
    max_dep = np.clip(max_dep - ret_df['r_401k_dep'].values , 0, None)
    ret_df['t_401k_dep'] = np.clip(
        ret_401k.employee_max_arr - ret_df['r_401k_dep'].values,
        0.0, max_dep/(1+ret.effective_tax_rate)).round(2)
    max_dep = np.clip(max_dep - (ret_df['t_401k_dep'].values/(1+ret.effective_tax_rate)), 0, None)
    ret_df['t_401k_match_dep'] = ret_401k.employer_max_arr(ret_df[['t_401k_dep', 'r_401k_dep']].sum(axis=1)).round(2)

    ret_df['net_earnings'] = (
        (
            ret_df['earnings'] - ret_df[['t_401k_dep','t_ira_dep']].sum(axis=1)
        ).apply(
            lambda x: IncomeTaxes(x, 'NY', 'NYC', 2022).get_after_tax_income()
        ) - ret_df[['r_401k_dep','r_ira_dep']].sum(axis=1)
    )

    ret_df.loc[ret.age, 'r_401k_dep'] += starting_roth_401k
    ret_df.loc[ret.age, 'r_ira_dep'] += starting_roth_ira
    ret_df.loc[ret.age, 't_401k_dep'] += starting_trad_401k
    ret_df.loc[ret.age, 't_401k_match_dep'] += starting_trad_match_401k
    ret_df.loc[ret.age, 't_ira_dep'] += starting_trad_ira

    ret_df['total_roth_dep'] = ret_df[['r_401k_dep','r_ira_dep']].sum(axis=1)
    ret_df['total_trad_dep'] = ret_df[['t_401k_dep','t_401k_match_dep','t_ira_dep']].sum(axis=1)

    ret_df['ssi_income'] = ret.ssi_arr
    ret_df['with'] = ret.withdrawal_arr

    return ret_df