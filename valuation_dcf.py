import pandas as pd
import numpy as np

# ----------------------------------------------------------------------------------------------------------------------
# Aux functions
# ----------------------------------------------------------------------------------------------------------------------


def convert_rate(previous_rate, previous_periodicity=1, new_periodicity=1):
    """
    Given a rate and a periodicity, computes the equivalent rate for a new periodicity
    Parameters
    ----------
    previous_rate
    previous_periodicity = 1
    new_periodicity = 1

    Returns
    -------
    new_rate
    """
    # (1+previous_rate)**previous_periodicity = (1+new_rate)**new_periodicity
    new_rate = (1+previous_rate)**(previous_periodicity/new_periodicity) - 1
    return new_rate


def freq_str_to_months(freq_str:str) -> int:
    """
    Given a string indicating the frequency, returns an int with the equivalent number of months

    Parameters
    ----------
    freq_str: str

    Returns
    -------
    integer indicating the number of months
    """
    if freq_str == "Y":
        freq = 12
    elif freq_str == "2Q":
        freq = 6
    elif freq_str == "Q":
        freq = 3
    elif freq_str == "M":
        freq = 1
    else:
        raise ValueError("Only Y, 2Q, Q, and M allowed as frequency strings.")
    return freq


def freq_months_to_freq_str(no_months: str)->int:
    """
    Given a int indicating the number of months, returns a str with the equivalent frequency

    Parameters
    ----------
    no_months: int

    Returns
    -------
    str indicating the frequency
    """
    if no_months == 12:
        freq_str = "Y"
    elif no_months == 6:
        freq_str = "2Q"
    elif no_months == 3:
        freq_str = "Q"
    elif no_months == 1:
        freq_str = "M"
    else:
        raise ValueError("Only 1, 3, 6 and 12 allowed as frequency months.")
    return freq_str

# ----------------------------------------------------------------------------------------------------------------------
# Cash flow classes
# ----------------------------------------------------------------------------------------------------------------------


