# encoding: UTF-8

"""
DualThrust交易策略
"""

from datetime import time,datetime,timedelta

from vnpy.trader.vtObject import VtBarData
from vnpy.trader.vtConstant import EMPTY_STRING
from vnpy.trader.app.ctaStrategy.ctaBase import *
from vnpy.trader.app.ctaStrategy.ctaTemplate import (CtaTemplate,
                                                     BarGenerator,
                                                     ArrayManager)

########################################################################
class DualThrustStrategy(CtaTemplate):
    """DualThrust交易策略"""
    className = 'DualThrustStrategy'
    author = u'用Python的交易员'

    # 策略参数
    fixedSize = 1
    k1 = 0.6
    k2 = 0.4

    initDays = 10

    # 策略变量
    barList = []                # K线对象的列表

    dayOpen = 0
    dayHigh = 0
    dayLow = 0
    dayClose = 0
    lastdayOpen = 0
    lastdayHigh = 0
    lastdayLow = 0
    lastdayClose = 0
    initialized = False

    
    range = 0
    longEntry = 0
    shortEntry = 0
    exitTime = time(hour=14, minute=55)

    longEntered = False
    shortEntered = False

    # 策略参数
    fastWindow = 10  # 快速均线参数
    slowWindow = 60  # 慢速均线参数

    # 策略变量
    fastMa0 = EMPTY_FLOAT  # 当前最新的快速EMA
    fastMa1 = EMPTY_FLOAT  # 上一根的快速EMA

    slowMa0 = EMPTY_FLOAT
    slowMa1 = EMPTY_FLOAT


    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol',
                 'k1',
                 'k2']    

    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'pos',
               'range',
               'longEntry',
               'shortEntry',
               'exitTime'] 
    
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['pos']    

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(DualThrustStrategy, self).__init__(ctaEngine, setting) 
        
        self.bg = BarGenerator(self.onBar)
        self.barList = []
        self.am = ArrayManager()

        self.baselinetime = None
    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略初始化' %self.name)
    
        # 载入历史数据，并采用回放计算的方式初始化策略数值
        initData = self.loadBar(self.initDays)
        for bar in initData:
            self.onBar(bar)

        self.putEvent()

    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略启动' %self.name)
        self.putEvent()

    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略停止' %self.name)
        self.putEvent()

    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        self.bg.updateTick(tick)
        
    #----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        # 撤销之前发出的尚未成交的委托（包括限价单和停止单）
        self.cancelAll()

        am = self.am
        am.updateBar(bar)
        #if not am.inited:
        #    return

        # 计算快慢均线
        fastMa = am.sma(self.fastWindow, array=True)
        self.fastMa0 = fastMa[-1]
        self.fastMa1 = fastMa[-2]

        slowMa = am.sma(self.slowWindow, array=True)
        self.slowMa0 = slowMa[-1]
        self.slowMa1 = slowMa[-2]

        # 计算指标数值
        self.barList.append(bar)
        
        if len(self.barList) <= 2:
            return
        else:
            self.barList.pop(0)
        lastBar = self.barList[-2]

        if self.baselinetime == None:
            self.baselinetime = datetime.now() - timedelta(hours=20)
            print(self.baselinetime)

        # 新的一天
        if lastBar.datetime.date() != bar.datetime.date() or self.initialized == False:
        #if (bar.datetime - self.baselinetime).seconds >= 23*60*60 or self.initialized == False:
            #print("%d" % (bar.datetime - self.baselinetime).seconds)

            self.baselinetime = bar.datetime

            if self.initialized == False:

                self.lastdayHigh = float(bar.open) * 1.05
                self.lastdayLow = float(bar.open) * 0.95
                self.lastdayOpen = float(bar.open)
                self.lastdayClose = float(bar.open)

                self.range = max(self.lastdayHigh - self.lastdayClose, self.lastdayClose - self.lastdayLow)
                #self.range = self.lastdayHigh - self.lastdayLow
                self.longEntry = float(bar.open) + self.k1 * self.range
                self.shortEntry = float(bar.open)- self.k2 * self.range

            else:
                self.lastdayHigh = self.dayHigh
                self.lastdayLow = self.dayLow
                self.lastdayOpen = self.dayOpen
                self.lastdayClose = self.dayClose

                # 如果已经初始化
                self.range = max(self.lastdayHigh - self.lastdayClose, self.lastdayClose - self.lastdayLow)
                #self.range = self.lastdayHigh - self.lastdayLow
                self.longEntry = float(bar.open) + self.k1 * self.range
                self.shortEntry = float(bar.open) - self.k2 * self.range

            print("range %f, range percent %f, open %f, long entry %f, short entry %f" % (self.range, self.range/bar.open, bar.open, self.longEntry, self.shortEntry))
            print("time %s" % bar.datetime)
            #self.coverp = self.longEntry
            #self.sellp = self.shortEntry

            self.dayOpen = float(bar.open)
            self.dayHigh = float(bar.high)
            self.dayLow = float(bar.low)
            self.dayClose = float(bar.close)

            self.longEntered = False
            self.shortEntered = False
            self.initialized = True



        else:
            self.dayHigh = max(self.dayHigh, float(bar.high))
            self.dayLow = min(self.dayLow, float(bar.low))
            if 0:
                self.longstoptmp = max(self.longEntry,bar.high)
                self.shortstoptmp = min(self.shortEntry, bar.low)

                self.coverp = self.longEntry - (self.shortEntry - self.shortstoptmp)
                self.sellp = self.shortEntry + (self.longstoptmp - self.longEntry)

        '''
        if self.range < max(bar.high - bar.close, bar.lose - bar.low):
            self.range = max(bar.high - bar.close, bar.lose - bar.low)
            self.longEntry = float(bar.open) + self.k1 * self.range
            self.shortEntry = float(bar.open) + self.k2 * self.range
        '''
        # 尚未到收盘
        if not self.range:
            return

        if self.pos == 0:
            if float(bar.close) > self.dayOpen:
                #if not self.longEntered:
                if not self.longEntered and self.slowMa0 < self.fastMa0:
                    self.buy(self.longEntry, self.fixedSize, stop=True)
            else:
                #if not self.shortEntered:
                if not self.shortEntered and self.slowMa0 > self.fastMa0:

                    self.short(self.shortEntry, self.fixedSize, stop=True)

        # 持有多头仓位
        elif self.pos > 0:
            self.longEntered = True

            # 多头止损单
            self.sell(self.shortEntry, self.fixedSize, stop=True)
            #self.sell(self.sellp, self.fixedSize, stop=True)
            #self.sell(self.longEntry*0.99, self.fixedSize, stop=True)
            # 空头开仓单
            #if 1:
            #if not self.shortEntered:
            if not self.shortEntered and self.slowMa0 > self.fastMa0:
                self.short(self.shortEntry, self.fixedSize, stop=True)

        # 持有空头仓位
        elif self.pos < 0:
            self.shortEntered = True

            # 空头止损单
            self.cover(self.longEntry, self.fixedSize, stop=True)
            #self.cover(self.coverp, self.fixedSize, stop=True)
            #self.cover(self.shortEntry*1.01, self.fixedSize, stop=True)
            # 多头开仓单
            #if 1:
            #if not self.longEntered:
            if not self.longEntered and self.slowMa0 < self.fastMa0:
                self.buy(self.longEntry, self.fixedSize, stop=True)

        '''
        if bar.datetime.time() < self.exitTime:
            pass
            
        # 收盘平仓
        else:
            if self.pos > 0:
                self.sell(float(bar.close) * 0.99, abs(self.pos))
            elif self.pos < 0:
                self.cover(float(bar.close) * 1.01, abs(self.pos))
        '''
        # 发出状态更新事件
        self.putEvent()

    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        pass

    #----------------------------------------------------------------------
    def onTrade(self, trade):
        # 发出状态更新事件
        self.putEvent()

    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        try:
            if so.status == STOPORDER_CANCELLED:
                pass
                #print ("cancellling stop order orderid %s" % so.stopOrderID)
            else:
                pass
                #print("sending stop order %s %f %s" % (so.orderType, so.price,  so.stopOrderID))

                #order.direction = so.direction
                #order.offset = so.offset
                #DIRECTION_LONG
                #OFFSET_OPEN
        except Exception,e:
            print e