from trading import DATA_PATH
import httplib

#Setup connection to yahoo site
conn = httplib.HTTPConnection("ichart.finance.yahoo.com", 80)

def save_symbol(symbol):
    """
    Writes the csv file of the last 10 years market data for this symbol
    """
    #Setup the request
    conn.request("GET", '/table.csv?s={}&d=0&e=28&g=d&a=3&b=12&c=2000&ignore=.csv'.format(symbol))

    #Get the csv data
    resp = conn.getresponse()
    data = resp.read()

    #Remove first line from data, which is just a header
    [header, real_data] = data.split('\n', 1)

    #Create the file for this symbol, titled 'symbol.csv'
    f = open('{}\{}.csv'.format(DATA_PATH, symbol), 'w')
    f.write(real_data)
    f.close()

#Iterate over list of Nasdaq, S&P 500, and Dow symbols
symbols = open('NasdaqTechSymbolList.txt', 'r')
i = 0
for line in symbols:
    symbol = line.split('"')[1].rstrip()
    if not symbol.isalpha():
        #Skip this symbol because it has some weird formatting
        continue

    save_symbol(symbol)

    i += 1

    print 'Symbol {} completed (Number {})'.format(symbol, i)

symbols.close()
conn.close()

print 'Saving stock data completed.'
