#Contains functions to facilitate the analysis of stock data to find potential pairs
#trades
import sklearn.preprocessing as preproc
import numpy as np
import citoolkit.neuralnetlib as nnlib
from .. import loaddata
from singleseriesfns import *
from twoseriesfns import *
from classificationfns import *

def default_filter(dataset, min_correlation=.5, min_cointegration=.9, min_spread=.04, \
        price_ratio_std=2):
    """
    Used as a preprocessor to remove pairs that do not meet a minimum criterion set.
    dataset := either data returned from all_pairs_calculation or an array of arrays
        containing 'stats' info
    price_ratio_std := the minimum number of standard deveations by which the current 
        price ratio should exceed the mean price ratio
    Returns a dataset in the same format, but with certain pairs removed.
    """
    #Setup lambda to determine how to access statistics array
    if 'stats' in dataset[0]:
        st = lambda dp : dp['stats']
    else:
        st = lambda dp : dp

    #Return filtered dataset
    return [ dp for dp in dataset if st(dp)[2] * st(dp)[3] < 0 and\
                                     st(dp)[4] > min_correlation and\
                                     st(dp)[5] > min_cointegration and\
                                     abs(st(dp)[2] - st(dp)[3]) > min_spread and\
                                     abs(st(dp[CUR_PRICE_RATIO_IND])-st(dp[MEAN_PRICE_RATIO_IND])) >= price_ratio_std*st(dp[STD_PRICE_RATION_IND]) ]

def all_pairs_calculation(data, two_series_fns, one_series_fns, n=20, offset=0, \
        duration=900, type='list'):
    """
    Applies stat_fns to the last n closing prices before time offset for all pairs 
    of stocks in data and returns the results as either a dictionary mapping each symbol 
    to a dictionary containing all the other symbols mapped to the stat_fn result, or as
    a list containing all possible pairs along with the computed statistic.
    """
    if type == 'dict':
        return { symbol1 : { symbol2 : (stat_fn(data[symbol1], data[symbol2], n, offset) \
                            for stat_fn in stat_fns) for symbol2 in data \
                            if symbol2 != symbol1 } for symbol1 in data }
    else:
        pairs_list = []
        keys = data.keys()

        #Build a list of all possible pairs without duplicating them
        for i in range(0, len(keys)-1):
            for j in range(i + 1, len(keys)):
                #Must be greater than or equal to duration, since we are testing over 
                #that time span
                if len(data[keys[i]].close) < duration or \
                   len(data[keys[j]].close) < duration:
                    continue

                pairs_list.append({ 'symbol1' : keys[i], 'symbol2' : keys[j], \
                        'stats' : [ fn(data[keys[a]], n, offset) for fn in one_series_fns \
                                    for a in (i, j) ]+[ stat_fn(data[keys[i]], \
                                    data[keys[j]], n, offset) for stat_fn in \
                                    two_series_fns ] })
        return pairs_list

def build_training_set(duration=20, n=20, initial_offset=80, \
        classification_fn=mean_reversion_test, filter_fn=default_filter, scale=True):
    """
    Constructs a training dataset using several statistical functions on each
    non-overlapping set of closing prices of length n for all pairs for the last year.
    duration := number of time steps to calculate for (in terms of n)
    n := time step (used to compute data looking backward and forward)
    correlation_cutoff := minimum required pearson-r correlation coefficient to be 
        considered. If a pair does not meet this, it is removed from the dataset.
    min_spread := the minimum required difference in percent changes between the two
        stocks in the pair. The pair is deleted if it does not meet this criteria.
    """
    #Get dataset
    all_data = loaddata.load_nasdaq_data()

    #Modify list of statistical functions to include classification function
    fns = list(two_series_fns)
    fns.append(classification_fn)

    #Build dataset by iterating over length in increments of n
    dataset = []
    for i in xrange(0, duration):
        dataset += all_pairs_calculation(all_data, fns, one_series_fns, n=n, \
                                         offset=n*i+initial_offset)
        print i

    #Eliminate ones that definitely won't work (i.e. neither has a positive %change)
    dataset = filter_fn(dataset)

    #Extract statistics data from dataset
    stats = [ dp['stats'] for dp in dataset ]

    if scale:
        #Separate features and labels (since we don't want to scale the labels)
        features = [ dp[:-1] for dp in stats]
        labels = [ dp[-1] for dp in stats ]

        #Scale dataset
        scaler = preproc.Scaler()
        scaled_features = scaler.fit_transform(features)

        #Recombine features with labels
        return [ np.append(scaled_features[i], labels[i]) \
                 for i in xrange(len(scaled_features)) ]
    else:
        return stats

