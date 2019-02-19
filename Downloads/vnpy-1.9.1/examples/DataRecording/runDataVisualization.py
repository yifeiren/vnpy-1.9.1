# encoding: UTF-8

import multiprocessing
from time import sleep
from datetime import datetime, time

from vnpy.event import EventEngine2
from vnpy.trader.vtEvent import EVENT_LOG, EVENT_ERROR
from vnpy.trader.vtEngine import MainEngine, LogEngine
#from vnpy.trader.gateway import ctpGateway
from vnpy.trader.app import dataRecorder
from vnpy.trader.gateway import okexGateway


from datetime import datetime, timedelta
from collections import OrderedDict
from itertools import product
import multiprocessing
import copy

import pymongo
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt

# 如果安装了seaborn则设置为白色风格
try:
    import seaborn as sns       
    sns.set_style('whitegrid')  
except ImportError:
    pass

from vnpy.trader.vtGlobal import globalSetting
from vnpy.trader.vtObject import VtTickData, VtBarData
from vnpy.trader.vtConstant import *
from vnpy.trader.vtGateway import VtOrderData, VtTradeData
from matplotlib.pylab import date2num
import datetime
import matplotlib.dates as mdates
import matplotlib.font_manager as font_manager
from matplotlib.ticker import MultipleLocator, FormatStrFormatter


# ----------------------------------------------------------------------
def loadHistoryData(dbName,symbol,type, forecast = 0):
    """载入历史数据"""
    try:
        dbClient = pymongo.MongoClient(globalSetting['mongoHost'], globalSetting['mongoPort'])
        collection = dbClient[dbName][symbol]

        #output(u'开始载入数据')

        #flt = {'type': {'$eq': type}}
        d1 = datetime.datetime.now()
        d2 = d1 - datetime.timedelta(days=1)
        flt = {'futureindex':{'$eq':0}}
        #flt = {'buy': {'$eq': 0}}
        #flt = {'thisweekvsspot':{'$gt':1}}


        cx = collection.find(flt)

        for data in cx:
        # 获取时间戳对象
            #dt = data['datetime'].time()
            collection.delete_one(data)
            print u'删除无效数据，时间戳：%s' % data['datetime']

        if forecast ==0:
            flt = {'datetime': {'$gte': d2,
                                '$lt': d1},'type': {'$eq': type} }
        else:
            flt = {'datetime': {'$gte': d2,
                                '$lt': d1},'type': {'$eq': type}, 'forecast': {'$gt':0} }
        initCursor = collection.find(flt).sort('datetime')



        #data = pd.DataFrame(list(collection.find(flt).sort('datetime')))
        data = pd.DataFrame(list(collection.find(flt)))
        del data['_id']
        data = data[['datetime', 'buy', 'sell', 'type', 'nextweekvsthisweek', 'quartervsthisweek', 'quartervsnextweek', 'futureindex', 'forecast', 'thisweekvsspot']]
        return (data)
    except Exception,e:
        print e


def visualize():


    try:

        plt.ion()
        fig, (ax,ax2) = plt.subplots(2,sharex=True)
        ax.xaxis_date()

        #plt.show()

        while True:
            hist_data_type1 = loadHistoryData('VnTrader_Tick_Db', 'eos.OKEX', 1)
            hist_data_type2 = loadHistoryData('VnTrader_Tick_Db', 'eos.OKEX', 2)
            hist_data_type3 = loadHistoryData('VnTrader_Tick_Db', 'eos.OKEX', 3)
            hist_data_type4 = loadHistoryData('VnTrader_Tick_Db', 'eos.OKEX', 3,1)

            ax.clear()
            ax2.clear()
            ax.plot(hist_data_type1['datetime'],hist_data_type1['buy'], label='this_week')
            ax.plot(hist_data_type2['datetime'],hist_data_type2['buy'], label='next_week')
            ax.plot(hist_data_type3['datetime'],hist_data_type3['buy'], label='quarter')
            ax.plot(hist_data_type3['datetime'],hist_data_type3['futureindex'], label='futureindex')
            if hist_data_type4 != None:
                ax.plot(hist_data_type4['datetime'],hist_data_type4['forecast'], label='forecast')


            ax2.plot(hist_data_type3['datetime'],hist_data_type3['quartervsthisweek'], label='quarter/this week')
            ax2.plot(hist_data_type3['datetime'],hist_data_type3['quartervsnextweek'], label='quarter/next week')
            ax2.plot(hist_data_type1['datetime'],hist_data_type1['nextweekvsthisweek'], label='next week/this week')
            ax2.plot(hist_data_type1['datetime'],hist_data_type1['thisweekvsspot'], label='this week/spot')



            props = font_manager.FontProperties(size=10)
            leg = ax.legend(loc='upper left', shadow=True, fancybox=True, prop=props)
            leg.get_frame().set_alpha(0.5)

            xfmt = mdates.DateFormatter('%y-%m-%d %H:%M')
            ax.xaxis.set_major_formatter(xfmt)

            props = font_manager.FontProperties(size=10)
            leg = ax2.legend(loc='upper left', shadow=True, fancybox=True, prop=props)
            leg.get_frame().set_alpha(0.5)

            xfmt = mdates.DateFormatter('%y-%m-%d %H:%M')
            ax2.xaxis.set_major_formatter(xfmt)

            #plt.grid()
            plt.draw()
            plt.pause(300)
