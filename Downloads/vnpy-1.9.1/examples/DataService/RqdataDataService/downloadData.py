# encoding: UTF-8

"""
立即下载数据到数据库中，用于手动执行更新操作。
"""

from dataService import *


if __name__ == '__main__':
    downloadMinuteBarBySymbol('IF99')
    downloadMinuteBarBySymbol('IA99')
    #downloadMinuteBarBySymbol('CU99')
    #downloadDailyBarBySymbol('IF99')
    #downloadDailyBarBySymbol('TA99')
    #downloadDailyBarBySymbol('I99')