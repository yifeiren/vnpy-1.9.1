# encoding: UTF-8

from logging import INFO

import time
from datetime import datetime

from vnpy.trader.language import constant
from vnpy.trader.vtConstant import (EMPTY_FLOAT, EMPTY_INT, EMPTY_STRING, EMPTY_UNICODE)


########################################################################
class VtBaseData(object):
    """回调函数推送数据的基础类，其他数据类继承于此"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.gatewayName = EMPTY_STRING         # Gateway名称        
        self.rawData = None                     # 原始数据

 
########################################################################
class VtTickData(VtBaseData):
    """Tick行情数据类"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        super(VtTickData, self).__init__()
        
        # 代码相关
        self.symbol = EMPTY_STRING              # 合约代码
        self.exchange = EMPTY_STRING            # 交易所代码
        self.vtSymbol = EMPTY_STRING            # 合约在vt系统中的唯一代码，通常是 合约代码.交易所代码
        
        # 成交数据
        self.lastPrice = EMPTY_FLOAT            # 最新成交价
        self.lastVolume = EMPTY_INT             # 最新成交量
        self.volume = EMPTY_INT                 # 今天总成交量
        self.openInterest = EMPTY_INT           # 持仓量
        self.time = EMPTY_STRING                # 时间 11:20:56.5
        self.date = EMPTY_STRING                # 日期 20151009
        self.datetime = None                    # python的datetime时间对象
        
        # 常规行情
        self.openPrice = EMPTY_FLOAT            # 今日开盘价
        self.highPrice = EMPTY_FLOAT            # 今日最高价
        self.lowPrice = EMPTY_FLOAT             # 今日最低价
        self.preClosePrice = EMPTY_FLOAT
        
        self.upperLimit = EMPTY_FLOAT           # 涨停价
        self.lowerLimit = EMPTY_FLOAT           # 跌停价
        
        # 五档行情
        self.bidPrice1 = EMPTY_FLOAT
        self.bidPrice2 = EMPTY_FLOAT
        self.bidPrice3 = EMPTY_FLOAT
        self.bidPrice4 = EMPTY_FLOAT
        self.bidPrice5 = EMPTY_FLOAT
        
        self.askPrice1 = EMPTY_FLOAT
        self.askPrice2 = EMPTY_FLOAT
        self.askPrice3 = EMPTY_FLOAT
        self.askPrice4 = EMPTY_FLOAT
        self.askPrice5 = EMPTY_FLOAT        
        
        self.bidVolume1 = EMPTY_INT
        self.bidVolume2 = EMPTY_INT
        self.bidVolume3 = EMPTY_INT
        self.bidVolume4 = EMPTY_INT
        self.bidVolume5 = EMPTY_INT
        
        self.askVolume1 = EMPTY_INT
        self.askVolume2 = EMPTY_INT
        self.askVolume3 = EMPTY_INT
        self.askVolume4 = EMPTY_INT
        self.askVolume5 = EMPTY_INT

        #Okex
        self.limitHigh = EMPTY_STRING#(string):最高买入限制价格
        self.limitLow = EMPTY_STRING#(string):最低卖出限制价格
        self.vol= EMPTY_FLOAT#(double):24小时成交量
        self.sell=EMPTY_FLOAT#(double):卖一价格
        self.buy= EMPTY_FLOAT#(double): 买一价格
        self.unitAmount=EMPTY_FLOAT #(double):合约价值
        self.hold_amount=EMPTY_FLOAT#(double):当前持仓量
        self.contractId= EMPTY_INT#(long):合约ID
        self.high=EMPTY_FLOAT#:24小时最高价格
        self.low= EMPTY_FLOAT#:24 小时最低价格
        self.type = EMPTY_INT #1, THIS WEEK, 2 NEXT_WEEK, 3,QUARTER
        self.nextweekvsthisweek = EMPTY_FLOAT
        self.quartervsthisweek= EMPTY_FLOAT
        self.quartervsnextweek = EMPTY_FLOAT
        self.forecast = EMPTY_FLOAT
        self.futureindex = EMPTY_FLOAT
        self.thisweekvsspot = EMPTY_FLOAT

    #----------------------------------------------------------------------
    @staticmethod
    def createFromGateway(gateway, symbol, exchange,
                          lastPrice, lastVolume,
                          highPrice, lowPrice,
                          openPrice=EMPTY_FLOAT,
                          openInterest=EMPTY_INT,
                          upperLimit=EMPTY_FLOAT,
                          lowerLimit=EMPTY_FLOAT):
        tick = VtTickData()
        tick.gatewayName = gateway.gatewayName
        tick.symbol = symbol
        tick.exchange = exchange
        tick.vtSymbol = symbol + '.' + exchange
    
        tick.lastPrice = lastPrice
        tick.lastVolume = lastVolume
        tick.openInterest = openInterest
        tick.datetime = datetime.now()
        tick.date = tick.datetime.strftime('%Y%m%d')
        tick.time = tick.datetime.strftime('%H:%M:%S')
    
        tick.openPrice = openPrice
        tick.highPrice = highPrice
        tick.lowPrice = lowPrice
        tick.upperLimit = upperLimit
        tick.lowerLimit = lowerLimit
        return tick
    
    