class LineBuilder:
    def __init__(self, name, effective_date=None, tenor=None):
        self.name = name
        self.effective_date = pd.to_datetime(effective_date)
        self.tenor = tenor

        if name is None:
            self.ignore_last_line = True
        else:
            self.ignore_last_line = False

    def __neg__(self):
        z = type(self)(name=f"({self.name})")
        z.ignore_last_line = self.ignore_last_line

        def cf_fun(start_date=None, end_date=None, nper=None, freq=None, initial_period=False):
            cf = - self._get_line(start_date=start_date, end_date=end_date, nper=nper, freq=freq, initial_period=initial_period)
            cf = cf.rename({cf.index[0]: z.name})
            return cf
        setattr(z, "_get_line", cf_fun)

        def table_fun(start_date=None, end_date=None, nper=None, freq=None, initial_period=False, breakdown_level=1):
            cf = z._get_line(start_date=start_date, end_date=end_date, nper=nper, freq=freq, initial_period=initial_period)
            if breakdown_level == 0:
                table = pd.DataFrame(columns=cf.columns)
            else:
                table = self.get_table(start_date=start_date, end_date=end_date, nper=nper, freq=freq, initial_period=initial_period, breakdown_level=breakdown_level)
                table = table.iloc[:-1]
            table = pd.concat((table, cf), axis=0)
            return table
        setattr(z, "get_table", table_fun)
        return z

    def __add__(self, other):
        z = type(self)(f"{self.name}+{other.name}")
        z.ignore_last_line = True

        def line_fun(start_date=None, end_date=None, nper=None, freq=None, initial_period=False):
            cf1 = self._get_line(start_date=start_date, end_date=end_date, nper=nper, freq=freq, initial_period=initial_period)
            cf2 = other._get_line(start_date=start_date, end_date=end_date, nper=nper, freq=freq, initial_period=initial_period)
            cf = cf1 + cf2.values
            cf = cf.rename(index={cf.index[0]: z.name})
            return cf
        setattr(z, "_get_line", line_fun)

        def table_fun(start_date=None, end_date=None, nper=None, freq=None, initial_period=False, breakdown_level=1):
            cf = z._get_line(start_date=start_date, end_date=end_date, nper=nper, freq=freq, initial_period=initial_period)
            if breakdown_level == 0:
                table1 = pd.DataFrame(columns=cf.columns)
                table2 = pd.DataFrame(columns=cf.columns)
            else:
                if self.ignore_last_line:
                    table1 = self.get_table(start_date=start_date, end_date=end_date, nper=nper, freq=freq,
                                            initial_period=initial_period, breakdown_level=breakdown_level)
                    table1 = table1.iloc[:-1]
                else:
                    table1 = self.get_table(start_date=start_date, end_date=end_date, nper=nper, freq=freq,
                                            initial_period=initial_period, breakdown_level=breakdown_level - 1)

                if other.ignore_last_line:
                    table2 = other.get_table(start_date=start_date, end_date=end_date, nper=nper, freq=freq,
                                             initial_period=initial_period, breakdown_level=breakdown_level)
                    table2 = table2.iloc[:-1]
                else:
                    table2 = other.get_table(start_date=start_date, end_date=end_date, nper=nper, freq=freq,
                                             initial_period=initial_period, breakdown_level=breakdown_level - 1)

            table = pd.concat((table1, table2), axis=0)
            table = pd.concat((table, cf), axis=0)
            return table

        setattr(z, "get_table", table_fun)
        return z

    def __sub__(self, other):
        z = self + (-other)
        z.name = f"{self.name} -{other.name}"
        return z

    def _get_line_bak(self, start_date=None, end_date=None, nper=None, freq=None, initial_period=False):
        # freq nomenclature: https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#timeseries-offset-aliases
        start_date = pd.to_datetime(start_date)
        if freq == "2Q" and (start_date + pd.offsets.QuarterEnd()).month in [3, 9]:
            start_date -= pd.DateOffset(months=3)
        elif freq in ["Y", "Q", "M"]:
            start_date -= pd.DateOffset(freq_str_to_months(freq))
        cols = pd.date_range(start=start_date, end=end_date, periods=nper+1, freq=freq)
        if not initial_period:
            cols = cols[1:]

        freq_str = freq
        freq = freq_str_to_months(freq)
        n = cols.size
        values = np.full(n, 1).astype("float64")
        if self.tenor is not None:
            if self.effective_date is not None:
                initial_zeros = np.sum(cols < self.effective_date)  # number of dates before the effective one
                if initial_zeros < n:  # there are dates in the range before the effective one
                    # or the effective date is out of the range (in the past)
                    temp_date = cols[cols >= self.effective_date][0] # first date of the range bigger than
                    # or equal to the effective one
                    initial_coverage = (temp_date.month - self.effective_date.month+1)/freq
                    # initial residual: difference bet. temp_date (in the set) and effective date + 1/freq
                else:  # the effective date is out of the range (in the future)
                    initial_coverage = 0
            else:
                initial_zeros = 0
                initial_coverage = 1

            if initial_coverage != 0:
                left_over_periods = self.tenor*12/freq - initial_coverage
                left_over_periods = int(left_over_periods) + int(left_over_periods % 1 != 0)  # ceiling
                if left_over_periods <= n - initial_zeros - 1:  # the left over periods fit in the array
                    final_coverage = (self.tenor*12-initial_coverage*freq) % freq
                    final_coverage = final_coverage/freq + int(final_coverage == 0)
                else:
                    left_over_periods = n - initial_zeros - 1
                    final_coverage = 1
                multiplier = np.ones(1+left_over_periods)
                multiplier[0] = initial_coverage
                multiplier[-1] = final_coverage
                multiplier = np.concatenate((np.zeros(initial_zeros), multiplier))
                multiplier = np.concatenate((multiplier, np.zeros(n-1-left_over_periods-initial_zeros)))
                # multiplier = initial zeros + left_over_periods + remaining periods
            else:
                multiplier = np.zeros(n)
            values *= multiplier
        return pd.DataFrame(values.reshape((1,n)), index=[self.name],columns=cols)


    def _get_line(self, start_date=None, end_date=None, nper=None, freq=None, initial_period=False):
        # freq nomenclature: https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#timeseries-offset-aliases
        start_date = pd.to_datetime(start_date)
        start_date2 = start_date # +pd.Timedelta(days=365)
        if freq == "2Q" and (start_date + pd.offsets.QuarterEnd()).month in [3, 9]:
            start_date -= pd.DateOffset(months=3)
        elif freq in ["Y", "Q", "M"]:
            start_date -= pd.DateOffset(freq_str_to_months(freq))
        cols = pd.date_range(start=start_date, end=end_date, periods=nper+1, freq=freq)
        if not initial_period:
            cols = cols[1:]

        freq_str = freq
        freq = freq_str_to_months(freq)
        n = cols.size
        values = np.full(n, 1).astype("float64")

        if self.tenor is not None:
            if self.effective_date is not None:
                initial_zeros = np.sum(cols < self.effective_date)  # number of dates before the effective one
            else:
                initial_zeros = 0
                self.effective_date = start_date2
            if initial_zeros == 0:  # the effective date is out of the range (in the past) or it's the 1st element
                expired_dates = pd.date_range(start=self.effective_date, end=start_date2, freq=freq_str)
                if len(expired_dates) == 0:
                    temp_date = start_date2
                    initial_coverage = 1
                else:
                    temp_date = expired_dates[expired_dates >= self.effective_date][0]
                    initial_coverage = (temp_date.month - self.effective_date.month + 1) / freq

                left_over_periods = max(self.tenor*12/freq - expired_dates.size - initial_coverage, 0)
                left_over_periods = int(left_over_periods) + int(left_over_periods % 1 != 0)  # ceiling
                if left_over_periods <= n - 1:
                    final_coverage = (self.tenor * 12 - initial_coverage * freq) % freq
                    # final residual: difference bet. tenor and initial_coverage + 1/freq
                    final_coverage = final_coverage / freq + int(final_coverage == 0)
                else:
                    left_over_periods = n - 1
                    final_coverage = 1
                multiplier = np.ones(1 + left_over_periods)
                multiplier[-1] = final_coverage
                multiplier = np.concatenate((multiplier, np.zeros(n - 1 - left_over_periods)))
                # multiplier = left_over_periods + remaining periods
            elif 0 < initial_zeros & initial_zeros < n:  # there are dates in the range before the effective one
                temp_date = cols[cols >= self.effective_date][0] # first date of the range bigger than
                # or equal to the effective one
                initial_coverage = (temp_date.month - self.effective_date.month+1)/freq
                # initial residual: difference bet. temp_date (in the set) and effective date + 1/freq

                left_over_periods = self.tenor*12/freq - initial_coverage
                left_over_periods = int(left_over_periods) + int(left_over_periods % 1 != 0)  # ceiling
                if left_over_periods <= n - initial_zeros - 1:
                    final_coverage = (self.tenor*12-initial_coverage*freq) % freq
                    final_coverage = final_coverage/freq + int(final_coverage == 0)
                else:
                    left_over_periods = n - initial_zeros - 1
                    final_coverage = 1
                multiplier = np.ones(1+left_over_periods)
                multiplier[0] = initial_coverage
                multiplier[-1] = final_coverage
                multiplier = np.concatenate((np.zeros(initial_zeros), multiplier))
                multiplier = np.concatenate((multiplier, np.zeros(n-1-left_over_periods-initial_zeros)))
            else:  # the effective date is out of the range (in the future)
                initial_coverage = 0
                multiplier = np.zeros(n)
            values *= multiplier
        return pd.DataFrame(values.reshape((1,n)), index=[self.name],columns=cols)


