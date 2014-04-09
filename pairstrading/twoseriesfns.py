#Contains functions that compute a statistic on two given HistoricData objects.
import scipy.stats as sts
from singleseriesfns import *
import statsmodels.api as sm
import statsmodels.tsa.stattools as ts

def get_short_long(hd1, hd2, n=20, offset=0):
    """
    Returns a tuple of (short, long) where short is the stock that would have been
    shorted over the given time period (offset:offset+n])
    """
    if gain_vs_avg(hd1, n, offset) > gain_vs_avg(hd2, n, offset):
        short_pos = hd1
        long_pos = hd2
    else:
        short_pos = hd2
        long_pos = hd1

    return (short_pos, long_pos)

def pearsonr_wrapper(hd1, hd2, n=20, offset=0):
    """
    A wrapper around scipy.stats.pearsonr that returns the result of that for
    the two given HistoricData objects.
    Note: we are testing for correlation over a time period of length 10*n in the past
    """
    return sts.pearsonr(hd1.close[offset:offset+10*n], hd2.close[offset:offset+10*n])[0]

def cointegration_test(hd1, hd2, time_period=90, offset=0):
    """
    Tests for cointegration of the two given stocks by fitting them first with OLS and
    then returning the p-value from an Augmented Dickey-Fuller test.
    """
    #Fit using ordinary least squares
    ols_result = sm.OLS(hd1.close[offset:offset+time_period], hd2.close[offset:offset+time_period]).fit()
    
    #Calculate the p-value using the residual from the fitting
    return ts.adfuller(ols_result.resid)[1]

def current_price_ratio(hd1, hd2, n=20, offset=0):
    """
    Returns current price ratio hd1/hd2
    """
    return hd1.close[offset]/hd2.close[offset]

def get_price_ratios(hd1, hd2, n=20, time_period=400, offset=0):
    """
    Returns a list of the price ratio (hd1/hd2) for the closing prices for the given
    time period.
    """
    return [ hd1.close[i]/hd2.close[i] for i in xrange(offset, offset+time_period) ]

def mean_price_ratio(hd1, hd2, n=20, time_period=400, offset=0):
    """
    Calculates the mean of the price ratio of hd1/hd2 for the given time period
    """
    return sts.tmean(get_price_ratios(hd1, hd2, n, time_period, offset))
    
def std_price_ratio(hd1, hd2, n=20, time_period=400, offset=0):
    """
    Calculates the mean of the price ratio of hd1/hd2 for the given time period
    """
    return sts.tstd(get_price_ratios(hd1, hd2, n, time_period, offset))