########################################################################
class VtBarData(VtBaseData):
    """K线数据"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        super(VtBarData, self).__init__()
        
        self.vtSymbol = EMPTY_STRING        # vt系统代码
        self.symbol = EMPTY_STRING          # 代码
        self.exchange = EMPTY_STRING        # 交易所
    
        self.open = EMPTY_FLOAT             # OHLC
        self.high = EMPTY_FLOAT
        self.low = EMPTY_FLOAT
        self.close = EMPTY_FLOAT
        
        self.date = EMPTY_STRING            # bar开始的时间，日期
        self.time = EMPTY_STRING            # 时间
        self.datetime = None                # python的datetime时间对象
        
        self.volume = EMPTY_INT             # 成交量
        self.openInterest = EMPTY_INT       # 持仓量  
        self.interval = EMPTY_UNICODE       # K线周期
    
        self.openInterest = EMPTY_INT       # 持仓量    
        #Okex
        self.amount =EMPTY_FLOAT
        self.amount_cur  =EMPTY_FLOAT
        self.type = EMPTY_INT

########################################################################
class VtTradeData(VtBaseData):
    """
    成交数据类
    一般来说，一个VtOrderData可能对应多个VtTradeData：一个订单可能多次部分成交
    """

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        super(VtTradeData, self).__init__()
        
        # 代码编号相关
        self.symbol = EMPTY_STRING              # 合约代码
        self.exchange = EMPTY_STRING            # 交易所代码
        self.vtSymbol = EMPTY_STRING            # 合约在vt系统中的唯一代码，通常是 合约代码.交易所代码

        self.tradeID = EMPTY_STRING  # 成交编号 gateway内部自己生成的编号
        self.vtTradeID = EMPTY_STRING           # 成交在vt系统中的唯一编号，通常是 Gateway名.成交编号
        
        self.orderID = EMPTY_STRING             # 订单编号
        self.vtOrderID = EMPTY_STRING           # 订单在vt系统中的唯一编号，通常是 Gateway名.订单编号
        
        # 成交相关
        self.direction = EMPTY_UNICODE          # 成交方向
        self.offset = EMPTY_UNICODE             # 成交开平仓
        self.price = EMPTY_FLOAT                # 成交价格
        self.volume = EMPTY_INT                 # 成交数量
        self.tradeTime = EMPTY_STRING           # 成交时间

    #----------------------------------------------------------------------
    @staticmethod
    def createFromGateway(gateway, symbol, exchange, tradeID, orderID, direction, tradePrice, tradeVolume):
        trade = VtTradeData()
        trade.gatewayName = gateway.gatewayName
        trade.symbol = symbol
        trade.exchange = exchange
        trade.vtSymbol = symbol + '.' + exchange

        trade.orderID = orderID
        trade.vtOrderID = trade.gatewayName + '.' + trade.tradeID
        
        trade.tradeID = tradeID
        trade.vtTradeID = trade.gatewayName + '.' + tradeID
        
        trade.direction = direction
        trade.price = tradePrice
        trade.volume = tradeVolume
        trade.tradeTime = datetime.now().strftime('%H:%M:%S')
        return trade
    
    #----------------------------------------------------------------------
    @staticmethod
    def createFromOrderData(order,
                            tradeID,
                            tradePrice,
                            tradeVolume):  # type: (VtOrderData, str, float, float)->VtTradeData
        trade = VtTradeData()
        trade.gatewayName = order.gatewayName
        trade.symbol = order.symbol
        trade.vtSymbol = order.vtSymbol
        
        trade.orderID = order.orderID
        trade.vtOrderID = order.vtOrderID
        trade.tradeID = tradeID
        trade.vtTradeID = trade.gatewayName + '.' + tradeID
        trade.direction = order.direction
        trade.price = tradePrice
        trade.volume = tradeVolume
        trade.tradeTime = datetime.now().strftime('%H:%M:%S')
        return trade
    

########################################################################
class VtOrderData(VtBaseData):
    """订单数据类"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        super(VtOrderData, self).__init__()
        
        # 代码编号相关
        self.symbol = EMPTY_STRING              # 合约代码
        self.exchange = EMPTY_STRING            # 交易所代码
        self.vtSymbol = EMPTY_STRING  # 索引，统一格式：f"{symbol}.{exchange}"
        
        self.orderID = EMPTY_STRING             # 订单编号 gateway内部自己生成的编号
        self.vtOrderID = EMPTY_STRING  # 索引，统一格式：f"{gatewayName}.{orderId}"
        
        # 报单相关
        self.direction = EMPTY_UNICODE          # 报单方向
        self.offset = EMPTY_UNICODE             # 报单开平仓
        self.price = EMPTY_FLOAT                # 报单价格
        self.totalVolume = EMPTY_INT            # 报单总数量
        self.tradedVolume = EMPTY_INT           # 报单成交数量
        self.status = EMPTY_UNICODE             # 报单状态
        
        self.orderTime = EMPTY_STRING           # 发单时间
        self.cancelTime = EMPTY_STRING          # 撤单时间
        
        # CTP/LTS相关
        self.frontID = EMPTY_INT                # 前置机编号
        self.sessionID = EMPTY_INT              # 连接编号