#            plt.plot()
#            plt.show()
            #sleep(1)

    except Exception,e:
        print e


def isoStr2utc8Str(isoStr):
    # 取出timestamp，解析转成iso8601 navie datetime
    utc = datetime.datetime.strptime(isoStr, '%Y-%m-%dT%H:%M:%S.%fZ')
    # utc navie datetime设置时区，再换成本地时区，最后解析成字符串。时区可以硬编码。
    #utc8Time = utc.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    #utc8Time= datetime.strptime(utc, '%Y-%m-%d %H:%M:%S.%f')
    # utc8Time = utc.replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal()).replace(tzinfo=None)
    return utc

def convert_database(dbName,symbol):
    try:
        dbClient = pymongo.MongoClient(globalSetting['mongoHost'], globalSetting['mongoPort'])
        collection = dbClient[dbName][symbol]

        flt = {}
        initCursor = collection.find(flt)
        i = 0
        for d in initCursor:
            #convert Time
            #d['datetime'] = isoStr2utc8Str(d['Time'])
            #collection.update({'_id': d['_id']}, {'$set': {'datetime': d['datetime']}})
            #convert high/low/open/close
            d['high'] = float(d['High'])
            collection.update({'_id': d['_id']}, {'$set': {'high': d['high']}})
            d['low'] = float(d['Low'])
            collection.update({'_id': d['_id']}, {'$set': {'low': d['low']}})
            d['open'] = float(d['Open'])
            collection.update({'_id': d['_id']}, {'$set': {'open': d['open']}})
            d['close'] = float(d['Close'])
            collection.update({'_id': d['_id']}, {'$set': {'close': d['close']}})
            print(i)
            i = i + 1
            # 载入回测数据

    except Exception,e:
        print e



def visualize_spot_future():

    try:
        dbClient = pymongo.MongoClient(globalSetting['mongoHost'], globalSetting['mongoPort'])
        collection = dbClient['Matrixdata_bar']['EOS/USDT.OK']
        d1 = datetime.datetime.now()
        d2 = d1 - datetime.timedelta(days=100)

        flt = {'datetime': {'$gte': (d2),
                            '$lt': (d1)}}
        #flt = {}
        data = pd.DataFrame(list(collection.find(flt).sort('datetime')))
        #data = pd.DataFrame(list(collection.find(flt)))
        #del data['_id']
        data = data[['datetime', 'high','low','close']]

        collection1 = dbClient['Matrixdata_bar']['EOS/USD.OK.TW']

        d1 = datetime.datetime.now()
        d2 = d1 - datetime.timedelta(days=100)
        flt = {'datetime': {'$gte': (d2),
                            '$lt': (d1)}}
        #flt = {}
        data1 = pd.DataFrame(list(collection1.find(flt).sort('datetime')))
        #data1 = pd.DataFrame(list(collection1.find(flt)))
        #del data['_id']
        data1 = data1[['datetime', 'high','low','close']]

        #plt.ion()

        fig = plt.figure()
        #ax1 = plt.subplot2grid((1,1),(0,0))
        ax1 = plt.subplot(111)
        plt.ylabel("Price")
        plt.xlabel("Date")

        #fig, (ax,ax2) = plt.subplots(2,sharex=True)
        #ax.xaxis_date()
        ymajorLocator = MultipleLocator(0.1)
        ax1.yaxis.set_major_locator(ymajorLocator)
        #ymajorLocator = MultipleLocator(0.5)  # 将y轴主刻度标签设置为0.5的倍数
        ymajorFormatter = FormatStrFormatter('%1.1f')  # 设置y轴标签文本的格式

        ax1.yaxis.set_major_formatter(ymajorFormatter)
        ax1.yaxis.grid(True, which = 'major')

        #ax1.set_yticks([0,5.8259])

        ax1.plot(data['datetime'],data['close'], label='Spot')
        ax1.plot(data1['datetime'],data1['close'], label='TW')

        # data_max = max(data['low'])
        # data_min = min(data['low'])
        # print(data_max)
        # print(data_min)

        #ax2.plot(hist_data_type3['datetime'],hist_data_type3['quartervsthisweek'], label='quarter/this week')

        props = font_manager.FontProperties(size=10)
        leg = ax1.legend(loc='upper left', shadow=True, fancybox=True, prop=props)
        leg.get_frame().set_alpha(0.5)

        xfmt = mdates.DateFormatter('%y-%m-%d %H:%M')
        ax1.xaxis.set_major_formatter(xfmt)
        #
        # props = font_manager.FontProperties(size=10)
        # leg = ax2.legend(loc='upper left', shadow=True, fancybox=True, prop=props)
        # leg.get_frame().set_alpha(0.5)
        #
        # xfmt = mdates.DateFormatter('%y-%m-%d %H:%M')
        # ax2.xaxis.set_major_formatter(xfmt)

        #plt.pause(300)
        #plt.draw()
        plt.show()

        print('a')
    except Exception,e:
        print e


if __name__ == '__main__':
    #visualize()
    visualize_spot_future()
    #convert_database('Matrixdata_bar','EOS/USDT.OK')
    #convert_database('Matrixdata_bar', 'EOS/USD.OK.TW')