class Immutable(LineBuilder):
    def __init__(self, name, value=np.nan, effective_date=None, tenor=None):
        LineBuilder.__init__(self, name=name, effective_date=effective_date, tenor=tenor)
        self.value = value

    def __add__(self, other):
        if type(self) != type(other):
            return NotImplemented
        else:
            return LineBuilder.__add__(self, other)

    def __mul__(self, other):
        try:
            float(other)
            return self*Quantity(name="Quantity", value=other, effective_date=self.effective_date, tenor=self.tenor)
        except TypeError:
            return NotImplemented

    def __rmul__(self, other):
        return self.__mul__(other)

    def _get_line(self, start_date=None, end_date=None, nper=None, freq=None, initial_period=False):
        line = LineBuilder._get_line(self, start_date=start_date, end_date=end_date, nper=nper, freq=freq, initial_period=initial_period)
        line = self.value * (line != 0)
        return line

    def get_value(self, start_date=None, end_date=None, nper=None, freq=None, initial_period=False):
        return self._get_line(start_date=start_date, end_date=end_date, nper=nper, freq=freq, initial_period=initial_period)

    def get_table(self, start_date=None, end_date=None, nper=None, freq=None, initial_period=False, breakdown_level=0):
        return self.get_value(start_date=start_date, end_date=end_date, nper=nper, freq=freq, initial_period=initial_period)


