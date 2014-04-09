#Contains functions used to classify a proposed trade consisting of two HistoricData
#objects at a specific time as either successful (reverted to mean) or unsuccessful.
from singleseriesfns import *
from twoseriesfns import *

def bounded_roi(hd1, hd2, n=20, offset=20):
    """
    Calculates the average, bounded ROI for the proposed trade (assuming the symbol
    with the larger percent gain over offset+n:offset has been shorted).
    NOTE: offset must be greater than or equal to n
    """
    #Calculate percent gain in hd1 and hd2 to determine which would be shorted
    pg1 = (hd1.close[offset] - hd1.close[offset+n]) / hd1.close[offset+n]
    pg2 = (hd2.close[offset] - hd2.close[offset+n]) / hd2.close[offset+n]
    if pg1 > pg2:
        short = hd1
        long = hd2
    else:
        short = hd2
        long = hd1

    #Calculate ROI for shorted symbol
    roi_short = (short.close[offset] - short.close[offset-n]) / short.close[offset]

    #Calculate ROI for long symbol
    roi_long = (long.close[offset-n] - long.close[offset]) / long.close[offset]

    #Return the average of these ROI's, multiplied by 10 and bounded by tanh
    return sp.tanh(5 * (roi_short+roi_long))

def winning_trade_test(hd1, hd2, n=20, offset=20):
    """
    Alternative to bounded_roi for determing class of trade.
    Returns 1 iff the shorted position decreased AND the long position increased.
    """
    #Calculate percent gain in hd1 and hd2 to determine which would be shorted
    pg1 = (hd1.close[offset] - hd1.close[offset+n]) / hd1.close[offset+n]
    pg2 = (hd2.close[offset] - hd2.close[offset+n]) / hd2.close[offset+n]
    if pg1 > pg2:
        short = hd1
        long = hd2
    else:
        short = hd2
        long = hd1

    return 1 if ( short.close[offset] > short.close[offset-n] ) and ( long.close[offset-n] > long.close[offset] ) else 0

def mean_reversion_test(hd1, hd2, n=20, offset=20, hold_time=30, return_index=False):
    """
    Tests over the time period offset:offset-n to see if the pair reverts to the mean.
    Specifically, we are doing this by testing at each closing price in this time period
    to see if the long position is higher than its sma at the same time the short position
    is below its sma.
    """
    #Get short and long positions
    (short_pos, long_pos) = get_short_long(hd1, hd2, n, offset)

    #Calculate the simple moving average for each stock at time offset
    short_sma = sma(short_pos, offset=offset)
    long_sma = sma(long_pos, offset=offset)

    for i in xrange(offset, max(offset-hold_time, 0), -1):
        if short_pos.close[i] < short_sma and long_pos.close[i] > long_sma:
            if return_index:
                return i
            return 1

    #The pair has not reverted to the mean
    if return_index:
        return i
    return 0

def mean_ratio_reversion_test(hd1, hd2, n=20, offset=20, hold_time=30, return_index=False):
    """
    Tests over the time period offset:offset-hold_time to see if the price ratio of the
    price pair reverts to the mean.
    """
    #Get initial price ratio
    init_pr = hd1.close[offset]/hd2.close[offset]

    #Get mean for the pair
    pr_mean = mean_price_ratio(hd1, hd2, n=n, offset=offset)

    #Calculate coefficient to use to see if the price ratio switched sides of mean pr
    coeff = 1 if init_pr > pr_mean else -1

    for i in xrange(offset, max(offset-hold_time, 0), -1):
        if coeff*(hd1.close[i]/hd2.close[offset] - pr_mean) < 0:
            if return_index:
                return i
            return 1

    #The pair has not reverted to the mean
    if return_index:
        return i
    return 0
