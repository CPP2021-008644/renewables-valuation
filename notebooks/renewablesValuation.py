# -*- coding: utf-8 -*-

import numpy as np
import numpy_financial as npf


###############################################################################
###############################################################################

# SOME FUNCTIONS


# DISCOUNTED CASH FLOW
def DCF(cf, discount_rate, discount_start_time=0):
    """Discount a cash flow series.

    Parameters
    ----------
    cf : array-like
        Cash flow values.
    discount_rate : float
        Nominal discount rate as a fraction.
    discount_start_time : int, optional
        Period at which discounting starts, by default ``0``.

    Returns
    -------
    numpy.ndarray
        Discounted cash flows.
    """

    return np.array(
        [
            cf_t / (1 + discount_rate) ** (discount_start_time + t)
            for t, cf_t in enumerate(cf)
        ]
    )


# NET PRESENT VALUE
def NPV(cf, discount_rate, discount_start_time=0):
    """Compute the net present value of a cash flow series.

    Parameters
    ----------
    cf : array-like
        Cash flow values.
    discount_rate : float
        Nominal discount rate as a fraction.
    discount_start_time : int, optional
        Period at which discounting starts, by default ``0``.

    Returns
    -------
    float
        Net present value in the same units as ``cf``.
    """

    return np.sum(DCF(cf, discount_rate, discount_start_time))


# PAYBACK PERIOD
def paybackPeriod(cf):
    """Calculate the payback period of a cash flow series.

    Parameters
    ----------
    cf : array-like
        Cash flow values with the investment at index 0.

    Returns
    -------
    float
        Time required to recover the initial investment.
    """

    ac_cf = cf[0]
    year = 1
    while (ac_cf < 0) and (year < len(cf)):
        ac_cf += cf[year]
        year += 1

    if (ac_cf < 0) and (year == len(cf)):
        return year
    else:
        return year - 1 + (cf[year - 1] - ac_cf) / cf[year - 1]


# RETURN ON INVESTMENT
def returnOnInvestment(cf, dr):
    """Calculate the average return on investment of a cash flow series.

    Parameters
    ----------
    cf : array-like
        Cash flow values with the investment at index 0.
    dr : float
        Discount rate used in NPV calculation.

    Returns
    -------
    float
        Annualized return on investment.
    """

    npv = NPV(cf, dr)
    initial_investment = -cf[0]
    life = len(cf) - 1

    if npv >= 0:
        C = 0
    elif npv < -initial_investment:
        C = 1
    else:
        C = -npv / initial_investment

    if dr == 0:
        return C * initial_investment / life

    return C * initial_investment * (dr * (1 + dr) ** life) / ((1 + dr) ** life - 1)


# FUNCTION THAT RETURNS STARTUP FACTORS FOR THE AMOUNT OF YEARS SPECIFIED IN startup_duration
# CALCULATED AS A LINEAR MODEL:
# startup factor = first startup factor + (startup rate)*year


def getStartupFactors(first_startup_factor, startup_duration, startup_rate):
    """Generate startup correction factors.

    Parameters
    ----------
    first_startup_factor : float
        Production factor in the first year.
    startup_duration : int
        Number of years until full capacity is reached.
    startup_rate : float
        Increment applied each year until capacity is reached.

    Returns
    -------
    numpy.ndarray
        Array of startup factors per year.
    """

    startup_factors = np.ones(startup_duration)

    if startup_duration == 0:
        return startup_factors

    for y in range(startup_duration):
        aux = first_startup_factor + startup_rate * y
        if aux <= 1:
            startup_factors[y] = aux
        else:
            startup_factors[y] = 1
    return startup_factors


def accumulatedCF(cf):
    """Compute accumulated cash flow over time.

    Parameters
    ----------
    cf : array-like
        Cash flow values.

    Returns
    -------
    numpy.ndarray
        Accumulated cash flow for each period.
    """

    ac_cf = np.zeros(len(cf))

    ac_cf[0] = cf[0]
    for y in range(1, len(cf)):
        ac_cf[y] = ac_cf[y - 1] + cf[y]

    return ac_cf


###############################################################################
###############################################################################


###############################################################################
###############################################################################

#   PROJECT CLASS