#okex
        self.amount = EMPTY_FLOAT #    amount(double): 委托数量
        self.contract_name = EMPTY_STRING#    contract_name(string): 合约名称
        self.create_date = EMPTY_FLOAT#     created_date(long): 委托时间
        self.create_date_str = EMPTY_STRING#    create_date_str(string):委托时间字符串
        self.deal_amount = EMPTY_FLOAT #    deal_amount(double): 成交数量
        self.fee = EMPTY_FLOAT#    fee(double): 手续费
        #order_id(long): 订单ID
        #price(double): 订单价格
        self.price_avg =  EMPTY_FLOAT# price_avg(double): 平均价格
        self.type = EMPTY_INT    # 订单类 1：开多2：开空 3：平多 4：平空
        #
        #status(int): 订单状态(0 等待成交 1 部分成交 2 全部成交 - 1 撤单 4 撤单处理中)
        #symbol(string): btc_usd   ltc_usd   eth_usd   etc_usd   bch_usd
        self.unit_amount = EMPTY_FLOAT #(double):合约面值
        self.lever_rate = EMPTY_FLOAT #(double):杠杆倍数
        #self.value = EMPTY_INT#:10 / 20 默认10
        self.system_type = EMPTY_INT#(int):订单类型0:普通1:交割2:强平4:全平5:系统反单
    #----------------------------------------------------------------------
    @staticmethod
    def createFromGateway(gateway,                          # type: VtGateway
                          orderId,                          # type: str
                          symbol,                           # type: str
                          exchange,                         # type: str
                          price,                            # type: float
                          volume,                           # type: int
                          direction,                        # type: str
                          offset=EMPTY_UNICODE,             # type: str
                          tradedVolume=EMPTY_INT,           # type: int
                          status=constant.STATUS_UNKNOWN,   # type: str
                          orderTime=EMPTY_UNICODE,          # type: str
                          cancelTime=EMPTY_UNICODE,         # type: str
                          ):                                # type: (...)->VtOrderData
        vtOrder = VtOrderData()
        vtOrder.gatewayName = gateway.gatewayName
        vtOrder.symbol = symbol
        vtOrder.exchange = exchange
        vtOrder.vtSymbol = symbol + '.' + exchange
        vtOrder.orderID = orderId
        vtOrder.vtOrderID = gateway.gatewayName + '.' + orderId

        vtOrder.direction = direction
        vtOrder.offset = offset
        vtOrder.price = price
        vtOrder.totalVolume = volume
        vtOrder.tradedVolume = tradedVolume
        vtOrder.status = status
        vtOrder.orderTime = orderTime
        vtOrder.cancelTime = cancelTime
        return vtOrder
    
    