class Flator(LineBuilder):
    def __init__(self, name, rate, base_date=None):
        LineBuilder.__init__(self, name=name)
        self.rate = rate
        if base_date is not None:
            self.base_date = pd.to_datetime(base_date)

    def __add__(self, other):
        return NotImplemented

    def __sub__(self, other):
        return NotImplemented

    def __mul__(self, other):
        try:
            float(other)
            z = self * Immutable(name="Base value", value=other)
            z.ignore_last_line = False
            return z
        except TypeError:
            if not hasattr(other, "get_value"):
                return NotImplemented
            z = Immutable(self.name + '-flated ' + other.name)

            def _line_fun(start_date=None, end_date=None, nper=None, freq=None, initial_period=False):
                cf = other.get_value(start_date=start_date, end_date=end_date, nper=nper, freq=freq,initial_period=initial_period)
                deflators = self.get_multipliers(start_date=start_date, end_date=end_date, nper=nper, freq=freq,
                                                 initial_period=initial_period)
                cf = deflators.values * cf
                cf = cf.rename({cf.index[0]: z.name})
                return cf
            setattr(z, "_get_line", _line_fun)

            def table_fun(start_date=None, end_date=None, nper=None, freq=None, initial_period=False, breakdown_level=1):
                values = z.get_value(start_date=start_date, end_date=end_date, nper=nper, freq=freq, initial_period=initial_period)
                if breakdown_level == 0:
                    table = pd.DataFrame(columns=values.columns)
                else:
                    table = other.get_table(start_date=start_date, end_date=end_date, nper=nper, freq=freq,
                                            initial_period=initial_period, breakdown_level=breakdown_level-1)
                    multipliers = self.get_multipliers(start_date=start_date, end_date=end_date, nper=nper, freq=freq,
                                                       initial_period=initial_period)
                    table = pd.concat((table, multipliers))*(values.values != 0)
                table = pd.concat((table, values), axis=0)
                return table
            setattr(z, "get_table", table_fun)
            z.ignore_last_line = False

            return z

    def __rmul__(self, other):
        return self.__mul__(other)

    def get_multipliers(self, start_date=None, end_date=None, nper=None, freq=None, initial_period=False):
        deflators = self._get_line(start_date=start_date, end_date=end_date, nper=nper, freq=freq,
                                   initial_period=True)
        base_date = self.base_date if hasattr(self, "base_date") else deflators.columns[0]
        taus = (deflators.columns - base_date).days/365
        deflators.loc[self.name] = (1+self.rate)**taus
        if not initial_period:
            deflators = deflators[deflators.columns[1:]]
        return deflators


class Aggregatable(LineBuilder):
    def __init__(self, name, freq_str="Y", value=np.nan, effective_date=None, nper=None, tenor=None):
        self.name = name
        self.value = value

        if tenor is not None and nper is not None:
            self.nper = nper
            self.tenor = tenor
            self.freq = int(12 * tenor / nper)
            self.freq_str = freq_months_to_freq_str(self.freq)
        else:
            self.freq_str = freq_str
            self.freq = freq_str_to_months(freq_str)
            if nper is not None:
                self.nper = nper
                self.tenor = int(nper * self.freq / 12)
            elif tenor is not None:
                self.tenor = tenor
                self.nper = int(tenor * 12 / self.freq)
            else:
                self.nper = None
                self.tenor = None

        if effective_date is not None:
            self.effective_date = pd.to_datetime(effective_date)
            if self.nper is not None:
                if self.freq_str == "2Q":
                    self.final_date = self.effective_date + 2*self.nper*pd.offsets.QuarterEnd()
                else:
                    self.final_date = pd.date_range(start=self.effective_date, periods=self.nper + 1, freq=freq_str)[-1]
            else:
                self.final_date = None
        else:
            self.effective_date = None
            self.final_date = None
        LineBuilder.__init__(self, name=name, effective_date=effective_date, tenor=self.tenor)

    def _get_line(self, start_date=None, end_date=None, nper=None, freq=None, initial_period=False):
        line = LineBuilder._get_line(self, start_date=start_date, end_date=end_date, nper=nper, freq=freq,
                                     initial_period=initial_period)
        freq = freq_str_to_months(freq)
        cf = self.value * line * freq / self.freq
        return cf


class Quantity(Aggregatable):
    def __init__(self, name, freq_str="Y", value=np.nan, effective_date=None, nper=None, tenor=None):
        Aggregatable.__init__(self, name=name, value=value, effective_date=effective_date, freq_str=freq_str, nper=nper, tenor=tenor)

    def __add__(self, other):
        if type(self) != type(other):
            return NotImplemented
        else:
            return LineBuilder.__add__(self, other)

    def __mul__(self, other):
        try:
            float(other)
            z = self * Immutable(name="Base value", value=other)
            z.ignore_last_line = False
            return z
        except TypeError:
            if not hasattr(other, "get_value"):
                return NotImplemented
            z = CashFlow(self.name + ' x ' + other.name)

            def line_fun(start_date=None, end_date=None, nper=None, freq=None, initial_period=False):
                values = other.get_value(start_date=start_date, end_date=end_date, nper=nper, freq=freq, initial_period=initial_period)
                quantities = self.get_multipliers(start_date=start_date, end_date=end_date, nper=nper, freq=freq,
                                                   initial_period=initial_period)
                values = quantities.values * values
                values = values.rename({values.index[0]: z.name})
                return values
            setattr(z, "_get_line", line_fun)

            def table_fun(start_date=None, end_date=None, nper=None, freq=None, initial_period=False, breakdown_level=1):
                cf = z.get_cf(start_date=start_date, end_date=end_date, nper=nper, freq=freq, initial_period=initial_period)
                if breakdown_level == 0:
                    table = pd.DataFrame(columns=cf.columns)
                else:
                    table = other.get_table(start_date=start_date, end_date=end_date, nper=nper, freq=freq,
                                            initial_period=initial_period, breakdown_level=breakdown_level-1)
                    quantities = self.get_multipliers(start_date=start_date, end_date=end_date, nper=nper, freq=freq,
                                                      initial_period=initial_period)
                    table = pd.concat((table*(quantities != 0).values, quantities))
                table = pd.concat((table, cf), axis=0)
                return table
            setattr(z, "get_table", table_fun)
            z.ignore_last_line = False

            return z

    def __rmul__(self, other):
        return self.__mul__(other)

    def get_multipliers(self, start_date=None, end_date=None, nper=None, freq=None, initial_period=False):
        return self._get_line(start_date=start_date, end_date=end_date, nper=nper, freq=freq, initial_period=initial_period)