class project:
    def __init__(self, name, start_time, life, startup_time, discount_rate):
        self.name = name
        self.start_time = start_time
        self.currency_ref_year = start_time
        self.life = life
        self.startup_time = startup_time
        self.end_time = start_time + life - 1
        self.discount_rate = discount_rate

    # SPECIFICATION OF REFERENCE YEAR CURRENCY

    def setCurrencyReferenceYear(self, ref_year):
        self.currency_ref_year = ref_year

    # MAIN PRODUCT

    def setMainProduct(
        self,
        utility_or_material,
        capacity,
        load_factor,
        target_price,
        first_startup_factor=1,
        startup_duration=0,
        startup_rate=0,
    ):
        self.main_product = mainProduct(
            utility_or_material,
            capacity,
            load_factor,
            target_price,
            first_startup_factor,
            startup_duration,
            startup_rate,
            self.end_time,
        )

    # COST SOURCES

    capex_dict = {}
    opex_dict = {}
    feedstock_dict = {}

    def addCost(
        self,
        name,
        kind,
        amount,
        first_time,
        last_time,
        period=-1,
        first_startup_factor=1,
        startup_duration=0,
        startup_rate=0,
    ):
        if kind == "capex":
            self.capex_dict[name] = cost(
                name,
                amount,
                first_time,
                last_time,
                period,
                first_startup_factor,
                startup_duration,
                startup_rate,
            )
        elif kind == "opex":
            self.opex_dict[name] = cost(
                name,
                amount,
                first_time,
                last_time,
                period,
                first_startup_factor,
                startup_duration,
                startup_rate,
            )

    def addFeedstock(self, name, utility_name, usage, isByproduct=False):
        self.feedstock_dict[name] = feedstock(name, utility_name, usage, isByproduct)

    def addFeedstockCosts(self, utilities_and_materials_dict):
        for fs_key, fs in self.feedstock_dict.items():
            by_sign = 1
            if fs.isByproduct:
                by_sign = -1

            year1_cost = (
                by_sign
                * fs.usage
                * utilities_and_materials_dict[fs.utility_name].price
                * self.main_product.yearly_output
            )
            self.opex_dict[fs.name] = cost(
                fs.name, year1_cost, self.startup_time, self.end_time, 1, 1, 0, 0
            )

    # GET LC OF MAIN PRODUCT

    def getLC(self, income_tax, inflation_time_series):
        LC = 0
        for capex_key, capex in self.capex_dict.items():
            LC += capex.getNPV(
                self.start_time,
                self.end_time,
                self.discount_rate,
                inflation_time_series,
                self.startup_time,
            )
            if capex.is_depreciable:
                LC -= income_tax * capex.getDepNPV(
                    self.start_time,
                    self.end_time,
                    self.discount_rate,
                    inflation_time_series,
                    self.end_time,
                    self.startup_time,
                )
        for opex_key, opex in self.opex_dict.items():
            LC += (1 - income_tax) * opex.getNPV(
                self.start_time,
                self.end_time,
                self.discount_rate,
                inflation_time_series,
                self.startup_time,
            )

        # return LC

        return LC / (
            (1 - income_tax)
            * self.main_product.getOutputNPV(
                self.start_time, self.end_time, self.discount_rate, self.startup_time
            )
        )

    def getCF(self, income_tax, inf_time_series):
        cf = np.zeros(self.life)

        for capex_key, capex in self.capex_dict.items():
            cf -= capex.getCF(
                self.start_time, self.end_time, inf_time_series, self.startup_time
            )
            if capex.is_depreciable:
                cf += income_tax * capex.getDepCF(
                    self.start_time,
                    self.end_time,
                    inf_time_series,
                    self.end_time,
                    self.startup_time,
                )

        for opex_key, opex in self.opex_dict.items():
            cf -= (1 - income_tax) * opex.getCF(
                self.start_time, self.end_time, inf_time_series, self.startup_time
            )

        # return cf

        cf += (1 - income_tax) * self.main_product.getCF(
            self.start_time, self.end_time, inf_time_series, self.startup_time
        )

        return cf

    def getNPV(self, income_tax, inf_time_series):
        nominal_dr = (1 + self.discount_rate) * (
            inf_time_series[1] / inf_time_series[0]
        ) - 1
        return NPV(self.getCF(income_tax, inf_time_series), nominal_dr)

    def getIRR(self, income_tax, inf_time_series):
        nominal_IRR = npf.irr(self.getCF(income_tax, inf_time_series))
        return (1 + nominal_IRR) / (inf_time_series[1] / inf_time_series[0]) - 1

    def getPayback(self, income_tax, inf_time_series):
        return paybackPeriod(self.getCF(income_tax, inf_time_series))

    def getReturnOnInvestment(self, income_tax, inf_time_series):
        nominal_dr = (1 + self.discount_rate) * (
            inf_time_series[1] / inf_time_series[0]
        ) - 1
        return returnOnInvestment(self.getCF(income_tax, inf_time_series), nominal_dr)