########################################################################
class VtPositionData(VtBaseData):
    """持仓数据类"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        super(VtPositionData, self).__init__()
        
        # 代码编号相关
        self.symbol = EMPTY_STRING              # 合约代码
        self.exchange = EMPTY_STRING            # 交易所代码
        self.vtSymbol = EMPTY_STRING            # 合约在vt系统中的唯一代码，合约代码.交易所代码  
        
        # 持仓相关
        self.direction = EMPTY_STRING           # 持仓方向
        self.position = EMPTY_INT               # 持仓量
        self.frozen = EMPTY_INT                 # 冻结数量
        self.price = EMPTY_FLOAT                # 持仓均价
        self.vtPositionName = EMPTY_STRING      # 持仓在vt系统中的唯一代码，通常是vtSymbol.方向
        self.ydPosition = EMPTY_INT             # 昨持仓
        self.positionProfit = EMPTY_FLOAT       # 持仓盈亏

        #Okex
        #position(string): 仓位 1 多仓 2 空仓
        self.contract_name = EMPTY_STRING # (string): 合约名称
        self.costprice = EMPTY_STRING # (string): 开仓价格
        self.bondfreez = EMPTY_STRING # (string): 当前合约冻结保证金
        self.avgprice = EMPTY_STRING # (string): 开仓均价
        self.contract_id = EMPTY_FLOAT # (long): 合约id
        self.position_id = EMPTY_FLOAT #(long): 仓位id
        self.hold_amount = EMPTY_STRING # (string): 持仓量
        self.eveningup = EMPTY_STRING # (string): 可平仓量
        self.levetype = EMPTY_INT  # 0 全仓 1 逐仓
        #Okex 全仓
        self.margin = EMPTY_FLOAT #: 固定保证金
        self.realized = EMPTY_FLOAT #:已实现盈亏

        #Okex 逐仓
        self.balance = EMPTY_STRING #(string): 合约账户余额

        self.forcedprice = EMPTY_STRING #(string): 强平价格
        self.profitreal = EMPTY_STRING #(string): 已实现盈亏
        self.fixmargin = EMPTY_FLOAT #(double): 固定保证金
        self.lever_rate = EMPTY_FLOAT #(double): 杠杆倍数
    #----------------------------------------------------------------------
    @staticmethod
    def createFromGateway(gateway,                      # type: VtGateway
                          exchange,                     # type: str
                          symbol,                       # type: str
                          direction,                    # type: str
                          position,                     # type: int
                          frozen=EMPTY_INT,             # type: int
                          price=EMPTY_FLOAT,            # type: float
                          yestordayPosition=EMPTY_INT,  # type: int
                          profit=EMPTY_FLOAT            # type: float
                          ):                            # type: (...)->VtPositionData
        vtPosition = VtPositionData()
        vtPosition.gatewayName = gateway.gatewayName
        vtPosition.symbol = symbol
        vtPosition.exchange = exchange
        vtPosition.vtSymbol = symbol + '.' + exchange
    
        vtPosition.direction = direction
        vtPosition.position = position
        vtPosition.frozen = frozen
        vtPosition.price = price
        vtPosition.vtPositionName = vtPosition.vtSymbol + '.' + direction
        vtPosition.ydPosition = yestordayPosition
        vtPosition.positionProfit = profit
        return vtPosition


########################################################################
class VtAccountData(VtBaseData):
    """账户数据类"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        super(VtAccountData, self).__init__()
        
        # 账号代码相关
        self.accountID = EMPTY_STRING           # 账户代码
        self.vtAccountID = EMPTY_STRING         # 账户在vt中的唯一代码，通常是 Gateway名.账户代码
        
        # 数值相关
        self.preBalance = EMPTY_FLOAT           # 昨日账户结算净值
        self.balance = EMPTY_FLOAT              # 账户净值
        self.available = EMPTY_FLOAT            # 可用资金
        self.commission = EMPTY_FLOAT           # 今日手续费
        self.margin = EMPTY_FLOAT               # 保证金占用
        self.closeProfit = EMPTY_FLOAT          # 平仓盈亏
        self.positionProfit = EMPTY_FLOAT       # 持仓盈亏

        #
        #balance(double): 账户余额
        self.symbol = EMPTY_STRING #(string)：币种
        self.keep_deposit = EMPTY_FLOAT #(double)：保证金
        self.profit_real= EMPTY_FLOAT #(double)：已实现盈亏
        self.unit_amount = EMPTY_INT #(int)：合约价值
        #balance.available
        self.bond = EMPTY_FLOAT
        self.contract_id = EMPTY_INT
        self.freeze = EMPTY_FLOAT
        self.long_order_amount = EMPTY_FLOAT
        self.pre_long_order_amount = EMPTY_FLOAT
        self.profit = EMPTY_FLOAT
        self.short_order_amount = EMPTY_FLOAT
        self.pre_short_order_amount = EMPTY_FLOAT

        

