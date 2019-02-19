# encoding: UTF-8

"""
单标的海龟交易策略，实现了完整海龟策略中的信号部分。
"""

from __future__ import division

from vnpy.trader.vtObject import VtBarData
from vnpy.trader.vtConstant import DIRECTION_LONG, DIRECTION_SHORT
from vnpy.trader.app.ctaStrategy.ctaTemplate import (CtaTemplate, 
                                                     BarGenerator, 
                                                     ArrayManager)


from collections import defaultdict

from vnpy.trader.vtConstant import (DIRECTION_LONG, DIRECTION_SHORT,
                                    OFFSET_OPEN, OFFSET_CLOSE)
from vnpy.trader.vtUtility import ArrayManager

from csv import DictReader

MAX_PRODUCT_POS = 4  # 单品种最大持仓
MAX_DIRECTION_POS = 10  # 单方向最大持仓

DAILY_DB_NAME = 'VnTrader_Daily_Db'


SIZE_DICT = {}
PRICETICK_DICT = {}
VARIABLE_COMMISSION_DICT = {}
FIXED_COMMISSION_DICT = {}
SLIPPAGE_DICT = {}

########################################################################
class TurtleTradingMultiStrategy(CtaTemplate):
    """海龟交易策略"""
    className = 'TurtleTradingMultiStrategy'
    author = u'用Python的交易员'

    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['pos']


    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(TurtleTradingMultiStrategy, self).__init__(ctaEngine, setting)

        self.ctaEngine = ctaEngine
        self.bgDict ={}

    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略初始化' %self.name)


        self.vtSymbolList = []
        self.portfolioValue = 100000
        self.initDays = 30

        with open('/home/yf/Downloads/vnpy-1.9.1/vnpy/trader/app/ctaStrategy/strategy/setting.csv') as f:
            r = DictReader(f)
            for d in r:
                self.vtSymbolList.append(d['vtSymbol'])

                SIZE_DICT[d['vtSymbol']] = int(d['size'])
                PRICETICK_DICT[d['vtSymbol']] = float(d['priceTick'])
                VARIABLE_COMMISSION_DICT[d['vtSymbol']] = float(d['variableCommission'])
                FIXED_COMMISSION_DICT[d['vtSymbol']] = float(d['fixedCommission'])
                SLIPPAGE_DICT[d['vtSymbol']] = float(d['slippage'])
                self.ctaEngine.subscribeMarketData(d['vtSymbol'])
                self.ctaEngine.addtickStrategy(self.ctaEngine.strategyDict['TurtleTradingMulti'],d['vtSymbol'])

        self.portfolio = TurtlePortfolio(self)
        self.portfolio.init(self.portfolioValue, self.vtSymbolList, SIZE_DICT)

        print(u'投资组合的合约代码%s' % (self.vtSymbolList))
        print(u'投资组合的初始价值%s' % (self.portfolioValue))

        for vtSymbol in self.vtSymbolList:
            bg = BarGenerator(self.onBar)

            self.bgDict[vtSymbol] = bg

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
        #print(tick.vtSymbol)
        try:
            bg = self.bgDict[tick.vtSymbol]
            bg.updateTick(tick)
        except Exception as ex:
            pass


    #----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        #self.cancelAll()
        self.portfolio.onBar(bar)

        # # 同步数据到数据库
        # self.saveSyncData()
    
        # 发出状态更新事件
        self.putEvent()        

    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        pass

    #----------------------------------------------------------------------
    def onTrade(self, trade):

        self.putEvent()

    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        pass
    

    # ----------------------------------------------------------------------
    def sendOrder(self, vtSymbol, direction, offset, price, volume):
        print("%s %s offset %s %d@%f" % (direction, vtSymbol, offset, volume, price))

        # """记录交易数据（由portfolio调用）"""
        # # 对价格四舍五入
        # priceTick = PRICETICK_DICT[vtSymbol]
        # price = int(round(price / priceTick, 0)) * priceTick
        #
        # # 记录成交数据
        # trade = TradeData(vtSymbol, direction, offset, price, volume)
        # l = self.tradeDict.setdefault(self.currentDt, [])
        # l.append(trade)
        # self.result.updateTrade(trade)