###############################################################################
###############################################################################


###############################################################################
###############################################################################

# GENERAL CLASS


class general:
    def __init__(self, inflation_rate=0.02):
        self.inflation_rate = inflation_rate

    # UTILITIES AND MATERIALS INFO
    utilities_and_materials_dict = {}

    def addUtilityOrMaterial(self, name, unit, price):
        self.utilities_and_materials_dict[name] = utilityOrMaterial(name, unit, price)


###############################################################################
###############################################################################


class utilityOrMaterial:
    def __init__(self, name, unit, price):
        self.name = name
        self.unit = unit
        self.price = price


class feedstock:
    def __init__(self, name, utility_name, usage, isByproduct=False):
        self.name = name
        self.utility_name = utility_name
        self.usage = usage
        self.isByproduct = isByproduct


###############################################################################
###############################################################################


# MAIN PRODUCT CLASS


class mainProduct:
    """
    Testing this

    """

    def __init__(
        self,
        utility_or_material,
        capacity,
        load_factor,
        target_price,
        first_startup_factor,
        startup_duration,
        startup_rate,
        production_end_time,
    ):
        self.product = utility_or_material
        self.capacity = capacity
        self.load_factor = load_factor
        self.yearly_output = capacity * load_factor * 365
        self.target_price = target_price
        self.first_startup_factor = first_startup_factor
        self.startup_duration = startup_duration
        self.startup_rate = startup_rate
        self.startup_factors = getStartupFactors(
            self.first_startup_factor, self.startup_duration, self.startup_rate
        )
        self.production_end_time = production_end_time

    # DECAY AND REPLACEMENTS

    def getReplacementYears(self, decay_rate, startup_time, min_tolerance=0):
        replacement_years = np.array([])

        dfactor = 1

        for y in range(startup_time, startup_time + self.startup_duration):
            print(y)
            print(dfactor)
            # Assume replacement happens at the beginning of the year

            dfactor = (
                dfactor
                - decay_rate * self.load_factor * self.startup_factors[y - startup_time]
            )
            if dfactor < min_tolerance:
                replacement_years = np.append(replacement_years, y)
                dfactor = 1

        for y in range(
            startup_time + self.startup_duration, self.production_end_time + 1
        ):
            print(y)
            print(dfactor)

            dfactor = dfactor - decay_rate * self.load_factor
            # Assume replacement happens at the beginning of the year
            if dfactor < min_tolerance:
                replacement_years = np.append(replacement_years, y)
                dfactor = 1

        return replacement_years

    def setDecay(self, decay_rate, replacement_years=[]):
        self.decay_rate = decay_rate
        self.replacement_years = np.array(replacement_years)

    def getDecayFactors(self, start, end, startup_time):
        decay_factors = np.zeros(end - start + 1)

        relative_startup_time = startup_time - start
        relative_replacement = self.replacement_years - start
        relative_end_time = self.production_end_time - start

        dfactor = 1

        for y in range(
            np.maximum(0, relative_startup_time),
            np.minimum(end - start + 1, relative_startup_time + self.startup_duration),
        ):
            decay_factors[y] = dfactor

            dfactor = (
                dfactor
                - self.decay_rate
                * self.load_factor
                * self.startup_factors[y - relative_startup_time]
            )

            # Assume replacement happens at the beginning of the year
            if y in relative_replacement:
                dfactor = 1

        for y in range(
            np.minimum(end - start + 1, relative_startup_time + self.startup_duration),
            np.minimum(end - start, relative_end_time) + 1,
        ):
            decay_factors[y] = dfactor

            dfactor = dfactor - self.decay_rate * self.load_factor

            # Assume replacement happens at the beginning of the year
            if y in relative_replacement:
                dfactor = 1

        return decay_factors

    # MAIN PRODUCT OUTPUT FLOWS, IN SPECIFIED MAIN PRODUCT UNIT
    # Returns main product flows starting and ending at specified dates

    def getOutputFlow(self, start, end, startup_time):
        output_flows = np.zeros(end - start + 1)

        relative_startup_time = startup_time - start
        relative_end_time = self.production_end_time - start

        for year in range(
            relative_startup_time, np.minimum(end - start, relative_end_time) + 1
        ):
            output_flows[year] = self.capacity * self.load_factor * 365

        lower_lim = np.maximum(relative_startup_time, 0)
        upper_lim = np.minimum(
            relative_startup_time + self.startup_duration - 1, end - start
        )

        for year in range(lower_lim, upper_lim + 1):
            output_flows[year] = (
                output_flows[year] * self.startup_factors[year - relative_startup_time]
            )

        return np.array(output_flows)

    # DISCOUNTED OUTPUT FLOWS, IN SPECIFIED MAIN PRODUCT UNIT
    # Returns discounted main product flows starting and ending at specified dates

    def getDiscountedOutputFlow(
        self, start, end, discount_rate, startup_time, discount_start_time=0
    ):
        return DCF(
            self.getOutputFlow(start, end, startup_time),
            discount_rate,
            discount_start_time,
        )

    # MAIN PRODUCT NET PRESENT VALUE OF OUTPUT, IN SPECIFIED MAIN PRODUCT UNIT
    # Returns NPV of discounted cash flow, obtained from getDCF()

    def getOutputNPV(
        self, start, end, discount_rate, startup_time, discount_start_time=0
    ):
        return NPV(
            self.getOutputFlow(start, end, startup_time),
            discount_rate,
            discount_start_time,
        )

    # REVENUE CASH FLOWS
    # Returns cash flows starting and ending at specified dates, taking into
    # account inflation, which is specified as an inflation factor time series
    # with the same length as the desired cash flows time series

    def getCF(self, start, end, inf_time_series, startup_time):
        return np.multiply(
            self.getOutputFlow(start, end, startup_time),
            inf_time_series * self.target_price,
        )

    # REVENUE DISCOUNTED CASH FLOWS
    # Returns discounted cash flows starting and ending at specified dates, taking into
    # account inflation, which is specified as an inflation factor time series
    # with the same length as the desired cash flows time series , and a specified nominal
    # discount rate

    def getDCF(
        self,
        start,
        end,
        discount_rate,
        inf_time_series,
        startup_time,
        discount_start_time=0,
    ):
        nominal_dr = (1 + discount_rate) * (inf_time_series[1] / inf_time_series[0]) - 1
        return np.multiply(
            self.getDiscountedOutputFlow(
                start, end, nominal_dr, startup_time, discount_start_time
            ),
            inf_time_series * self.target_price,
        )

    # REVENUE NET PRESENT VALUE, IN REFERENCE YEAR CURRENCY
    # Returns NPV of discounted cash flow

    def getNPV(
        self,
        start,
        end,
        discount_rate,
        inf_time_series,
        startup_time,
        discount_start_time=0,
    ):
        nominal_dr = (1 + discount_rate) * (inf_time_series[1] / inf_time_series[0]) - 1
        return NPV(
            self.getCF(start, end, inf_time_series, startup_time),
            nominal_dr,
            discount_start_time,
        )