def test_with_mlp():
    train = build_training_set(duration=5, initial_offset=300)
    validation = build_training_set(duration=2, initial_offset=180)
    test = build_training_set(duration=2, initial_offset=80)

    mlp = nnlib.mlp(train, validation, test)
    mlp.do_training(15, 10, True)

    mlp.graph_results()

    return (mlp, test)

def backtest(prediction_fn=lambda x:x, start_time=380, duration=5, step_size=20, \
        hold_time=30, filter_fn=default_filter, scale=True, \
        strategy_fn=mean_reversion_test):
    """
    Backtests the given strategy (represented by prediction_fn) from the given start time
    for the given duration. Tests all pairs every step_size amount of time. Will 'buy' a
    pair if the prediction_fn returns a 1 when given the data in all_pairs format and
    will hold it until either the pair reverts to the mean or hold_time is reached. Mean
    reversion is tested for at each unit of time.
    Returns a list containing data on each of the 'trades' made, including the ROI, hold
    time, time the trade was initiated, and the stocks involved.
    prediction_fn must accept a single array argument representing various data points for
    a pair. It will return either 1 (buy pair) or 0 (do nothing).
    duration := number of time steps to test over (in terms of step_size)
    """
    #Get dataset
    all_data = loaddata.load_nasdaq_data()

    results = []

    for t in xrange(start_time, start_time-(duration*step_size), -1*step_size):
        print t
        #Get all pairs data for time i
        dataset = all_pairs_calculation(all_data, two_series_fns, one_series_fns, \
                                        n=step_size, offset=t)
        
        #Eliminate ones that definitely won't work (i.e. neither has a positive %change)
        dataset = filter_fn(dataset)

        if scale:
            #Scale dataset
            scaler = preproc.Scaler()
            scaler.fit([ dp['stats'] for dp in dataset ])

        for dp in dataset:
            if scale:
                scaler.transform(dp['stats'])

            #Run each pair through prediction_fn
            if prediction_fn(dp['stats']) == 1:
                #Pair bought, evaluate trade
                hd1 = all_data[dp['symbol1']]
                hd2 = all_data[dp['symbol2']]
                closing_time = strategy_fn(hd1, hd2, step_size, t, hold_time, True)

                #Get short and long positions
                if gain_vs_avg(hd1, step_size, t) > gain_vs_avg(hd2, step_size, t):
                    short_pos = hd1
                    long_pos = hd2
                else:
                    short_pos = hd2
                    long_pos = hd1

                #Measure the ROI at closing_time
                long_roi = (long_pos.close[closing_time] - long_pos.close[t]) / long_pos.close[t]
                short_roi = (short_pos.close[t] - short_pos.close[closing_time]) / short_pos.close[t]
                avg_roi = (long_roi + short_roi) / 2
                results.append([ avg_roi, t-closing_time, t, dp['symbol1'], dp['symbol2'] ])

    return results

#Define a list of default functions used to calculate statistics between two stocks at
#time offset for time n (looking backwards). All of these functions must accept two
#HistoricData objects, a length of time n, and a time offset.
two_series_fns = [ pearsonr_wrapper, cointegration_test, mean_price_ratio, std_price_ratio,
                   current_price_ratio ]
CORRELATION_IND = 4
COINTEGRATION_IND = 5
MEAN_PRICE_RATIO_IND = 6
STD_PRICE_RATION_IND = 7
CUR_PRICE_RATIO_IND = 8

#Same as above, but compute statistic for just one time series
one_series_fns = [ variation_wrapper, gain_vs_avg ]
VARIATION_IND = 0 #and 1
GAIN_IND = 2 #and 3
