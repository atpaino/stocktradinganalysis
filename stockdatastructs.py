from trading import DATA_PATH

class MarketDatapoint:
    """
    Contains various data corresponding to a particular day for a particular symbol.
    """

    def __init__(self, line):
        """
        Initializes this datapoint by extracting data from the CSV line given.
        """
        #Break up data from the line
        try:
            [ date, op, high, low, close, vol, adjusted_close ] = line.rstrip().split(',')
        except ValueError:
            self.date = None
            return

        #Convert numeric values to floating points and assign data to this object
        self.date = date
        self.open = float(op)
        self.high = float(high)
        self.low = float(low)
        self.close = float(close)
        self.volume = float(vol)
        self.adj_close = float(adjusted_close)

class HistoricData:
    """
    Contains all the historic market data for a given symbol.
    """

    def __init__(self, symbol):
        """
        Initializes this object with the data of the given symbol.
        """
        #Open the file for the given symbol
        data = open('{}\{}.csv'.format(DATA_PATH, symbol), 'r')

        #Build dataset from file
        self.data = [ MarketDatapoint(line) for line in data ]
        self.close = [ dp.close for dp in self.data ]

        self.symbol = symbol

        data.close()