class CashFlow(Aggregatable):
    def __init__(self, name, freq_str="Y", value=np.nan, effective_date=None, nper=None, tenor=None):
        Aggregatable.__init__(self, name=name, value=value, effective_date=effective_date, freq_str=freq_str, nper=nper, tenor=tenor)

    def __add__(self, other):
        if type(self) != type(other):
            return NotImplemented
        else:
            return Aggregatable.__add__(self, other)

    def __mul__(self, other):
        try:
            float(other)
            z = self*Quantity(name="Quantity", value=other, freq_str="Y",
                              effective_date=self.effective_date, nper=self.nper, tenor=self.tenor)
        except TypeError:
            z = CashFlow(name=other.name + " x " + self.name)

            def line_fun(start_date=None, end_date=None, nper=None, freq=None, initial_period=False):
                cf = self._get_line(start_date=start_date, end_date=end_date, nper=nper, freq=freq, initial_period=initial_period)
                multipliers = other.get_multipliers(start_date=start_date, end_date=end_date, nper=nper, freq=freq,
                                                   initial_period=initial_period)
                cf = multipliers.values * cf
                cf = cf.rename({cf.index[0]: z.name})
                return cf
            z._get_line = line_fun

            def table_fun(start_date=None, end_date=None, nper=None, freq=None, initial_period=False, breakdown_level=1):
                cf = z.get_cf(start_date=start_date, end_date=end_date, nper=nper, freq=freq, initial_period=initial_period)
                if breakdown_level == 0:
                    table = pd.DataFrame(columns=cf.columns)
                else:
                    table = self.get_cf(start_date=start_date, end_date=end_date, nper=nper, freq=freq,
                                            initial_period=initial_period)
                    multipliers = other.get_multipliers(start_date=start_date, end_date=end_date, nper=nper, freq=freq,
                                                       initial_period=initial_period)
                    table = pd.concat((table, multipliers))
                table = pd.concat((table, cf), axis=0)
                return table
            z.get_table = table_fun
            z.ignore_last_line = False
        return z

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        z = Quantity(f'{self.name}/{other.name}')

        def multiplier_fun(start_date=None, end_date=None, nper=None, freq=None, initial_period=False):
            self_cf = self.get_cf(start_date=start_date, end_date=end_date, nper=nper, freq=freq, initial_period=initial_period)
            other_cf = other.get_cf(start_date=start_date, end_date=end_date, nper=nper, freq=freq, initial_period=initial_period)
            multipliers = self_cf/other_cf.values
            multipliers = multipliers.rename({self.name: z.name})
            return multipliers
        setattr(z, "get_multipliers", multiplier_fun)
        return z

    def get_cf(self, start_date=None, end_date=None, nper=None, freq=None, initial_period=False):
        return self._get_line(start_date=start_date, end_date=end_date, nper=nper, freq=freq, initial_period=initial_period)

    def get_dcf(self, deflator=None, discount_rate=None, start_date=None, end_date=None, nper=None, freq=None, initial_period=False):
        if deflator is None and discount_rate is not None:
            new_periodicity = 12/freq_str_to_months(freq)  # in years
            effective_disc_rate = convert_rate(discount_rate, previous_periodicity=1, new_periodicity=new_periodicity)
            effective_disc_rate = discount_rate
            deflator = Flator(name="Discount", rate=-effective_disc_rate)
        elif deflator is not None and discount_rate is None:
            deflator = deflator
        else:
            raise ValueError("Exactly one of deflator and discount_date must be given")

        dcf = (deflator*self).get_cf(start_date=start_date, end_date=end_date, nper=nper, freq=freq, initial_period=initial_period)
        dcf = dcf.rename(index={dcf.index[0]: f'Discounted {self.name}'})
        return dcf

    def get_npv(self, deflator=None, discount_rate=None, start_date=None, end_date=None, nper=None, freq=None, initial_period=False):
        dcf = self.get_dcf(deflator=deflator, discount_rate=discount_rate, start_date=start_date, end_date=end_date, nper=nper, freq=freq, initial_period=initial_period)
        npv = pd.DataFrame(dcf.sum(axis=1).rename({self.name: f'{self.name} NPV'}), columns=[pd.to_datetime(start_date)])
        return npv.transpose()

    def get_table(self, start_date=None, end_date=None, nper=None, freq=None, initial_period=False, breakdown_level=0):
        return self.get_cf(start_date=start_date, end_date=end_date, nper=nper, freq=freq, initial_period=initial_period)