########################################################################
class TurtleResult(object):
    """一次完整的开平交易"""

    # ----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.unit = 0
        self.entry = 0  # 开仓均价
        self.exit = 0  # 平仓均价
        self.pnl = 0  # 盈亏

    # ----------------------------------------------------------------------
    def open(self, price, change):
        """开仓或者加仓"""
        cost = self.unit * self.entry  # 计算之前的开仓成本
        cost += change * price  # 加上新仓位的成本
        self.unit += change  # 加上新仓位的数量
        self.entry = cost / self.unit  # 计算新的平均开仓成本

    # ----------------------------------------------------------------------
    def close(self, price):
        """平仓"""
        self.exit = price
        self.pnl = self.unit * (self.exit - self.entry)


########################################################################
class TurtleSignal(object):
    """海龟信号"""

    # ----------------------------------------------------------------------
    def __init__(self, portfolio, vtSymbol,
                 entryWindow, exitWindow, atrWindow,
                 profitCheck=False):
        """Constructor"""
        self.portfolio = portfolio  # 投资组合

        self.vtSymbol = vtSymbol  # 合约代码
        self.entryWindow = entryWindow  # 入场通道周期数
        self.exitWindow = exitWindow  # 出场通道周期数
        self.atrWindow = atrWindow  # 计算ATR周期数
        self.profitCheck = profitCheck  # 是否检查上一笔盈利

        self.am = ArrayManager(60)  # K线容器

        self.atrVolatility = 0  # ATR波动率
        self.entryUp = 0  # 入场通道
        self.entryDown = 0
        self.exitUp = 0  # 出场通道
        self.exitDown = 0

        self.longEntry1 = 0  # 多头入场位
        self.longEntry2 = 0
        self.longEntry3 = 0
        self.longEntry4 = 0
        self.longStop = 0  # 多头止损位

        self.shortEntry1 = 0  # 空头入场位
        self.shortEntry2 = 0
        self.shortEntry3 = 0
        self.shortEntry4 = 0
        self.shortStop = 0  # 空头止损位

        self.unit = 0  # 信号持仓
        self.result = None  # 当前的交易
        self.resultList = []  # 交易列表
        self.bar = None  # 最新K线

    # ----------------------------------------------------------------------
    # def onBar(self, bar):
    #     """"""
    #     self.bar = bar
    #     self.am.updateBar(bar)
    #     if not self.am.inited:
    #         return
    #
    #     self.generateSignal(bar)
    #     self.calculateIndicator()

    def onBar(self, bar):
        """"""
        self.bar = bar
        self.am.updateBar(bar)
        while not self.am.inited:
            self.am.updateBar(bar)

        self.generateSignal(bar)
        self.calculateIndicator()

    # ----------------------------------------------------------------------
    def generateSignal(self, bar):
        """
        判断交易信号
        要注意在任何一个数据点：buy/sell/short/cover只允许执行一类动作
        """
        # 如果指标尚未初始化，则忽略
        if not self.longEntry1:
            return

        # 优先检查平仓
        if self.unit > 0:
            longExit = max(self.longStop, self.exitDown)

            if bar.low <= longExit:
                self.sell(longExit)
                return
        elif self.unit < 0:
            shortExit = min(self.shortStop, self.exitUp)
            if bar.high >= shortExit:
                self.cover(shortExit)
                return

        # 没有仓位或者持有多头仓位的时候，可以做多（加仓）
        if self.unit >= 0:
            trade = False

            if bar.high >= self.longEntry1 and self.unit < 1:
                self.buy(self.longEntry1, 1)
                trade = True

            if bar.high >= self.longEntry2 and self.unit < 2:
                self.buy(self.longEntry2, 1)
                trade = True

            if bar.high >= self.longEntry3 and self.unit < 3:
                self.buy(self.longEntry3, 1)
                trade = True

            if bar.high >= self.longEntry4 and self.unit < 4:
                self.buy(self.longEntry4, 1)
                trade = True

            if trade:
                return

        # 没有仓位或者持有空头仓位的时候，可以做空（加仓）
        if self.unit <= 0:
            if bar.low <= self.shortEntry1 and self.unit > -1:
                self.short(self.shortEntry1, 1)

            if bar.low <= self.shortEntry2 and self.unit > -2:
                self.short(self.shortEntry2, 1)

            if bar.low <= self.shortEntry3 and self.unit > -3:
                self.short(self.shortEntry3, 1)

            if bar.low <= self.shortEntry4 and self.unit > -4:
                self.short(self.shortEntry4, 1)

    # ----------------------------------------------------------------------
    def calculateIndicator(self):
        """计算技术指标"""
        self.entryUp, self.entryDown = self.am.donchian(self.entryWindow)
        self.exitUp, self.exitDown = self.am.donchian(self.exitWindow)

        # 有持仓后，ATR波动率和入场位等都不再变化
        if not self.unit:
            self.atrVolatility = self.am.atr(self.atrWindow)

            self.longEntry1 = self.entryUp
            self.longEntry2 = self.entryUp + self.atrVolatility * 0.5
            self.longEntry3 = self.entryUp + self.atrVolatility * 1
            self.longEntry4 = self.entryUp + self.atrVolatility * 1.5
            self.longStop = 0

            self.shortEntry1 = self.entryDown
            self.shortEntry2 = self.entryDown - self.atrVolatility * 0.5
            self.shortEntry3 = self.entryDown - self.atrVolatility * 1
            self.shortEntry4 = self.entryDown - self.atrVolatility * 1.5
            self.shortStop = 0

    # ----------------------------------------------------------------------
    def newSignal(self, direction, offset, price, volume):
        """"""
        self.portfolio.newSignal(self, direction, offset, price, volume)

    # ----------------------------------------------------------------------
    def buy(self, price, volume):
        """买入开仓"""
        price = self.calculateTradePrice(DIRECTION_LONG, price)

        self.open(price, volume)
        self.newSignal(DIRECTION_LONG, OFFSET_OPEN, price, volume)

        # 以最后一次加仓价格，加上两倍N计算止损
        self.longStop = price - self.atrVolatility * 2

    # ----------------------------------------------------------------------
    def sell(self, price):
        """卖出平仓"""
        price = self.calculateTradePrice(DIRECTION_SHORT, price)
        volume = abs(self.unit)

        self.close(price)
        self.newSignal(DIRECTION_SHORT, OFFSET_CLOSE, price, volume)

    # ----------------------------------------------------------------------
    def short(self, price, volume):
        """卖出开仓"""
        price = self.calculateTradePrice(DIRECTION_SHORT, price)

        self.open(price, -volume)
        self.newSignal(DIRECTION_SHORT, OFFSET_OPEN, price, volume)

        # 以最后一次加仓价格，加上两倍N计算止损
        self.shortStop = price + self.atrVolatility * 2

    # ----------------------------------------------------------------------
    def cover(self, price):
        """买入平仓"""
        price = self.calculateTradePrice(DIRECTION_LONG, price)
        volume = abs(self.unit)

        self.close(price)
        self.newSignal(DIRECTION_LONG, OFFSET_CLOSE, price, volume)

    # ----------------------------------------------------------------------
    def open(self, price, change):
        """开仓"""
        self.unit += change

        if not self.result:
            self.result = TurtleResult()
        self.result.open(price, change)

    # ----------------------------------------------------------------------
    def close(self, price):
        """平仓"""
        self.unit = 0

        self.result.close(price)
        self.resultList.append(self.result)
        self.result = None

    # ----------------------------------------------------------------------
    def getLastPnl(self):
        """获取上一笔交易的盈亏"""
        if not self.resultList:
            return 0

        result = self.resultList[-1]
        return result.pnl

    # ----------------------------------------------------------------------
    def calculateTradePrice(self, direction, price):
        """计算成交价格"""
        # 买入时，停止单成交的最优价格不能低于当前K线开盘价
        if direction == DIRECTION_LONG:
            tradePrice = max(self.bar.open, price)
        # 卖出时，停止单成交的最优价格不能高于当前K线开盘价
        else:
            tradePrice = min(self.bar.open, price)

        return tradePrice


