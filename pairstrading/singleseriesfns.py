#Contains functions that compute a statistic for a single HistoricData item from time
#offset+n through time offset.
import scipy.stats as sts

def variation_wrapper(hd, n=20, offset=0):
    """
    Calculates the variation on the closing price of hd from offset:offset+n
    """
    return sts.variation(hd.close[offset:offset+n])

def gain(hd, n=20, offset=0):
    """
    Calculates the gain over offset:offset+n in hd's closing prices
    """
    return ((hd.close[offset] - hd.close[offset+n]) / hd.close[offset+n])

def gain_vs_avg(hd, n=20, offset=0):
    """
    Calculates the gain of the closing price at offset vs the moving avg.
    """
    return ((hd.close[offset] - sma(hd, offset=offset)) / sma(hd, offset=offset))

def sma(hd, time_period=90, offset=0):
    """
    Returns the simple moving average for the stock over the specified period of time.
    Note: time_period is used instead of n since typically the time period here being
    used is greater than n.
    """
    if len(hd.close) >= offset+time_period:
        return sts.tmean(hd.close[offset:offset+time_period])
    else:
        return sts.tmean(hd.close[offset:])
