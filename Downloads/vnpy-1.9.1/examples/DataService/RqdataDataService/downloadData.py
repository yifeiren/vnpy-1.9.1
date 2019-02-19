# encoding: UTF-8
# coding: UTF-8
"""
立即下载数据到数据库中，用于手动执行更新操作。
"""

from dataService import *
from csv import DictReader


if __name__ == '__main__':

    # df = getallInstrments()
    # ls = {}
    #
    # for ix, row in df.iterrows():
    #     symbol = df.ix[ix,'order_book_id']
    #     margin_rate = df.ix[ix,'margin_rate']
    #     trading_hours = df.ix[ix, 'trading_hours']
    #     name = df.ix[ix,'symbol']
    #     #print(symbol)
    #     if symbol not in ls and '99' in symbol:
    #         print (symbol,margin_rate,trading_hours)
    #         print (name)
    #
    #
    #         #downloadMinuteBarBySymbol(symbol)
    #         downloadDailyBarBySymbol(symbol)
    with open('/home/yf/Downloads/vnpy-1.9.1/vnpy/trader/app/ctaStrategy/strategy/setting.csv') as f:
        r = DictReader(f)
        for d in r:
            downloadDailyBarBySymbol(d['vtSymbol'])