class MultipliedBaseValueCashFlow:
    def __new__(cls, name, base_value, rate=None, rate_name=None, quantity=None, effective_date=None, freq_str="Y", nper=None, tenor=None):
        cf = CashFlow(name, value=base_value, effective_date=effective_date, freq_str="Y", nper=effective_date, tenor=effective_date)
        if quantity is None and rate is None:
            raise ValueError("Exactly one of rate and multiplier must be provided.")
        elif quantity is None and rate is not None:
            if rate_name is None:
                raise ValueError("Rate name has to be provided")
            quantity = Flator(name=rate_name, rate=rate, base_date=effective_date)
        cf = quantity * cf
        cf.name = f'{quantity.name}-grown {name}'
        return cf


class SalesCashFlow(CashFlow):
    def __new__(cls, price, quantities, product_name, flator=None, rate=None, rate_name=None, base_date=None):
        try:
            float(price)
            price = Immutable(name=product_name, value=price)
        except TypeError:
            price = price

        if flator is None and rate is not None:
            if rate_name is None:
                rate_name = f'rate {rate:.1%}'
            deflator = Flator(name=rate_name, rate=rate, base_date=base_date)
        elif flator is not None and rate is None:
            deflator = flator
        else:
            raise ValueError("Excatly one of flator and rate must be provided.")

        price = deflator * price
        price.name = product_name + " price"
        price.ignore_last_line = False
        z = quantities*price
        try:
            z.name = product_name + " sales"
        except SyntaxError:
            z = CashFlow(name=product_name + " sales", value=z)
        return z


class FixedRateLoan(CashFlow):
    def __init__(self, name, principal, interest_rate, freq_str=None, tenor=None, nper=None, effective_date=None):
        self.name = name
        self.principal = principal
        self.interest_rate = interest_rate
        CashFlow.__init__(self, name=name, value=0, effective_date=effective_date, nper=nper, freq_str=freq_str, tenor=tenor)

        if self.interest_rate == 0:
            payment = self.principal / self.nper
        else:
            i = (self.interest_rate/12)*self.freq
            payment = self.principal * i * (1+i)**self.nper / ((1+i)**self.nper - 1)
        self.value = payment

    def get_payment(self):
        return self.value

    def get_table(self, start_date=None, end_date=None, nper=None, freq=None, initial_period=False, breakdown_level=1):
        return self.get_payment()


# ----------------------------------------------------------------------------------------------------------------------
# Corporate classes
# ----------------------------------------------------------------------------------------------------------------------

class EBITDA(dict):
    """
    Encapsulates a table with the following rows:

    Operative incomes
    - Operative expenses
    ---------------------
    EBITDA
    EBITDA Margin
    """
    def __init__(self, operating_revenues=None, operating_expenses=None):
        # We do not save the derived lines at initialization because they wouldn't update if the elemental ones changed
        dict.__init__(self)
        self["Operating Revenues"] = CashFlow(name=None, value=0)
        if operating_revenues is not None:
            self["Operating Revenues"] += operating_revenues
            self["Operating Revenues"].name = "Operating Revenues"
            self["Operating Revenues"].ignore_last_line = False

        self["Operating Expenses"] = CashFlow(name=None, value=0)
        if operating_expenses is not None:
            self["Operating Expenses"] += operating_expenses
            self["Operating Expenses"].name = "Operating Expenses"
            self["Operating Expenses"].ignore_last_line = False

    def _generate_ebitda(self):
        # We do not save ebitda while initiation, so that it automatically updates if we change revenues or expenses
        ebitda = self["Operating Revenues"] - self["Operating Expenses"]
        ebitda.name = "EBITDA"
        ebitda.ignore_last_line = False

        margin = ebitda/self["Operating Revenues"]
        margin.name = "EBITDA Margin"

        return ebitda, margin

    def get_cf(self, start_date=None, end_date=None, nper=None, freq=None, initial_period=False):
        ebitda, margin = self._generate_ebitda()
        return ebitda.get_cf(start_date=start_date, end_date=end_date, nper=nper, freq=freq, initial_period=initial_period)

    def get_table(self, start_date=None, end_date=None, nper=None, freq=None, initial_period=False, breakdown_level=1):
        ebitda, margin = self._generate_ebitda()
        table = ebitda.get_table(start_date=start_date, end_date=end_date, nper=nper, freq=freq, initial_period=initial_period, breakdown_level=breakdown_level)
        if "EBITDA Margin" not in table.index:
            margin_df = margin.get_multipliers(start_date=start_date, end_date=end_date, nper=nper, freq=freq, initial_period=initial_period)
            table = pd.concat((table, margin_df))
        return table


