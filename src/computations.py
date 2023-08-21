import time
from typing import Dict, Optional, Union


import numpy as np
import pandas as pd


from src.inputs import ParametricOptimizationInputs
from src.interfaces import RetireeClass as Retiree


def compute_period_returns(
        contributions: np.array,
        allocations: np.ndarray,
        rates: np.ndarray,
) -> np.ndarray:
    rates_ev: np.array = (allocations * rates).sum(axis=1)
    cum_rates_ev = (np.triu(np.expand_dims(rates_ev, axis=0).repeat(rates_ev.shape[0], axis=0)) + 1).cumprod(axis=1)
    period_contribs = np.triu(contributions.reshape((-1,1)).repeat(contributions.shape, axis=1))
    realized_contribs = period_contribs * cum_rates_ev
    period_balances = realized_contribs.sum(axis=0).reshape((-1,1))
    return np.clip(period_balances * allocations, 0, None)


def compute_period_returns_with_rmd(
        contributions: np.array,
        allocations: np.ndarray,
        rates: np.ndarray,
        rmd: np.ndarray,
) -> np.ndarray:
    rates_ev: np.array = (allocations * rates).sum(axis=1)
    cum_rates_ev = (np.triu(np.expand_dims(rates_ev, axis=0).repeat(rates_ev.shape[0], axis=0)) + 1).cumprod(axis=1)
    cum_rates_ev = cum_rates_ev * rmd
    period_contribs = np.triu(contributions.reshape((-1,1)).repeat(contributions.shape, axis=1))
    realized_contribs = period_contribs * cum_rates_ev
    period_balances = realized_contribs.sum(axis=0).reshape((-1,1))
    return np.clip(period_balances * allocations, 0, None)


def calc_rmd(ret: Retiree):
    divisors = np.array([
        27.4, 26.5, 25.5, 24.6, 23.7,
        22.9, 22.0, 21.1, 20.2, 19.4,
        18.5, 17.7, 16.8, 16.0, 15.2,
        14.4, 13.7, 12.9, 12.2, 11.5,
        10.8, 10.1,  9.5,  8.9,  8.4,
         7.8,  7.3,  6.8,  6.4,  6.0,
         5.6,  5.2,  4.9,  4.6,  4.3,
         4.1,  3.9,  3.7,  3.5,  3.4,
         3.3,  3.1,  3.0,  2.9,  2.8,
         2.7,  2.5,  2.3,  2.0,  2.0,
    ])
    rmd_year = 72
    rmd_arr = np.concatenate((
        np.repeat(1, rmd_year),
        1 - (1/divisors),
        np.repeat(1 - (1/divisors[-1]), ret.life_expectancy - rmd_year)
    ))[:ret.life_expectancy + 1]
    return 1-rmd_arr, rmd_arr.cumprod()


def simulate(
        roth_contrib: np.ndarray,
        trad_contrib: np.ndarray,
        withdrawal: np.ndarray,
        allocations: np.ndarray,
        rates: np.ndarray,
        rmd_take: np.ndarray,
        rmd_remain: np.ndarray,
        tax_rate: float,
        inflation: Optional[Union[float, np.ndarray]] = None,
):
    trad = compute_period_returns_with_rmd(
        contributions=trad_contrib,
        allocations=allocations,
        rates=rates,
        rmd=rmd_remain,
    ).sum(axis=1).round(2)

#     print(trad.reshape((-1,1)).shape,np.ones_like(trad.reshape((-1,1))).shape,inflation.reshape((-1,1)).shape)
    trad_infl = compute_period_returns(
        contributions=np.diff(trad, prepend=0).flatten(),
        allocations=np.pad(np.ones_like(trad.reshape((-1,1))), (0,1))[:-1],
        rates=np.pad(inflation.reshape((-1,1)), (0,1))[:-1],
    ).sum(axis=1).round(2)
    
    trad_rmd = ((1 - tax_rate) * trad * np.pad(rmd_take[1:], (0,1), mode='edge')).round(2)
    
    roth_withdrawal = np.clip(withdrawal - trad_rmd, 0.0, None).round(2)
    
    roth = np.clip((compute_period_returns(
        contributions=roth_contrib,
        allocations=allocations,
        rates=rates,
    ).sum(axis=1).round(2) - compute_period_returns(
        contributions=roth_withdrawal,
        allocations=allocations,
        rates=rates,
    ).sum(axis=1).round(2)), 0.0, None).round(2)
    
    roth_infl = compute_period_returns(
        contributions=np.diff(roth, prepend=0).flatten(),
        allocations=np.ones_like(roth.reshape((-1,1))),
        rates=inflation.reshape((-1,1)),
    ).sum(axis=1).round(2)
    
    return (trad, roth), (trad_infl, roth_infl), (trad_rmd, roth_withdrawal)


from collections import defaultdict

def run_simulations(
    ret: Retiree,
    ret_df: pd.DataFrame,
    allocation_strats: Dict[str, np.ndarray],
    rng: ParametricOptimizationInputs,
    start_age: Optional[int] = None,
    end_age: Optional[int] = None,
    n_sims: int = 10_000,
) -> Dict[str, np.ndarray]:
    result_dict = defaultdict(dict)
    rmd_t, rmd_r = calc_rmd(ret)
    if start_age is None:
        start_age = ret.age
    if end_age is None:
        end_age = ret.retirement_age

    start_time = time.time()
    
        
    for key, astrat in allocation_strats.items():   
        rng.reset()
        traditional_balance_list = []
        roth_balance_list = []
        traditional_balance_real_list = []
        roth_balance_real_list = []
        traditional_withdrawals_list = []
        roth_withdrawals_list = []
        for _ in range(n_sims):
            r = rng.generate_normal(end_age - start_age + 1)
            (
                (traditional_balance, roth_balance),
                (traditional_balance_real, roth_balance_real),
                (traditional_withdrawals, roth_withdrawals)
            ) = simulate(
                roth_contrib=ret_df['total_roth_dep'].values[start_age: end_age+1],
                trad_contrib=ret_df['total_trad_dep'].values[start_age: end_age+1],
                withdrawal=ret_df['with'].values[start_age: end_age+1],
                allocations=astrat[start_age: end_age+1],
                rates=r,
                rmd_take=rmd_t[start_age: end_age+1],
                rmd_remain=rmd_r[start_age: end_age+1],
                tax_rate=ret.effective_tax_rate,
                inflation=ret.inflation_arr[start_age: end_age+1],
            )
            
            traditional_balance_list.append(traditional_balance)
            roth_balance_list.append(roth_balance)
            traditional_balance_real_list.append(traditional_balance_real)
            roth_balance_real_list.append(roth_balance_real)
            traditional_withdrawals_list.append(traditional_withdrawals)
            roth_withdrawals_list.append(roth_withdrawals)
            
            

        result_dict[key]['traditional_balance'] =  np.column_stack(traditional_balance_list).round()
        result_dict[key]['roth_balance'] =  np.column_stack(roth_balance_list).round()
        result_dict[key]['traditional_balance_real'] =  np.column_stack(traditional_balance_real_list).round()
        result_dict[key]['roth_balance_real'] =  np.column_stack(roth_balance_real_list).round()
        result_dict[key]['traditional_withdrawals'] =  np.column_stack(traditional_withdrawals_list).round()
        result_dict[key]['roth_withdrawals'] =  np.column_stack(roth_withdrawals_list).round()
    
    total_time =  time.time() - start_time
    
    print(f'Done. {n_sims * len(allocation_strats):,} simulations of {end_age - start_age:,} years took {total_time:0.2f}s')
    return result_dict