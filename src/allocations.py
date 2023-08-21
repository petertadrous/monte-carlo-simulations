from typing import Optional


import numpy as np


def compute_cash_array(
        step_size,
        interval_diffs,
        delta,
        sigfig = 3
):
    to_concat = []
    for i in range(0, len(interval_diffs)):
        step_ranges = np.floor_divide(interval_diffs[i], step_size)
        additional_range = np.mod(interval_diffs[i], step_size)

        repeat_array = np.repeat(np.array([step_size]), step_ranges)
        if additional_range:
            repeat_array = np.concatenate([repeat_array, [additional_range]])
        cash_array = np.repeat(np.linspace(
                max(delta*(i-1), 0),
                delta*i,
                repeat_array.size + 1
            ).round(sigfig)[1:], repeat_array)
        to_concat.append(cash_array)
    return np.concatenate(to_concat)


def custom_allocation(
        max_age: int = 120,
        inflection_points: Optional[np.array] = None,
        stock_pcts: Optional[np.array] = None
):
    if inflection_points is None:
        inflection_points = np.array([35,45,55,65,70,75,80,85,90,95])
        stock_pcts = np.array([1.,.85,.75,.65,.55,.4,.3,.2,.1,.0])
    inflection_points = np.diff(inflection_points, prepend=0)
    stocks = np.repeat(stock_pcts, inflection_points)[:max_age+1]
    # stocks = np.array([1.0] * 35 + [0.8] * 10 + [0.7] * 10 + [0.60] * 10 + [0.45] * 10 + [0.4] * 10)
    stocks = np.pad(stocks, (0, max_age+1 - stocks.size), mode='edge')
    bonds = 1 - stocks
    bills = np.zeros_like(bonds)
    return np.column_stack((stocks, bonds, bills))


def simple_allocation(
    max_age: int = 120,
    stock_rule: int = 110,
    step: int = 1,
    cash_delta: float = 0.05,
    cash_intervals: Optional[list] = None,
    max_cash: float = 0.5,
):
    stocks = np.flip(np.repeat(np.clip(np.arange(0, stock_rule + 1,step), 0, 100), step)/ 100)[:max_age+1]
    stocks = np.pad(stocks, (0, max_age + 1 - stocks.size), mode='edge')
    remaining = np.ones_like(stocks) -  stocks

    if cash_delta == 0.0:
        cash = np.zeros_like(stocks)
    else:
        if cash_intervals is None:
            cash_intervals = np.array([25, 50,70,80,90,100, 110, 120, 130, 140])
        
        cash_intervals = np.append(cash_intervals, [max_age + 1])
        cash_intervals = np.diff(np.clip(cash_intervals, 0, max_age + 1), prepend=[0])
        
    #     cash = np.repeat(np.arange(cash_intervals.size) * cash_delta, cash_intervals)
    #     cash = np.clip(np.clip(cash, 0.0, remaining), 0.0, max_cash)
        cash = compute_cash_array(step,
            cash_intervals,
            cash_delta)
        cash = np.clip(np.clip(cash, 0.0, remaining), 0.0, max_cash)
    
    bonds = remaining - cash    
    
    return np.column_stack((stocks, bonds, cash))
#     return np.column_stack((np.arange(0, max_age+1), stocks, bonds, cash))


def get_vanguard_glide_path(default: bool = True, stop_year: Optional[int] = None, max_age: Optional[int] = 120):
    vanguard_default = np.concatenate((
        np.repeat(0.9, 40),
        np.linspace(0.9, 0.6, 20, endpoint=False),
    ))
    if default:
        vanguard_default = np.concatenate((
            vanguard_default,
            np.linspace(0.6, 0.5, 5, endpoint=False),
            np.linspace(0.5, 0.3, 8, endpoint=True),
        )).round(3)
    else:
        vanguard_default = np.concatenate((
            vanguard_default,
            np.linspace(0.6, 0.5, 6, endpoint=True),
        )).round(3)
    if stop_year is not None:
        vanguard_default = vanguard_default[:stop_year+1]
    vanguard_default = np.pad(vanguard_default, (0, max_age - vanguard_default.shape[0] + 1), mode='edge')
    vanguard_default = np.column_stack((vanguard_default, 1-vanguard_default, np.zeros_like(vanguard_default)))
    return vanguard_default