class Enterprise(dict):
    """
    Encapsulates a table with the following rows:

    Operative incomes
    - Operative expenses
    ---------------------
    EBITDA
    - Depreciation
    ---------------------
    EBIT
    - Taxes
    ---------------------
    NOPAT
    + Depreciation
    - CAPEX
    ---------------------
    Free Cash flow
    """

    def __init__(self, operating_revenues=None, operating_expenses=None, ebitda=None, ebitda_margin=None,
                 depreciations=None, capex=None):
        # We do not save the derived lines at initialization because they wouldn't update if the elemental ones changed

        dict.__init__(self)

        if operating_revenues is None and operating_expenses is None and ebitda is not None:
            self["EBITDA"] = ebitda
            if ebitda.name != "EBITDA":
                self["EBITDA"].name = "EBITDA"
                self["EBITDA"].ignore_last_line = False
            else:
                self["EBITDA"].ignore_last_line = True

            if ebitda_margin is not None:
                self["EBITDA Margin"] = ebitda_margin
                if ebitda_margin.name != "EBITDA Margin":
                    self["EBITDA Margin"].name = "EBITDA Margin"
                    self["EBITDA Margin"].ignore_last_line = False
                else:
                    self["EBITDA Margin"].ignore_last_line = True

        elif operating_revenues is not None and operating_expenses is not None and ebitda is None:
            self["Operating Revenues"] = CashFlow(name=None, value=0)
            if operating_revenues is not None:
                self["Operating Revenues"] += operating_revenues
                self["Operating Revenues"].name = "Operating Revenues"
                self["Operating Revenues"].ignore_last_line = False

            self["Operating Expenses"] = CashFlow(name=None, value=0)
            if operating_expenses is not None:
                self["Operating Expenses"] += operating_expenses
                self["Operating Expenses"].name = "Operating Expenses"
                self["Operating Expenses"].ignore_last_line = False

        else:
            raise ValueError("Only either an EBITDA or a combination of OpRev and OpEx must given.")

        self["D&A"] = CashFlow(name=None, value=0)
        if depreciations is not None:
            self["D&A"] += depreciations

        self["CapEx"] = CashFlow(name=None, value=0)
        if capex is not None:
            self["CapEx"] += capex

    def _generate_ebitda(self):
        # We do not save ebitda while initiation, so that it automatically updates if we change revenues or expenses
        try:
            ebitda = self["Operating Revenues"] - self["Operating Expenses"]
            ebitda.name = "EBITDA"
            ebitda.ignore_last_line = False

            margin = ebitda/self["Operating Revenues"]
            margin.name = "EBITDA Margin"
        except KeyError:
            ebitda = self["EBITDA"]
            try:
                margin = self["EBITDA Margin"]
            except KeyError:
                margin = None
        return ebitda, margin

    def get_ebitda(self, start_date=None, end_date=None, nper=None, freq=None, initial_period=False):
        ebitda, margin = self._generate_ebitda()
        return ebitda.get_cf(start_date=start_date, end_date=end_date, nper=nper, freq=freq, initial_period=initial_period)

    def get_ebitda_table(self, start_date=None, end_date=None, nper=None, freq=None, initial_period=False, breakdown_level=1):
        ebitda, margin = self._generate_ebitda()
        table = ebitda.get_table(start_date=start_date, end_date=end_date, nper=nper, freq=freq,
                                 initial_period=initial_period, breakdown_level=breakdown_level)
        if "EBITDA Margin" not in table.index and margin is not None:
            margin_df = margin.get_multipliers(start_date=start_date, end_date=end_date, nper=nper, freq=freq, initial_period=initial_period)
            table = pd.concat((table, margin_df))
        return table

    def _generate_ebit(self):
        ebitda, margin = self._generate_ebitda()
        ebit = ebitda - self["D&A"]
        ebit.name = "EBIT"
        ebit.ignore_last_line = False
        return ebit

    def get_ebit(self, start_date=None, end_date=None, nper=None, freq=None, initial_period=False):
        ebit = self._generate_ebit()
        return ebit.get_cf(start_date=start_date, end_date=end_date, nper=nper, freq=freq,initial_period=initial_period)

    def get_ebit_table(self, start_date=None, end_date=None, nper=None, freq=None, initial_period=False, breakdown_level=1):
        ebit = self._generate_ebit()
        return ebit.get_cf(start_date=start_date, end_date=end_date, nper=nper, freq=freq,
                           initial_period=initial_period, breakdown_level=breakdown_level)

    def _generate_noplat(self, tax_rate):
        ebit = self._generate_ebit()
        taxes = ebit*tax_rate
        noplat = ebit - taxes
        noplat.name = "NOPLAT"
        noplat.ignore_last_line = False
        return noplat

    def get_noplat(self, tax_rate, start_date=None, end_date=None, nper=None, freq=None, initial_period=False):
        noplat = self._generate_noplat(tax_rate)
        return noplat.get_cf(start_date=start_date, end_date=end_date, nper=nper, freq=freq, initial_period=initial_period)

    def get_noplat_table(self, tax_rate, start_date=None, end_date=None, nper=None, freq=None, initial_period=False, breakdown_level=1):
        noplat = self._generate_noplat(tax_rate)
        return noplat.get_cf(start_date=start_date, end_date=end_date, nper=nper, freq=freq,
                             initial_period=initial_period, breakdown_level=breakdown_level)

    def _generate_fcff(self, tax_rate):
        # fcff: free cash flow to firm
        depreciation = self["D&A"]
        capex = self["CapEx"]
        noplat = self._generate_noplat(tax_rate=tax_rate)

        fcff = noplat + depreciation - capex
        fcff.name = "FCFF"
        fcff.ignore_last_line = False
        return fcff

    def get_fcff(self, tax_rate, start_date=None, end_date=None, nper=None, freq=None, initial_period=False):
        fcff = self._generate_fcff(tax_rate=tax_rate)
        return fcff.get_cf(start_date=start_date, end_date=end_date, nper=nper, freq=freq, initial_period=initial_period)

    def get_table(self, tax_rate, start_date=None, end_date=None, nper=None, freq=None, initial_period=False):
        fcff = self._generate_fcff(tax_rate=tax_rate)
        return fcff.get_table(start_date=start_date, end_date=end_date, nper=nper, freq=freq, initial_period=initial_period)

    def get_dcf(self, tax_rate, deflator=None, discount_rate=None, start_date=None, end_date=None, nper=None, freq=None, initial_period=False):
        fcff = self._generate_fcff(tax_rate=tax_rate)
        return fcff.get_dcf(deflator=deflator, discount_rate=discount_rate, start_date=start_date, end_date=end_date,
                            nper=nper, freq=freq, initial_period=initial_period)

    def get_npv(self, tax_rate, deflator=None, discount_rate=None, start_date=None, end_date=None, nper=None, freq=None, initial_period=False):
        fcff = self._generate_fcff(tax_rate=tax_rate)
        return fcff.get_npv(deflator=deflator, discount_rate=discount_rate, start_date=start_date, end_date=end_date,
                            nper=nper, freq=freq, initial_period=initial_period)

    def get_ev(self, tax_rate, deflator=None, discount_rate=None, start_date=None, end_date=None, nper=None, freq=None, initial_period=False):
        return self.get_npv(tax_rate=tax_rate,deflator=deflator, discount_rate=discount_rate, start_date=start_date, end_date=end_date,
                            nper=nper, freq=freq, initial_period=initial_period)