########################################################################
class VtErrorData(VtBaseData):
    """错误数据类"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        super(VtErrorData, self).__init__()
        
        self.errorID = EMPTY_STRING             # 错误代码
        self.errorMsg = EMPTY_UNICODE           # 错误信息
        self.additionalInfo = EMPTY_UNICODE     # 补充信息
        
        self.errorTime = time.strftime('%X', time.localtime())    # 错误生成时间


########################################################################
class VtLogData(VtBaseData):
    """日志数据类"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        super(VtLogData, self).__init__()
        
        self.logTime = time.strftime('%X', time.localtime())    # 日志生成时间
        self.logContent = EMPTY_UNICODE                         # 日志信息
        self.logLevel = INFO                                    # 日志级别


########################################################################
class VtContractData(VtBaseData):
    """合约详细信息类"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        super(VtContractData, self).__init__()
        
        self.symbol = EMPTY_STRING              # 代码
        self.exchange = EMPTY_STRING            # 交易所代码
        self.vtSymbol = EMPTY_STRING            # 合约在vt系统中的唯一代码，通常是 合约代码.交易所代码
        self.name = EMPTY_UNICODE               # 合约中文名
        
        self.productClass = EMPTY_UNICODE       # 合约类型
        self.size = EMPTY_INT                   # 合约大小
        self.priceTick = EMPTY_FLOAT            # 合约最小价格TICK
        
        # 期权相关
        self.strikePrice = EMPTY_FLOAT          # 期权行权价
        self.underlyingSymbol = EMPTY_STRING    # 标的物合约代码
        self.optionType = EMPTY_UNICODE         # 期权类型
        self.expiryDate = EMPTY_STRING          # 到期日
        
    #----------------------------------------------------------------------
    @staticmethod
    def createFromGateway(gateway,
                          exchange,
                          symbol,
                          productClass,
                          size,
                          priceTick,
                          name=None,
                          strikePrice=EMPTY_FLOAT,
                          underlyingSymbol=EMPTY_STRING,
                          optionType=EMPTY_UNICODE,
                          expiryDate=EMPTY_STRING
                          ):
        d = VtContractData()
        d.gatewayName = gateway.gatewayName
        d.symbol = symbol
        d.exchange = exchange
        d.vtSymbol = symbol + '.' + exchange
        d.productClass = productClass
        d.size = size
        d.priceTick = priceTick
        if name is None:
            d.name = d.symbol
        d.strikePrice = strikePrice
        d.underlyingSymbol = underlyingSymbol
        d.optionType = optionType
        d.expiryDate = expiryDate
        return d
            

########################################################################
class VtHistoryData(object):
    """K线时间序列数据"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.vtSymbol = EMPTY_STRING    # vt系统代码
        self.symbol = EMPTY_STRING      # 代码
        self.exchange = EMPTY_STRING    # 交易所
        
        self.interval = EMPTY_UNICODE   # K线时间周期
        self.queryID = EMPTY_STRING     # 查询号
        self.barList = []               # VtBarData列表
    

