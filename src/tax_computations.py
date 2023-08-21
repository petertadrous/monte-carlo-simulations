from copy import deepcopy
from datetime import datetime as dt
from typing import Dict, Optional, Union


import numpy as np


from cache.tax_data import TAX_LOOKUP


class IncomeTaxes:
    def __init__(
            self,
            taxable_income: float,
            state: str,
            city: str,
            tax_year: Optional[int] = None,
            itemized_federal: float = 0.0,
            itemized_state: float = 0.0,
            withheld_tax: float = 0.0,
    ) -> None:
        self.taxable_income = taxable_income
        self.update_tax_year(tax_year=tax_year, state=state, city=city)
        self.federal_deduction = max(
            itemized_federal, TAX_LOOKUP[self.tax_year]['FED']['DEDUCTION'])
        self.state_deduction = max(
            itemized_state, TAX_LOOKUP[self.tax_year][self.state]['DEDUCTION'])
        self.withheld_tax = withheld_tax
        self.update_calculations()

    def update_tax_year(
            self,
            tax_year: Optional[int] = None,
            state: Optional[str] = None,
            city: Optional[str] = None
    ) -> None:
        self.tax_year = tax_year or (dt.today().year - 1)
        self._fed_lookup = deepcopy(TAX_LOOKUP[self.tax_year]['FED']['TAXES'])
        self.update_state(state)
        self.update_city(city)

    def update_state(
            self,
            state: str
    ) -> None:
        if str.upper(state) not in TAX_LOOKUP[self.tax_year]:
            raise NotImplementedError(
                f'No available tax data for {str.upper(state)} in {self.tax_year}')
        self.state = str.upper(state)
        self._state_lookup = deepcopy(TAX_LOOKUP[self.tax_year][self.state]['TAXES'])

    def update_city(
            self,
            city: Optional[str] = None
    ) -> None:
        if any([
                'LOCALITIES' not in TAX_LOOKUP[self.tax_year][self.state],
                str.upper(city) not in TAX_LOOKUP[self.tax_year][self.state]['LOCALITIES']
        ]) and city is not None:
            raise NotImplementedError(
                f'No available tax data for {str.upper(city)} '
                f'in {self.state} in {self.tax_year}')
        self.city = str.upper(city) if city is not None else city
        self._city_lookup = deepcopy(
            TAX_LOOKUP[self.tax_year][self.state]['LOCALITIES']
            .get(self.city, dict())).get('TAXES', dict())

    @staticmethod
    def _tax_calc(
            incomes: Union[np.ndarray, float],
            bands: np.ndarray,
            rates: np.ndarray,
            round_brackets: bool = False
    ):
        if isinstance(incomes, float):
            incomes = np.array([incomes])
            is_float = True
        else: is_float = False
        # Broadcast incomes so that we can compute an amount per income, per band
        incomes_ = np.broadcast_to(incomes, (bands.shape[0] - 1, incomes.shape[0]))
#         print('incomes', incomes.shape,incomes)
#         print('incomes_',incomes_.shape,incomes_)
#         print('bands',bands.shape,bands)
#         print('rates',rates.shape,rates)
#         print('incomes_.transpose()',incomes_.transpose().shape, incomes_.transpose())
#         print('bands[:-1]',bands[:-1].shape, bands[:-1])
#         print('bands[1:]',bands[1:].shape, bands[1:])
#         print('np.clip(incomes_.transpose(), bands[:-1], bands[1:])',np.clip(incomes_.transpose(),
#                                 bands[:-1], bands[1:]).shape, np.clip(incomes_.transpose(),
#                                 bands[:-1], bands[1:]))
        # Find amounts in bands for each income
        amounts_in_bands = np.clip(incomes_.transpose(),
                                bands[:-1], bands[1:]) - bands[:-1]
#         print('amounts_in_bands', amounts_in_bands)
        # Calculate tax per band
        taxes = rates * amounts_in_bands
        if round_brackets:
            unrounded_idxs_ = taxes.shape[1] - 1 - (taxes[:,::-1]!=0).argmax(1)
            unrounded_ = taxes[np.arange(taxes.shape[0]), unrounded_idxs_]
            taxes = np.round(taxes)
            taxes[np.arange(taxes.shape[0]), unrounded_idxs_] = unrounded_
        # Sum tax bands per income
        taxes = taxes.sum(axis=1)
        return taxes[0] if is_float else taxes

    def update_calculations(
            self
    ) -> float:
        # Calculate taxable income at federal and state level
        self.federal_taxable_income = self.taxable_income - self.federal_deduction
        self.state_taxable_income = self.taxable_income - self.state_deduction
        # Calculate estimated taxes
        self.federal_taxes = dict()
        self.state_taxes = dict()
        self.city_taxes = dict()
        self.estimated_taxes = dict()
        for key, est_tax, tax_income, tax_lookup, round_brackets in zip(
            ['FED', self.state, self.city],
            [self.federal_taxes, self.state_taxes, self.city_taxes],
            [self.federal_taxable_income, self.state_taxable_income, self.state_taxable_income],
            [self._fed_lookup, self._state_lookup, self._city_lookup],
            [False, True, True]
        ):
            est_tax.update({
                f'{key}_{k}' : round(self._tax_calc(
                    incomes=tax_income,
                    bands=np.array(v['BRACKETS'] + [np.inf]),
                    rates=np.array(v['RATES']),
                    round_brackets=round_brackets), 2)
                for k,v in tax_lookup.items()
            })
            self.estimated_taxes.update(est_tax)
        self.total_estimated_taxes = round(sum(self.estimated_taxes.values()), 2)
        return self.total_estimated_taxes
    
    def get_estimated_taxes(
            self,
            total: bool = True
    ) -> Union[float, Dict[str, float]]:
        if total: return self.total_estimated_taxes
        return self.estimated_taxes

    def get_estimated_refund(
            self
    ) -> float:
        self.estimated_refund = round(self.withheld_tax-self.total_estimated_taxes, 2)
        return self.estimated_refund
    
    def get_after_tax_income(
            self
    ) -> float:
        self.after_tax_income = round(self.taxable_income - self.total_estimated_taxes, 2)
        return self.after_tax_income