# class Equity(Enterprise):
#     def __init__(self, debt, market_dict, enterprise_dict, operating_revenues=None, operating_expenses=None, ebitda=None,
#                  depreciations=None, capex=None):
#         Enterprise.__init__(self, market_dict=market_dict, enterprise_dict=enterprise_dict,
#                             operating_revenues=operating_revenues, operating_expenses=operating_expenses,
#                             ebitda=ebitda, depreciations=depreciations, capex=capex)
#         self.debt = debt
#
#     def get_cf(self):
#         # fcfe: free cash flow to equity
#         fcff_cf = Enterprise.get_cf(self)
#         debt_cf = self.debt.get_cf()
#
#         fcfe = fcff_cf.values - debt_cf.values
#         fcfe = pd.DataFrame(data=fcfe, index=["FCFE"], columns=fcff_cf.columns)
#         return fcfe
#
#     def get_table(self, breakdown_level=1):
#         if breakdown_level == 0:
#             table = self.get_cf()
#         else:
#             negative_capex = NegativeCF(self.capex,"- Capital Expenditures")
#             negative_depreciation = NegativeCF(self.depreciation,"- Depreciation")
#             negative_debt = NegativeCF(self.debt,"- Debt")
#             #breakdown_level -= 1
#             table_proj = pd.concat((self.get_ebitda_table(breakdown_level),
#                                     negative_depreciation.get_table(breakdown_level),
#                                     self.get_ebit(),
#                                     self.get_nopat(),
#                                     self.depreciation.get_table(breakdown_level),
#                                     negative_capex.get_table(breakdown_level),
#                                     Enterprise.get_cf(self)
#                                ), axis=0)
#             table = pd.concat((table_proj, negative_debt.get_cf(), self.get_cf(),self.get_dcf()), axis=0)
#         return table