########################################################################
class TurtlePortfolio(object):
    """海龟组合"""

    # ----------------------------------------------------------------------
    def __init__(self, engine):
        """Constructor"""
        self.engine = engine

        self.SignalDict = defaultdict(list)

        self.unitDict = {}  # 每个品种的持仓情况
        self.totalLong = 0  # 总的多头持仓
        self.totalShort = 0  # 总的空头持仓

        self.tradingDict = {}  # 交易中的信号字典

        self.sizeDict = {}  # 合约大小字典
        self.multiplierDict = {}  # 按照波动幅度计算的委托量单位字典
        self.posDict = {}  # 真实持仓量字典

        self.portfolioValue = 0  # 组合市值
        #Yifei
        self.portfolioAvailable = 0

    # ----------------------------------------------------------------------
    def init(self, portfolioValue, vtSymbolList, sizeDict):
        """"""
        self.portfolioValue = portfolioValue
        #Yifei
        self.portfolioAvailable = self.portfolioValue

        self.sizeDict = sizeDict

        for vtSymbol in vtSymbolList:
            Signal1 = TurtleSignal(self, vtSymbol, 20, 10, 20, True)
            Signal2 = TurtleSignal(self, vtSymbol, 55, 20, 20, False)

            l = self.SignalDict[vtSymbol]
            l.append(Signal1)
            l.append(Signal2)

            self.unitDict[vtSymbol] = 0
            self.posDict[vtSymbol] = 0

    # ----------------------------------------------------------------------
    def onBar(self, bar):
        """"""
        for Signal in self.SignalDict[bar.vtSymbol]:
            Signal.onBar(bar)
        #needs to be compitable with backtest mode
        if self.stateng is None:
            self.stateng = BacktestingEngine()

        self.stateng.currentDt = bar.dt

        previousResult = self.stateng.result

        self.stateng.result = DailyResult(dt)
        self.stateng.result.updatePos(self.posDict)
        self.stateng.resultList.append(self.stateng.result)

        if previousResult:
            self.stateng.result.updatePreviousClose(previousResult.closeDict)

        self.stateng.result.updateBar(bar)

    # ----------------------------------------------------------------------
    def newSignal(self, Signal, direction, offset, price, volume):
        """对交易信号进行过滤，符合条件的才发单执行"""
        unit = self.unitDict[Signal.vtSymbol]

        # 如果当前无仓位，则重新根据波动幅度计算委托量单位
        if not unit:
            size = self.sizeDict[Signal.vtSymbol]
            riskValue = self.portfolioValue * 0.01
            multiplier = riskValue / (Signal.atrVolatility * size)
            multiplier = int(round(multiplier, 0))
            self.multiplierDict[Signal.vtSymbol] = multiplier
        else:
            multiplier = self.multiplierDict[Signal.vtSymbol]

        # 开仓
        if offset == OFFSET_OPEN:
            # 检查上一次是否为盈利
            if Signal.profitCheck:
                pnl = Signal.getLastPnl()
                if pnl > 0:
                    return

            # 买入
            if direction == DIRECTION_LONG:
                # 组合持仓不能超过上限
                if self.totalLong >= MAX_DIRECTION_POS:
                    return

                # 单品种持仓不能超过上限
                if self.unitDict[Signal.vtSymbol] >= MAX_PRODUCT_POS:
                    return
            # 卖出
            else:
                if self.totalShort <= -MAX_DIRECTION_POS:
                    return

                if self.unitDict[Signal.vtSymbol] <= -MAX_PRODUCT_POS:
                    return
        # 平仓
        else:
            if direction == DIRECTION_LONG:
                # 必须有空头持仓
                if unit >= 0:
                    return

                # 平仓数量不能超过空头持仓
                volume = min(volume, abs(unit))
            else:
                if unit <= 0:
                    return

                volume = min(volume, abs(unit))

        # 获取当前交易中的信号，如果不是本信号，则忽略
        currentSignal = self.tradingDict.get(Signal.vtSymbol, None)
        if currentSignal and currentSignal is not Signal:
            return

        # 开仓则缓存该信号的交易状态
        if offset == OFFSET_OPEN:
            self.tradingDict[Signal.vtSymbol] = Signal
        # 平仓则清除该信号
        else:
            self.tradingDict.pop(Signal.vtSymbol)
    #     self.sendOrder(Signal.vtSymbol, direction, offset, price, volume, multiplier)
    #
    # # ----------------------------------------------------------------------
    # def sendOrder(self, vtSymbol, direction, offset, price, volume, multiplier):
        """"""
        # 计算合约持仓
        if direction == DIRECTION_LONG:
            self.unitDict[vtSymbol] += volume
            self.posDict[vtSymbol] += volume * multiplier
        else:
            self.unitDict[vtSymbol] -= volume
            self.posDict[vtSymbol] -= volume * multiplier

        # 计算总持仓
        self.totalLong = 0
        self.totalShort = 0

        for unit in self.unitDict.values():
            if unit > 0:
                self.totalLong += unit
            elif unit < 0:
                self.totalShort += unit

        # 向回测引擎中发单记录
        self.engine.sendOrder(vtSymbol, direction, offset, price, volume * multiplier)
