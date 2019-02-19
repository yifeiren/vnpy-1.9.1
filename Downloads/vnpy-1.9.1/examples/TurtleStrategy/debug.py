# encoding: UTF-8


from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt

from turtleEngine import BacktestingEngine



if __name__ == '__main__':
    engine = BacktestingEngine()
    engine.setPeriod(datetime(2014, 1, 1), datetime(2018, 12, 12))
    engine.initPortfolio('setting.csv', 10000000)

    engine.loadData()
    engine.runBacktesting()
    engine.showResult()

    tradeList = engine.getTradeData('RB888')
    for trade in tradeList:
        print '%s %s %s %s@%s %s' %(trade.vtSymbol, trade.direction, trade.offset,
                                 trade.volume, trade.price, trade.dt)