########################################################################
class VtSubscribeReq(object):
    """订阅行情时传入的对象类"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.symbol = EMPTY_STRING              # 代码
        self.exchange = EMPTY_STRING            # 交易所
        
        # 以下为IB相关
        self.productClass = EMPTY_UNICODE       # 合约类型
        self.currency = EMPTY_STRING            # 合约货币
        self.expiry = EMPTY_STRING              # 到期日
        self.strikePrice = EMPTY_FLOAT          # 行权价
        self.optionType = EMPTY_UNICODE         # 期权类型


########################################################################
class VtOrderReq(object):
    """发单时传入的对象类"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.symbol = EMPTY_STRING              # 代码
        self.exchange = EMPTY_STRING            # 交易所
        self.vtSymbol = EMPTY_STRING            # VT合约代码
        self.price = EMPTY_FLOAT                # 价格
        self.volume = EMPTY_INT                 # 数量
    
        self.priceType = EMPTY_STRING           # 价格类型
        self.direction = EMPTY_STRING           # 买卖
        self.offset = EMPTY_STRING              # 开平
        
        # 以下为IB相关
        self.productClass = EMPTY_UNICODE       # 合约类型
        self.currency = EMPTY_STRING            # 合约货币
        self.expiry = EMPTY_STRING              # 到期日
        self.strikePrice = EMPTY_FLOAT          # 行权价
        self.optionType = EMPTY_UNICODE         # 期权类型     
        self.lastTradeDateOrContractMonth = EMPTY_STRING   # 合约月,IB专用
        self.multiplier = EMPTY_STRING                     # 乘数,IB专用

        # Okex FUTURE
        self.contracttype = EMPTY_STRING
        self.type = EMPTY_INT
        self.matchprice = EMPTY_STRING
        self.leverrate = EMPTY_STRING

########################################################################
class VtCancelOrderReq(object):
    """撤单时传入的对象类"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.symbol = EMPTY_STRING              # 代码
        self.exchange = EMPTY_STRING            # 交易所
        self.vtSymbol = EMPTY_STRING            # VT合约代码
        
        # 以下字段主要和CTP、LTS类接口相关
        self.orderID = EMPTY_STRING             # 报单号
        self.frontID = EMPTY_STRING             # 前置机号
        self.sessionID = EMPTY_STRING           # 会话号

        # Okex Future
        self.contracttype = EMPTY_STRING

########################################################################
class VtHistoryReq(object):
    """查询历史数据时传入的对象类"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.symbol = EMPTY_STRING              # 代码
        self.exchange = EMPTY_STRING            # 交易所
        self.vtSymbol = EMPTY_STRING            # VT合约代码
        
        self.interval = EMPTY_UNICODE           # K线周期
        self.start = None                       # 起始时间datetime对象
        self.end = None                         # 结束时间datetime对象
    

########################################################################
class VtSingleton(type):
    """
    单例，应用方式:静态变量 __metaclass__ = Singleton
    """
    
    _instances = {}

    #----------------------------------------------------------------------
    def __call__(cls, *args, **kwargs):
        """调用"""
        if cls not in cls._instances:
            cls._instances[cls] = super(VtSingleton, cls).__call__(*args, **kwargs)
            
        return cls._instances[cls]
