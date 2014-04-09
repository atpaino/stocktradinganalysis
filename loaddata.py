import stockdatastructs as sds

def load_nasdaq_data():
    """
    Returns a dictionary of HistoricData objects representing each symbol in the
    Nasdaq symbols list. The keys to the dictionary are the symbols.
    """
    #Open symbols file
    symbols_file = open('NasdaqTechSymbolList.txt', 'r')
    symbols = []
    for line in symbols_file:
        symbol = line.split('"')[1].rstrip()
        if not symbol.isalpha():
            #Skip this symbol
            continue
        symbols.append(symbol)

    #Build dictionary out of these symbols
    return { symbol : sds.HistoricData(symbol) for symbol in symbols }
