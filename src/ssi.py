import numpy as np


from src.interfaces import RetireeClass as Retiree


ssi_index_factors = np.flip(np.array([
    14.1154565, 13.7775824, 13.2366334, 13.0025136,
    12.2662321, 11.6190212, 10.8718017, 10.2778311,
    9.7919043, 9.3234299, 8.4912767, 7.9912654,
    7.5428814, 7.0183793, 6.5653499, 6.1941246,
    5.7384329, 5.2768223, 4.840793, 4.3980709,
    4.1685811, 3.9749404, 3.754249, 3.6008342,
    3.4970384, 3.287387, 3.1330788, 3.0137525,
    2.880689, 2.7771952, 2.6411145, 2.618594,
    2.5501502, 2.4518701, 2.3375513, 2.2086732,
    2.0988236, 1.9880337, 1.8838566, 1.8399616,
    1.8216921, 1.7782228, 1.6992296, 1.639249,
    1.567215, 1.4991796, 1.4654679, 1.4879065,
    1.4535518, 1.4093909, 1.3667145, 1.3494665,
    1.3032076, 1.2593928, 1.2453206, 1.2037519,
    1.1616481, 1.1196873, 1.0889195, 1.0, 1.0,]))


ssi_base_max_growth = 1.0362923
ssi_base_max_since_1990 = np.array([
     51_300.0,  53_400.0,  55_500.0,  57_600.0,  60_600.0,
     61_200.0,  62_700.0,  65_400.0,  68_400.0,  72_600.0,
     76_200.0,  80_400.0,  84_900.0,  87_000.0,  87_900.0,
     90_000.0,  94_200.0,  97_500.0, 102_000.0, 106_800.0,
    106_800.0, 106_800.0, 110_100.0, 113_700.0, 117_000.0,
    118_500.0, 118_500.0, 127_200.0, 128_400.0, 132_900.0,
    137_700.0, 142_800.0, 147_000.0, 160_200.0,
])


def calc_ssi(ret: Retiree):
    ssi_base_max = np.concatenate((
        ssi_base_max_since_1990[ret.years_arr[0] - 1990:],
        np.repeat([ssi_base_max_growth], ret.years_arr[-1] - 2023).cumprod() * ssi_base_max_since_1990[-1]
    ))
    clipped_earnings = np.clip(ret.income_arr, 0.0, ssi_base_max)
    
    i = np.flip(clipped_earnings[max(0, ssi_index_factors.size - (62+1)):62+1])
    awi = i[:ssi_index_factors.size] * ssi_index_factors
    top_awi = awi[np.argpartition(awi, -35)[-35:]]
    aime = np.sum(top_awi) // 420
    pia = (
        (0.90 *  np.clip(aime, 0.0, 1_115.) ) 
        + (0.32 *  (np.clip(aime, 1_115., 6_721.) - 1_115.) ) 
        + (0.15 *  (np.clip(aime, 6_721., None) - 6_721.) )
    ) // 0.1 / 10.0
    return (pia * 12.0).round(2)


def calc_ssi_income_array(ret: Retiree):
    return np.repeat([0., calc_ssi(ret)], [68, ret.life_expectancy-67])[:ret.life_expectancy +1]