###############################################################################
###############################################################################


###############################################################################
###############################################################################

# COST CLASS


class cost:
    def __init__(
        self,
        name,
        amount,
        first_time,
        last_time,
        period,
        first_startup_factor,
        startup_duration,
        startup_rate,
    ):
        self.name = name
        self.amount = amount
        self.first_time = first_time
        self.last_time = last_time
        self.period = period
        self.is_periodic = True if period > 0 else False
        self.first_startup_factor = first_startup_factor
        self.startup_duration = startup_duration
        self.startup_rate = startup_rate
        self.startup_factors = getStartupFactors(
            first_startup_factor, startup_duration, startup_rate
        )

    # COST CASH FLOWS
    # Returns cash flows starting and ending at specified dates, taking into
    # account inflation, which is specified as an inflation factor time series
    # with the same length as the desired cash flows time series

    def getCF(self, start, end, inf_time_series, startup_time):
        cash_flows = np.zeros(end - start + 1)

        relative_first_time = self.first_time - start
        relative_last_time = self.last_time - start

        relative_startup_time = startup_time - start

        if self.is_periodic == True:
            per = self.period
        else:
            per = relative_last_time + 1 - relative_first_time

        payment_years = np.arange(relative_first_time, relative_last_time + 1, per)

        if len(payment_years) > 0:
            while payment_years[0] < 0:
                payment_years = np.delete(payment_years, 0)
                if len(payment_years) == 0:
                    break

        if len(payment_years) > 0:
            while payment_years[-1] > end - start:
                payment_years = np.delete(payment_years, -1)
                if len(payment_years) == 0:
                    break

        for year in payment_years:
            cash_flows[year] = self.amount * inf_time_series[year]

        # STARTUP CORRECTION #

        lower_lim = np.maximum(relative_startup_time, 0)
        upper_lim = np.minimum(
            relative_startup_time + self.startup_duration - 1, end - start
        )

        for year in range(lower_lim, upper_lim + 1):
            cash_flows[year] = (
                cash_flows[year] * self.startup_factors[year - relative_startup_time]
            )

        return cash_flows

    # COST DISCOUNTED CASH FLOWS
    # Returns discounted cash flows starting and ending at specified dates, taking into
    # account inflation, which is specified as an inflation factor time series
    # with the same length as the desired cash flows time series , and a specified nominal
    # discount rate

    def getDCF(
        self,
        start,
        end,
        discount_rate,
        inf_time_series,
        startup_time,
        discount_start_time=0,
    ):
        nominal_dr = (1 + discount_rate) * (inf_time_series[1] / inf_time_series[0]) - 1
        return DCF(self.getCF(start, end, inf_time_series, startup_time), nominal_dr)

    # COST NET PRESENT VALUE, IN REFERENCE YEAR CURRENCY
    # Returns NPV of discounted cash flow

    def getNPV(
        self,
        start,
        end,
        discount_rate,
        inf_time_series,
        startup_time,
        discount_start_time=0,
    ):
        nominal_dr = (1 + discount_rate) * (inf_time_series[1] / inf_time_series[0]) - 1
        return NPV(self.getCF(start, end, inf_time_series, startup_time), nominal_dr)

    # DEPRECIATION

    is_depreciable = False

    def setDepreciation(self, dep_time, salvage_value=0):
        self.dep_time = dep_time
        self.salvage_value = salvage_value
        self.is_depreciable = True

    # DEPRECIATION CASH FLOWS, DISCOUNTED CFS and NPV
    # Analogous to other cash flow, discounted cash flows and NPV functions

    def getDepCF(self, start, end, inf_time_series, project_end_year, startup_time):
        dep_cash_flows = np.zeros(end - start + 1)

        if self.is_depreciable == False:
            return dep_cash_flows

        cash_flows = self.getCF(start, end, inf_time_series, startup_time)

        for payment_year, payment in enumerate(cash_flows):
            charge = (payment - self.salvage_value) / (self.dep_time)

            for charge_year in range(
                payment_year + 1,
                np.minimum(end - start + 1, payment_year + self.dep_time),
            ):
                dep_cash_flows[charge_year] += charge

            if (project_end_year == end) and (
                project_end_year < payment_year + start + self.dep_time
            ):
                dep_cash_flows[project_end_year - start] += (
                    payment_year + self.dep_time + start - project_end_year
                ) * charge

        return dep_cash_flows

    def getDepDCF(
        self,
        start,
        end,
        discount_rate,
        inflation_time_series,
        project_end_year,
        startup_time,
        discount_start_time=0,
    ):
        nominal_dr = (1 + discount_rate) * (
            inflation_time_series[1] / inflation_time_series[0]
        ) - 1
        return DCF(
            self.getDepCF(
                start, end, inflation_time_series, project_end_year, startup_time
            ),
            nominal_dr,
            discount_start_time,
        )

    def getDepNPV(
        self,
        start,
        end,
        discount_rate,
        inflation_time_series,
        project_end_year,
        startup_time,
        discount_start_time=0,
    ):
        nominal_dr = (1 + discount_rate) * (
            inflation_time_series[1] / inflation_time_series[0]
        ) - 1

        return NPV(
            self.getDepCF(
                start, end, inflation_time_series, project_end_year, startup_time
            ),
            nominal_dr,
            discount_start_time,
        )


