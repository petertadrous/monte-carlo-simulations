TAX_LOOKUP = {
    2022 : {
        'FED': dict(
            DEDUCTION = 12_950,
            TAXES = dict(
                INCOME = dict(BRACKETS = [0,10_275,41_775,89_075,170_050,215_950,539_900],
                              RATES = [0.10,0.12,0.22,0.24,0.32,0.35,0.37]),
                OASDI = dict(BRACKETS = [0,147_000],
                             RATES = [0.062,0.0]),
                MEDICARE = dict(BRACKETS = [0,200_000],
                                RATES = [0.0145, 0.0235])
            )
        ),
        'NY': dict(
            DEDUCTION = 8_000,
            TAXES = dict(
                INCOME = dict(
                    BRACKETS = [0,8_500,11_700,13_900,80_650,215_400,1_077_550,5_000_000,25_000_000],
                    RATES = [0.04,0.045,0.0525,0.0585,0.0625,0.0685,0.0965,0.1030,0.1090],
                ),
                NYPFL = dict(
                    BRACKETS = [0,82_917.8082192],
                    RATES = [0.00511, 0.0]
                )
            ),
            LOCALITIES = dict(
                NYC = dict(
                    TAXES = dict(
                        INCOME = dict(
                            BRACKETS = [0,12_000,25_000,50_000],
                            RATES = [0.03078,0.03762,0.03819,0.03876]
                        )
                    )
                )
            )
        )
    },
    2023 : {
        'FED': dict(
            DEDUCTION = 0,
            TAXES = dict(
                INCOME = dict(
                    BRACKETS = [],
                    RATES = []
                ),
                OASDI = dict(
                    BRACKETS = [0,160_200],
                    RATES = [0.062,0.0]
                ),
                MEDICARE = dict(
                    BRACKETS = [],
                    RATES = []
                )
            )
        )
    }
}