###############################################################################
###############################################################################


def printCF(obj, project, inf_time_series, dep=False):
    """Print cash flows for a project object.

    Parameters
    ----------
    obj : cost or mainProduct
        Object exposing ``getCF`` or ``getDepCF`` methods.
    project : project
        Project containing timing information.
    inf_time_series : array-like
        Inflation factors used to compute nominal values.
    dep : bool, optional
        If ``True`` prints depreciation cash flows, otherwise normal cash flows.

    Returns
    -------
    None
    """

    import pandas as pd

    if dep:
        cf = obj.getDepCF(
            project.start_time,
            project.end_time,
            inf_time_series,
            project.end_time,
            project.startup_time,
        )
    else:
        cf = obj.getCF(
            project.start_time, project.end_time, inf_time_series, project.startup_time
        )
    print(" \n CASH FLOWS: \n")
    print(pd.DataFrame(cf, np.arange(len(cf)) + project.start_time))
    print("\n")


def plotCF(start_time, cf):
    """Plot a cash flow time series.

    Parameters
    ----------
    start_time : int
        Year corresponding to the first cash flow.
    cf : array-like
        Cash flow values to plot.

    Returns
    -------
    matplotlib.figure.Figure
        Figure object containing the plot.
    """

    import matplotlib.pyplot as plt

    time = np.arange(start_time, start_time + len(cf))

    fig, ax = plt.subplots()
    ax.plot(time, cf)
