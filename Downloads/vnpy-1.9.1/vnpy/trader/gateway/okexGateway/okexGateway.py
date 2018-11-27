# encoding: UTF-8

'''
vnpy.api.okex的gateway接入

Contributor：ipqhjjybj 大佳
'''
from __future__ import print_function


import os
import json
from datetime import datetime
from time import sleep
from copy import copy
from threading import Condition
from queue import Queue, Empty
from threading import Thread
from time import sleep

from vnpy.api.okex import OkexSpotApi, OkexFuturesApi, OKEX_SPOT_HOST, OKEX_USD_CONTRACT
from vnpy.trader.vtGateway import *
from vnpy.trader.vtFunction import getJsonPath
#import datetime
import zlib

# 价格类型映射
# 买卖类型： 限价单（buy/sell） 市价单（buy_market/sell_market）
priceTypeMap = {}
priceTypeMap['buy'] = (DIRECTION_LONG, PRICETYPE_LIMITPRICE)
priceTypeMap['buy_market'] = (DIRECTION_LONG, PRICETYPE_MARKETPRICE)
priceTypeMap['sell'] = (DIRECTION_SHORT, PRICETYPE_LIMITPRICE)
priceTypeMap['sell_market'] = (DIRECTION_SHORT, PRICETYPE_MARKETPRICE)
priceTypeMapReverse = {v: k for k, v in priceTypeMap.items()} 

# 委托状态印射
statusMap = {}
statusMap[-1] = STATUS_CANCELLED
statusMap[0] = STATUS_NOTTRADED
statusMap[1] = STATUS_PARTTRADED
statusMap[2] = STATUS_ALLTRADED
statusMap[4] = STATUS_UNKNOWN

okex_all_symbol_pairs = ['eth_btc','hpb_eth','ada_eth']
okex_all_future_symbol = ['eos']

#okex_all_symbol_pairs = ['hpb_btc','hpb_eth','hpb_usdt','eth_btc','eth_usdt','btc_usdt','gnx_eth','gnx_btc','gnx_usdt','ltc_eth','ltc_btc','ltc_usdt','eos_eth','eos_btc','eos_usdt']

#okex_all_symbol_pairs = ['ref_usdt', 'soc_usdt', 'light_usdt', 'avt_usdt', 'of_usdt', 'brd_usdt', 'ast_usdt', 'int_usdt', 'zrx_usdt', 'ctr_usdt', 'dgd_usdt', 'aidoc_usdt', 'wtc_usdt', 'swftc_usdt', 'wrc_usdt', 'sub_usdt', 'dna_usdt', 'knc_usdt', 'kcash_usdt', 'mdt_usdt', 'theta_usdt', 'ppt_usdt', 'utk_usdt', 'qvt_usdt', 'salt_usdt', 'la_usdt', 'itc_usdt', 'fair_usdt', 'yee_usdt', '1st_usdt', 'fun_usdt', 'iost_usdt', 'mkr_usdt', 'tio_usdt', 'req_usdt', 'ubtc_usdt', 'icx_usdt', 'tct_usdt', 'san_usdt', 'lrc_usdt', 'icn_usdt', 'cvc_usdt', 'eth_usdt', 'poe_usdt', 'xlm_usdt', 'iota_usdt', 'eos_usdt', 'nuls_usdt', 'mot_usdt', 'neo_usdt', 'gnx_usdt', 'dgb_usdt', 'evx_usdt', 'ltc_usdt', 'mda_usdt', 'etc_usdt', 'dpy_usdt', 'tnb_usdt', 'nas_usdt', 'btc_usdt', 'smt_usdt', 'ssc_usdt', 'oax_usdt', 'yoyo_usdt', 'snc_usdt', 'sngls_usdt', 'bch_usdt', 'mana_usdt', 'mof_usdt', 'mco_usdt', 'vib_usdt', 'topc_usdt', 'pra_usdt', 'bnt_usdt', 'xmr_usdt', 'edo_usdt', 'snt_usdt', 'eng_usdt', 'stc_usdt', 'qtum_usdt', 'key_usdt', 'ins_usdt', 'rnt_usdt', 'bcd_usdt', 'amm_usdt', 'lend_usdt', 'btm_usdt', 'elf_usdt', 'xuc_usdt', 'cag_usdt', 'snm_usdt', 'act_usdt', 'dash_usdt', 'zec_usdt', 'storj_usdt', 'pay_usdt', 'vee_usdt', 'show_usdt', 'trx_usdt', 'atl_usdt', 'ark_usdt', 'ost_usdt', 'gnt_usdt', 'dat_usdt', 'rcn_usdt', 'qun_usdt', 'mth_usdt', 'rct_usdt', 'read_usdt', 'gas_usdt', 'btg_usdt', 'mtl_usdt', 'cmt_usdt', 'xrp_usdt', 'spf_usdt', 'aac_usdt', 'can_usdt', 'omg_usdt', 'hsr_usdt', 'link_usdt', 'dnt_usdt', 'true_usdt', 'ukg_usdt', 'xem_usdt', 'ngc_usdt', 'lev_usdt', 'rdn_usdt', 'ace_usdt', 'ipc_usdt', 'ugc_usdt', 'viu_usdt', 'mag_usdt', 'hot_usdt', 'pst_usdt','ref_btc', 'soc_btc', 'light_btc', 'avt_btc', 'of_btc', 'brd_btc', 'ast_btc', 'int_btc', 'zrx_btc', 'ctr_btc', 'dgd_btc', 'aidoc_btc', 'wtc_btc', 'swftc_btc', 'wrc_btc', 'sub_btc', 'dna_btc', 'knc_btc', 'kcash_btc', 'mdt_btc', 'theta_btc', 'ppt_btc', 'utk_btc', 'qvt_btc', 'salt_btc', 'la_btc', 'itc_btc', 'fair_btc', 'yee_btc', '1st_btc', 'fun_btc', 'iost_btc', 'mkr_btc', 'tio_btc', 'req_btc', 'ubtc_btc', 'icx_btc', 'tct_btc', 'san_btc', 'lrc_btc', 'icn_btc', 'cvc_btc', 'eth_btc', 'poe_btc', 'xlm_btc', 'iota_btc', 'eos_btc', 'nuls_btc', 'mot_btc', 'neo_btc', 'gnx_btc', 'dgb_btc', 'evx_btc', 'ltc_btc', 'mda_btc', 'etc_btc', 'dpy_btc', 'tnb_btc', 'nas_btc', 'btc_btc', 'smt_btc', 'ssc_btc', 'oax_btc', 'yoyo_btc', 'snc_btc', 'sngls_btc', 'bch_btc', 'mana_btc', 'mof_btc', 'mco_btc', 'vib_btc', 'topc_btc', 'pra_btc', 'bnt_btc', 'xmr_btc', 'edo_btc', 'snt_btc', 'eng_btc', 'stc_btc', 'qtum_btc', 'key_btc', 'ins_btc', 'rnt_btc', 'bcd_btc', 'amm_btc', 'lend_btc', 'btm_btc', 'elf_btc', 'xuc_btc', 'cag_btc', 'snm_btc', 'act_btc', 'dash_btc', 'zec_btc', 'storj_btc', 'pay_btc', 'vee_btc', 'show_btc', 'trx_btc', 'atl_btc', 'ark_btc', 'ost_btc', 'gnt_btc', 'dat_btc', 'rcn_btc', 'qun_btc', 'mth_btc', 'rct_btc', 'read_btc', 'gas_btc', 'btg_btc', 'mtl_btc', 'cmt_btc', 'xrp_btc', 'spf_btc', 'aac_btc', 'can_btc', 'omg_btc', 'hsr_btc', 'link_btc', 'dnt_btc', 'true_btc', 'ukg_btc', 'xem_btc', 'ngc_btc', 'lev_btc', 'rdn_btc', 'ace_btc', 'ipc_btc', 'ugc_btc', 'viu_btc', 'mag_btc', 'hot_btc', 'pst_btc','eos_eth','eth_usdt','gnx_eth','hpb_btc','hpb_eth','hpb_usdt','ltc_eth','okb_btc','okb_eth','okb_usdt','hsr_eth','xrp_eth','xrp_btc','bch_eth','bch_usdt']

okex_all_symbol = ['btc','eth','eos','gnx','hpb','ltc','okb','hsr','xrp','bch','ada']

########################################################################
class OkexGateway(VtGateway):
    """OKEX交易接口"""
    
    #----------------------------------------------------------------------
    def __init__(self, eventEngine, gatewayName='OKEX'):
        """Constructor"""
        super(OkexGateway, self).__init__(eventEngine, gatewayName)
        
        
        # self.api_contract = Api_contract(self)
        
        self.leverage = 0
        self.connected = False
        
        self.fileName = self.gatewayName + '_connect.json'
        self.filePath = getJsonPath(self.fileName, __file__)     

    #----------------------------------------------------------------------
    def connect(self):
        """连接"""
        # 载入json文件
        try:
            f = open(self.filePath)
        except IOError:
            log = VtLogData()
            log.gatewayName = self.gatewayName
            log.logContent = u'读取连接配置出错，请检查'
            self.onLog(log)
            return
        
        # 解析json文件
        setting = json.load(f)
        f.close()
        try:
            apiKey = str(setting['apiKey'])
            secretKey = str(setting['secretKey'])
            trace = setting['trace']
            symbols = setting['symbols']
        except KeyError:
            log = VtLogData()
            log.gatewayName = self.gatewayName
            log.logContent = u'连接配置缺少字段，请检查'
            self.onLog(log)
            return            
        
        # 初始化接口
        #spot
        #self.spotApi = SpotApi(self)
        #self.spotApi.init(apiKey, secretKey, trace, symbols)
        #future
        self.spotApi = FutureApi(self,apiKey,secretKey)
        self.spotApi.connect(OKEX_USD_CONTRACT,apiKey,secretKey)

    #----------------------------------------------------------------------
    def subscribe(self, subscribeReq):
        """订阅行情"""
        pass
        
    #----------------------------------------------------------------------
    def sendOrder(self, orderReq):
        """发单"""
        return self.spotApi.sendOrder(orderReq)

    #----------------------------------------------------------------------
    def cancelOrder(self, cancelOrderReq):
        """撤单"""
        self.spotApi.cancelOrder(cancelOrderReq)
        
    #----------------------------------------------------------------------
    def qryAccount(self):
        """查询账户资金"""
        pass

    #----------------------------------------------------------------------
    def qryPosition(self):
        """查询持仓"""
        self.spotApi.spotUserInfo()
        
    #----------------------------------------------------------------------
    def close(self):
        """关闭"""
        self.spotApi.close()
        
    #----------------------------------------------------------------------
    def initQuery(self):
        """初始化连续查询"""
        if self.qryEnabled:
            # 需要循环的查询函数列表
            self.qryFunctionList = [self.qryPosition]
            
            self.qryCount = 0           # 查询触发倒计时
            self.qryTrigger = 2         # 查询触发点
            self.qryNextFunction = 0    # 上次运行的查询函数索引
            
            self.startQuery()  
    
    #----------------------------------------------------------------------
    def query(self, event):
        """注册到事件处理引擎上的查询函数"""
        self.qryCount += 1
        
        if self.qryCount > self.qryTrigger:
            # 清空倒计时
            self.qryCount = 0
            
            # 执行查询函数
            function = self.qryFunctionList[self.qryNextFunction]
            function()
            
            # 计算下次查询函数的索引，如果超过了列表长度，则重新设为0
            self.qryNextFunction += 1
            if self.qryNextFunction == len(self.qryFunctionList):
                self.qryNextFunction = 0
                
    #----------------------------------------------------------------------
    def startQuery(self):
        """启动连续查询"""
        self.eventEngine.register(EVENT_TIMER, self.query)
    
    #----------------------------------------------------------------------
    def setQryEnabled(self, qryEnabled):
        """设置是否要启动循环查询"""
        self.qryEnabled = qryEnabled


########################################################################
class SpotApi(OkexSpotApi):
    """OKEX的API实现"""

    #----------------------------------------------------------------------
    def __init__(self, gateway):
        """Constructor"""
        super(SpotApi, self).__init__()
        
        self.gateway = gateway                  # gateway对象
        self.gatewayName = gateway.gatewayName  # gateway对象名称

        self.cbDict = {}
        self.tickDict = {}
        self.orderDict = {}

        self.channelSymbolMap = {}
        
        self.localNo = 0                # 本地委托号
        self.localNoQueue = Queue()     # 未收到系统委托号的本地委托号队列
        self.localNoDict = {}           # key为本地委托号，value为系统委托号
        self.localOrderDict = {}        # key为本地委托号, value为委托对象
        self.orderIdDict = {}           # key为系统委托号，value为本地委托号
        self.cancelDict = {}            # key为本地委托号，value为撤单请求

        self.recordOrderId_BefVolume = {}       # 记录的之前处理的量

        self.cache_some_order = {}
        self.tradeID = 0

        self.registerSymbolPairArray = set([])

    #----------------------------------------------------------------------
    def onMessage(self, data):
        """信息推送""" 
        print(data)
        channel = data.get('channel', '')
        if not channel:
            return

        if channel in self.cbDict:
            callback = self.cbDict[channel]
            callback(data)

    #----------------------------------------------------------------------
    def onError(self, data):
        """错误推送"""
        error = VtErrorData()
        error.gatewayName = self.gatewayName
        error.errorMsg = str(data)
        self.gateway.onError(error)
        
    #----------------------------------------------------------------------
    def onClose(self):
        """接口断开"""
        self.gateway.connected = False
        self.writeLog(u'服务器连接断开')
    
    #----------------------------------------------------------------------
    def onOpen(self):       
        """连接成功"""
        self.gateway.connected = True
        self.writeLog(u'服务器连接成功')
        
        self.login()
        
        # 推送合约数据
        for symbol in self.symbols:
            contract = VtContractData()
            contract.gatewayName = self.gatewayName
            contract.symbol = symbol
            contract.exchange = EXCHANGE_OKEX
            contract.vtSymbol = '.'.join([contract.symbol, contract.exchange])
            contract.name = symbol
            contract.size = 0.00001
            contract.priceTick = 0.00001
            contract.productClass = PRODUCT_SPOT
            self.gateway.onContract(contract)
    
    #----------------------------------------------------------------------
    def initCallback(self):
        """初始化回调函数"""
        for symbol in self.symbols:
            # channel和symbol映射
            self.channelSymbolMap["ok_sub_spot_%s_ticker" % symbol] = symbol
            self.channelSymbolMap["ok_sub_spot_%s_depth_5" % symbol] = symbol
            
            # channel和callback映射
            self.cbDict["ok_sub_spot_%s_ticker" % symbol] = self.onTicker
            self.cbDict["ok_sub_spot_%s_depth_5" % symbol] = self.onDepth
            self.cbDict["ok_sub_spot_%s_order" % symbol] = self.onSubSpotOrder
            self.cbDict["ok_sub_spot_%s_balance" % symbol] = self.onSubSpotBalance

        self.cbDict['ok_spot_userinfo'] = self.onSpotUserInfo
        self.cbDict['ok_spot_orderinfo'] = self.onSpotOrderInfo
        self.cbDict['ok_spot_order'] = self.onSpotOrder
        self.cbDict['ok_spot_cancel_order'] = self.onSpotCancelOrder
        self.cbDict['login'] = self.onLogin
    
    #----------------------------------------------------------------------
    def onLogin(self, data):
        """"""
        self.writeLog(u'服务器登录成功')
        
        # 查询持仓
        self.spotUserInfo()
        
        # 订阅推送
        for symbol in self.symbols:
            self.subscribe(symbol)
        
    #----------------------------------------------------------------------
    def onTicker(self, data):
        """"""
        channel = data['channel']
        symbol = self.channelSymbolMap[channel]
        
        if symbol not in self.tickDict:
            tick = VtTickData()
            tick.symbol = symbol
            tick.exchange = EXCHANGE_OKEX
            tick.vtSymbol = '.'.join([tick.symbol, tick.exchange])
            tick.gatewayName = self.gatewayName
            
            self.tickDict[symbol] = tick
        else:
            tick = self.tickDict[symbol]
        
        d = data['data']
        tick.highPrice = float(d['high'])
        tick.lowPrice = float(d['low'])
        tick.lastPrice = float(d['last'])
        tick.volume = float(d['vol'].replace(',', ''))
        tick.date, tick.time = self.generateDateTime(d['timestamp'])
        
        if tick.bidPrice1:
            newtick = copy(tick)
            self.gateway.onTick(newtick)
    
    #----------------------------------------------------------------------
    def onDepth(self, data):
        """"""
        channel = data['channel']
        symbol = self.channelSymbolMap[channel]

        if symbol not in self.tickDict:
            tick = VtTickData()
            tick.symbol = symbol
            tick.exchange = EXCHANGE_OKEX
            tick.vtSymbol = '.'.join([tick.symbol, tick.exchange])
            tick.gatewayName = self.gatewayName

            self.tickDict[symbol] = tick
        else:
            tick = self.tickDict[symbol]
        
        d = data['data']
        
        tick.bidPrice1, tick.bidVolume1 = d['bids'][0]
        tick.bidPrice2, tick.bidVolume2 = d['bids'][1]
        tick.bidPrice3, tick.bidVolume3 = d['bids'][2]
        tick.bidPrice4, tick.bidVolume4 = d['bids'][3]
        tick.bidPrice5, tick.bidVolume5 = d['bids'][4]
        
        tick.askPrice1, tick.askVolume1 = d['asks'][-1]
        tick.askPrice2, tick.askVolume2 = d['asks'][-2]
        tick.askPrice3, tick.askVolume3 = d['asks'][-3]
        tick.askPrice4, tick.askVolume4 = d['asks'][-4]
        tick.askPrice5, tick.askVolume5 = d['asks'][-5]     
        
        tick.bidPrice1 = float(tick.bidPrice1)
        tick.bidPrice2 = float(tick.bidPrice2)
        tick.bidPrice3 = float(tick.bidPrice3)
        tick.bidPrice4 = float(tick.bidPrice4)
        tick.bidPrice5 = float(tick.bidPrice5)
        tick.askPrice1 = float(tick.askPrice1)
        tick.askPrice2 = float(tick.askPrice2)
        tick.askPrice3 = float(tick.askPrice3)
        tick.askPrice4 = float(tick.askPrice4)
        tick.askPrice5 = float(tick.askPrice5)   
        
        tick.bidVolume1 = float(tick.bidVolume1)
        tick.bidVolume2 = float(tick.bidVolume2)
        tick.bidVolume3 = float(tick.bidVolume3)
        tick.bidVolume4 = float(tick.bidVolume4)
        tick.bidVolume5 = float(tick.bidVolume5)
        tick.askVolume1 = float(tick.askVolume1)
        tick.askVolume2 = float(tick.askVolume2)
        tick.askVolume3 = float(tick.askVolume3)
        tick.askVolume4 = float(tick.askVolume4)
        tick.askVolume5 = float(tick.askVolume5)          
        
        tick.date, tick.time = self.generateDateTime(d['timestamp'])
        
        if tick.lastPrice:
            newtick = copy(tick)
            self.gateway.onTick(newtick)
    
    #----------------------------------------------------------------------        
    def onSpotOrder(self, data):
        """"""
        # 如果委托失败，则通知委托被拒单的信息
        if self.checkDataError(data):
            try:
                localNo = self.localNoQueue.get_nowait()
            except Empty:
                return
            
            order = self.localOrderDict[localNo]
            order.status = STATUS_REJECTED
            self.gateway.onOrder(order)
    
    #----------------------------------------------------------------------
    def onSpotCancelOrder(self, data):
        """"""
        self.checkDataError(data)
        
    #----------------------------------------------------------------------
    def onSpotUserInfo(self, data):
        """现货账户资金推送"""
        if self.checkDataError(data):
            return
        
        funds = data['data']['info']['funds']
        free = funds['free']
        freezed = funds['freezed']
        
        # 持仓信息
        for symbol in free.keys():
            frozen = float(freezed[symbol])
            available = float(free[symbol])
            
            if frozen or available:
                account = VtAccountData()
                account.gatewayName = self.gatewayName
                
                account.accountID = symbol
                account.vtAccountID = '.'.join([account.gatewayName, account.accountID])
                account.balance = frozen + available
                account.available = available
                
                self.gateway.onAccount(account)                      
        
        self.writeLog(u'持仓信息查询成功')
        
        # 查询委托
        for symbol in self.symbols:
            self.spotOrderInfo(symbol, '-1')        
            
    #----------------------------------------------------------------------
    def onSpotOrderInfo(self, data):
        """委托信息查询回调"""
        if self.checkDataError(data):
            return
        
        rawData = data['data']
        
        for d in rawData['orders']:
            self.localNo += 1
            localNo = str(self.localNo)
            orderId = str(d['order_id'])
            
            self.localNoDict[localNo] = orderId
            self.orderIdDict[orderId] = localNo
            
            if orderId not in self.orderDict:
                order = VtOrderData()
                order.gatewayName = self.gatewayName
                
                order.symbol = d['symbol']
                order.exchange = EXCHANGE_OKEX
                order.vtSymbol = '.'.join([order.symbol, order.exchange])
    
                order.orderID = localNo
                order.vtOrderID = '.'.join([self.gatewayName, order.orderID])
                
                order.price = d['price']
                order.totalVolume = d['amount']
                order.direction, priceType = priceTypeMap[d['type']]
                date, order.orderTime = self.generateDateTime(d['create_date'])
                
                self.orderDict[orderId] = order
            else:
                order = self.orderDict[orderId]
                
            order.tradedVolume = d['deal_amount']
            order.status = statusMap[d['status']]            
            
            self.gateway.onOrder(copy(order))

    #----------------------------------------------------------------------
    def onSubSpotOrder(self, data):
        """交易数据"""
        rawData = data["data"]
        orderId = str(rawData['orderId'])  
        
        # 获取本地委托号
        if orderId in self.orderIdDict:
            localNo = self.orderIdDict[orderId]
        else:
            try:
                localNo = self.localNoQueue.get_nowait()
            except Empty:
                self.localNo += 1
                localNo = str(self.localNo)
        
        self.localNoDict[localNo] = orderId
        self.orderIdDict[orderId] = localNo        

        # 获取委托对象
        if orderId in self.orderDict:
            order = self.orderDict[orderId]
        else:
            order = VtOrderData()
            order.gatewayName = self.gatewayName
            order.symbol = rawData['symbol']
            order.exchange = EXCHANGE_OKEX
            order.vtSymbol = '.'.join([order.symbol, order.exchange])
            order.orderID = localNo
            order.vtOrderID = '.'.join([self.gatewayName, localNo])
            order.direction, priceType = priceTypeMap[rawData['tradeType']]
            order.price = float(rawData['tradeUnitPrice'])
            order.totalVolume = float(rawData['tradeAmount'])
            date, order.orderTime = self.generateDateTime(rawData['createdDate'])
        
        lastTradedVolume = order.tradedVolume
        
        order.status = statusMap[rawData['status']]
        order.tradedVolume = float(rawData['completedTradeAmount'])
        self.gateway.onOrder(copy(order))
        
        # 成交信息
        if order.tradedVolume > lastTradedVolume:
            trade = VtTradeData()
            trade.gatewayName = self.gatewayName
    
            trade.symbol = order.symbol
            trade.exchange = order.exchange
            trade.vtSymbol = order.vtSymbol
            
            self.tradeID += 1
            trade.tradeID = str(self.tradeID)
            trade.vtTradeID = '.'.join([self.gatewayName, trade.tradeID])
            
            trade.orderID = order.orderID
            trade.vtOrderID = order.vtOrderID
            
            trade.direction = order.direction
            trade.price = float(rawData['averagePrice'])
            trade.volume = order.tradedVolume - lastTradedVolume
            
            trade.tradeTime = datetime.now().strftime('%H:%M:%S')
            self.gateway.onTrade(trade)
        
        # 撤单
        if localNo in self.cancelDict:
            req = self.cancelDict[localNo]
            self.spotCancel(req)
            del self.cancelDict[localNo]        

    #----------------------------------------------------------------------        
    def onSubSpotBalance(self, data):
        """"""
        rawData = data['data']
        free = rawData['info']['free']
        freezed = rawData['info']['freezed']
        
        for symbol in free.keys():            
            account = VtAccountData()
            account.gatewayName = self.gatewayName
            
            account.accountID = symbol
            account.vtAccountID = '.'.join([account.gatewayName, account.accountID])
            account.available = float(free[symbol])
            account.balance = account.available + float(freezed[symbol])
            
            self.gateway.onAccount(account)                   
    
    #----------------------------------------------------------------------
    def init(self, apiKey, secretKey, trace, symbols):
        """初始化接口"""
        self.symbols = symbols
        self.initCallback()
        self.connect(OKEX_SPOT_HOST, apiKey, secretKey, trace)
        self.writeLog(u'接口初始化成功')

    #----------------------------------------------------------------------
    def sendOrder(self, req):
        """发单"""
        type_ = priceTypeMapReverse[(req.direction, req.priceType)]
        result = self.spotOrder(req.symbol, type_, str(req.price), str(req.volume))
        
        # 若请求失败，则返回空字符串委托号
        if not result:
            return ''
        
        # 本地委托号加1，并将对应字符串保存到队列中，返回基于本地委托号的vtOrderID
        self.localNo += 1
        self.localNoQueue.put(str(self.localNo))
        vtOrderID = '.'.join([self.gatewayName, str(self.localNo)])
        
        # 缓存委托信息
        order = VtOrderData()
        order.gatewayName = self.gatewayName
        
        order.symbol = req.symbol
        order.exchange = EXCHANGE_OKEX
        order.vtSymbol = '.'.join([order.symbol, order.exchange])
        order.orderID= str(self.localNo)
        order.vtOrderID = vtOrderID
        order.direction = req.direction
        order.price = req.price
        order.totalVolume = req.volume
        
        self.localOrderDict[str(self.localNo)] = order

        return vtOrderID
    
    #----------------------------------------------------------------------
    def cancelOrder(self, req):
        """撤单"""
        localNo = req.orderID
        if localNo in self.localNoDict:
            orderID = self.localNoDict[localNo]
            self.spotCancelOrder(req.symbol, orderID)
        else:
            # 如果在系统委托号返回前客户就发送了撤单请求，则保存
            # 在cancelDict字典中，等待返回后执行撤单任务
            self.cancelDict[localNo] = req

    #----------------------------------------------------------------------
    def generateDateTime(self, s):
        """生成时间"""
        dt = datetime.fromtimestamp(float(s)/1e3)
        time = dt.strftime("%H:%M:%S.%f")
        date = dt.strftime("%Y%m%d")
        return date, time
#----------------------------------------------------------------------
    def writeLog(self, content):
        """快速记录日志"""
        log = VtLogData()
        log.gatewayName = self.gatewayName
        log.logContent = content
        self.gateway.onLog(log)

    #----------------------------------------------------------------------
    def checkDataError(self, data):
        """检查回报是否存在错误"""
        rawData = data['data']
        if 'error_code' not in rawData:
            return False
        else:
            error = VtErrorData()
            error.gatewayName = self.gatewayName
            error.errorID = rawData['error_code']
            error.errorMsg = u'请求失败，功能：%s' %data['channel']
            self.gateway.onError(error)
            return True

    #----------------------------------------------------------------------
    def subscribe(self, symbol):
        """订阅行情"""
        symbol = symbol
        
        self.subscribeSpotTicker(symbol)
        self.subscribeSpotDepth(symbol, 5)
        self.subSpotOrder(symbol)
        self.subSpotBalance(symbol)
    


########################################################################
class FutureApi(OkexFuturesApi):
    """okex的API实现"""

    # ----------------------------------------------------------------------
    def __init__(self, gateway, apikey, secretkey):
        """Constructor"""
        super(FutureApi, self).__init__(apikey, secretkey)

        self.gateway = gateway  # gateway对象
        self.gatewayName = gateway.gatewayName  # gateway对象名称
        self.active = False  # 若为True则会在断线后自动重连

        self.cbDict = {}
        self.tickDict = {}
        self.orderDict = {}

        self.channelSymbolMap = {}

        self.localNo = 0  # 本地委托号
        self.localNoQueue = Queue()  # 未收到系统委托号的本地委托号队列
        self.localNoDict = {}  # key为本地委托号，value为系统委托号
        self.orderIdDict = {}  # key为系统委托号，value为本地委托号
        self.cancelDict = {}  # key为本地委托号，value为撤单请求

        self.recordOrderId_BefVolume = {}  # 记录的之前处理的量

        self.cache_some_order = {}
        self.tradeID = 0

        self.registerSymbolPairArray = set([])

        self.initCallback()
        self.forecast = 0
        self.futureindex_eos = 0
        self.futureindex_btc = 0

        self.this_week_eos = 0
        self.next_week_eos = 0
        self.quarter_eos = 0

        self.this_week_btc = 0
        self.next_week_btc = 0
        self.quarter_btc = 0

    # ----------------------------------------------------------------------
    def onMessage(self, ws, evt):
        """信息推送"""
        #evt = inflate(evt)
        #print(evt)
        try:
            data = self.readData(evt)
            print(data)
            data = data[0]
            try:
                channel = data['channel']
            except Exception, ex:
                channel = None
            if channel == None:
                return
            # try:
            if channel == "addChannel" and 'data' in data:
                channel = data['data']["channel"]
            if channel != "addChannel" and 'spot' not in channel and channel != 'login':
                # print channel
                callback = self.cbDict[channel]
                callback(data)
        except Exception, e:
            print(e)

    # ----------------------------------------------------------------------
    def onError(self, ws, evt):
        """错误推送"""
        # evt = inflate(evt)
        error = VtErrorData()
        error.gatewayName = self.gatewayName
        error.errorMsg = str(evt)
        self.gateway.onError(error)

    # ----------------------------------------------------------------------
    '''
    def onError(self, data):
        # data = inflate(data)
        error = VtErrorData()
        error.gatewayName = self.gatewayName
        error.errorMsg = str(data["data"]["error_code"])
        self.gateway.onError(error)
    '''
    # ----------------------------------------------------------------------
    def onClose(self, ws):
        """接口断开"""
        # 如果尚未连上，则忽略该次断开提示
        if not self.gateway.connected:
            return

        self.gateway.connected = False
        self.writeLog(u'服务器连接断开')

        # 重新连接
        if self.active:
            def reconnect():
                while not self.gateway.connected:
                    self.writeLog(u'等待10秒后重新连接')
                    sleep(10)
                    if not self.gateway.connected:
                        self.reconnect()

            t = Thread(target=reconnect)
            t.start()

    # ----------------------------------------------------------------------
    def subscribe(self, subscribeReq):
        try:
            symbol = subscribeReq.symbol

            if symbol not in self.registerSymbolPairArray:
                self.registerSymbolPairArray.add(symbol)
                self.subsribeFuturesTicker(symbol, "this_week")
                self.subsribeFuturesTicker(symbol, "next_week")
                self.subsribeFuturesTicker(symbol, "quarter")

                self.subscribeFuturesKline(symbol, "this_week", "1min")
                self.subscribeFuturesKline(symbol, "next_week", "1min")
                self.subscribeFuturesKline(symbol, "quarter", "1min")

                self.subscribeFuturesDepth(symbol, "this_week", 5)
                self.subscribeFuturesDepth(symbol, "next_week", 5)
                self.subscribeFuturesDepth(symbol, "quarter", 5)

                self.subscribeFuturesIndex(symbol)

                # Ticker数据
                self.channelSymbolMap["ok_sub_futureusd_%s_ticker_this_week" % symbol] = symbol + '.this_week'
                self.channelSymbolMap["ok_sub_futureusd_%s_ticker_next_week" % symbol] = symbol + '.next_week'
                self.channelSymbolMap["ok_sub_futureusd_%s_ticker_quarter" % symbol] = symbol + '.quarter'

                self.channelSymbolMap["ok_sub_futureusd_%s_kline_this_week_1min" % symbol] = symbol
                self.channelSymbolMap["ok_sub_futureusd_%s_kline_next_week_1min" % symbol] = symbol
                self.channelSymbolMap["ok_sub_futureusd_%s_kline_quarter_1min" % symbol] = symbol

                # 盘口的深度
                self.channelSymbolMap["ok_sub_futureusd_%s_depth_this_week" % symbol] = symbol
                self.channelSymbolMap["ok_sub_futureusd_%s_depth_next_week" % symbol] = symbol
                self.channelSymbolMap["ok_sub_futureusd_%s_depth_quarter" % symbol] = symbol
                self.channelSymbolMap["ok_sub_futureusd_%s_depth_quarter" % symbol] = symbol

                self.channelSymbolMap["ok_sub_futureusd_%s_index" % symbol] = symbol

        except Exception, e:
            print(e)

            # ----------------------------------------------------------------------
            #    def subscribeSingleSymbol(self, symbol):
            #        if symbol in okex_all_symbol_pairs:
            #            self.subscribeSpotTicker(symbol)
            # self.subscribeSpotDepth5(symbol)
            # self.subscribeSpotDeals(symbol)

    # ----------------------------------------------------------------------
    def futureAllOrders(self):

        try:
            print('futureAllOrders')
            # for symbol in self.registerSymbolPairArray:
            for symbol in okex_all_future_symbol:
                self.future_orderinfo(symbol, 'this_week', 1, -1, 1, 50)
                self.future_orderinfo(symbol, 'this_week', 2, -1, 1, 50)
                self.future_orderinfo(symbol, 'next_week', 1, -1, 1, 50)
                self.future_orderinfo(symbol, 'next_week', 2, -1, 1, 50)
                self.future_orderinfo(symbol, 'quarter', 1, -1, 1, 50)
                self.future_orderinfo(symbol, 'quarter', 2, -1, 1, 50)
        except Exception, e:
            print(e)
            #            self.spotOrderInfo(symbol, '-1')

            #        for orderId in self.orderIdDict.keys():
            #            order = self.orderDict.get(orderId, None)
            #            if order != None:
            #                symbol_pair = (order.symbol.split('.'))[0]
            #                self.spotOrderInfo(symbol_pair, orderId)

    # ----------------------------------------------------------------------
    def onOpen(self, ws):
        """连接成功"""
        try:
            self.gateway.connected = True
            self.writeLog(u'服务器连接成功')

            self.login()

            for symbol in okex_all_future_symbol:
                # Yifei
                '''
                self.subscribeSpotTi4632546333asfcker(symbol)
                try:
                    self.subscribeSpotDepth(symbol, 5)
                except Exception as e:
                    print e
                '''
                self.subsribeFuturesTicker(symbol, "this_week")
                self.subsribeFuturesTicker(symbol, "next_week")
                self.subsribeFuturesTicker(symbol, "quarter")

                # self.subscribeFuturesKline(symbol, "this_week","1min")
                # self.subscribeFuturesKline(symbol, "next_week","1min")
                # self.subscribeFuturesKline(symbol, "quarter","1min")

                # self.subscribeFuturesDepth(symbol,"this_week",5)
                # self.subscribeFuturesDepth(symbol,"next_week",5)
                # self.subscribeFuturesDepth(symbol,"quarter",5)
                self.subscribeFuturesIndex(symbol)

                # self.subscribeSpotDeals(symbol)

                # Ticker数据
                self.channelSymbolMap["ok_sub_futureusd_%s_ticker_this_week" % symbol] = symbol + '.this_week'
                self.channelSymbolMap["ok_sub_futureusd_%s_ticker_next_week" % symbol] = symbol + '.next_week'
                self.channelSymbolMap["ok_sub_futureusd_%s_ticker_quarter" % symbol] = symbol + '.quarter'

                self.channelSymbolMap["ok_sub_futureusd_%s_kline_this_week_1min" % symbol] = symbol
                self.channelSymbolMap["ok_sub_futureusd_%s_kline_next_week_1min" % symbol] = symbol
                self.channelSymbolMap["ok_sub_futureusd_%s_kline_quarter_1min" % symbol] = symbol

                # 盘口的深度
                self.channelSymbolMap["ok_sub_futureusd_%s_depth_this_week" % symbol] = symbol
                self.channelSymbolMap["ok_sub_futureusd_%s_depth_next_week" % symbol] = symbol
                self.channelSymbolMap["ok_sub_futureusd_%s_depth_quarter" % symbol] = symbol

                self.channelSymbolMap["ok_sub_futureusd_%s_index" % symbol] = symbol

                # 所有人的交易数据
                # self.channelSymbolMap["ok_sub_spot_%s_deals" % symbol] = symbol

                contract = VtContractData()
                contract.gatewayName = self.gatewayName
                contract.symbol = symbol + '.this_week'
                contract.exchange = EXCHANGE_OKEX
                contract.vtSymbol = '.'.join([contract.symbol, contract.exchange])
                contract.name = u'OKEX 期货 %s' % symbol
                contract.size = 0.00001
                contract.priceTick = 0.00001
                contract.productClass = PRODUCT_SPOT
                self.gateway.onContract(contract)


                contract = VtContractData()
                contract.gatewayName = self.gatewayName
                contract.symbol = symbol + '.next_week'
                contract.exchange = EXCHANGE_OKEX
                contract.vtSymbol = '.'.join([contract.symbol, contract.exchange])
                contract.name = u'OKEX 期货 %s' % symbol
                contract.size = 0.00001
                contract.priceTick = 0.00001
                contract.productClass = PRODUCT_SPOT

                self.gateway.onContract(contract)

                contract = VtContractData()
                contract.gatewayName = self.gatewayName
                contract.symbol = symbol + '.quarter'
                contract.exchange = EXCHANGE_OKEX
                contract.vtSymbol = '.'.join([contract.symbol, contract.exchange])
                contract.name = u'OKEX 期货 %s' % symbol
                contract.size = 0.00001
                contract.priceTick = 0.00001
                contract.productClass = PRODUCT_SPOT
                self.gateway.onContract(contract)

        except Exception, e:
            print(e)

    # ----------------------------------------------------------------------
    def writeLog(self, content):
        """快速记录日志"""
        log = VtLogData()
        log.gatewayName = self.gatewayName
        log.logContent = content
        self.gateway.onLog(log)

    # ----------------------------------------------------------------------
    def initCallback(self):
        """初始化回调函数"""
        try:
            self.cbDict["login"] = self.onLogin
            for symbol in okex_all_future_symbol:
                self.cbDict["ok_sub_futureusd_%s_ticker_this_week" % symbol] = self.onTicker
                self.cbDict["ok_sub_futureusd_%s_ticker_next_week" % symbol] = self.onTicker
                self.cbDict["ok_sub_futureusd_%s_ticker_quarter" % symbol] = self.onTicker

                # self.cbDict["ok_sub_futureusd_%s_kline_this_week_1min" % symbol] = self.onBar
                # self.cbDict["ok_sub_futureusd_%s_kline_next_week_1min" % symbol] = self.onBar
                # self.cbDict["ok_sub_futureusd_%s_kline_quarter_1min" % symbol] = self.onBar

                # self.cbDict["ok_sub_futureusd_%s_depth_this_week_5" % symbol] = self.onDepth
                # self.cbDict["ok_sub_futureusd_%s_depth_next_week_5" % symbol] = self.onDepth
                # self.cbDict["ok_sub_futureusd_%s_depth_quarter_5" % symbol] = self.onDepth

                self.cbDict["ok_sub_futureusd_%s_index" % symbol] = self.onIndex
                self.cbDict["%s_forecast_price" % symbol] = self.onForecast

                # self.cbDict["ok_sub_spot_%s_balance" % symbol_pair] = self.onSpotBalance

            self.cbDict['ok_sub_futureusd_userinfo'] = self.onFutureUserInfo
            self.cbDict['ok_sub_futureusd_trades'] = self.onFutureTradeInfo
            self.cbDict['ok_sub_futureusd_positions'] = self.onFuturePositionInfo
        except Exception, e:
            print(e)

    def onLogin(self, data):
        print(data)

    # ----------------------------------------------------------------------
    def onTicker(self, data):

        # data = inflate(data)
        """"""
        if 'data' not in data:
            return

        channel = data['channel']
        if channel == 'addChannel':
            return
        try:
            self.channel = self.channelSymbolMap[channel]
            symbol = self.channel

            # self.forecast = self.future_estimated_price('%s_usd' % symbol)
            # print self.forecast
            if symbol not in self.tickDict:
                tick = VtTickData()
                tick.exchange = EXCHANGE_OKEX
                tick.symbol = '.'.join([symbol, tick.exchange])
                tick.vtSymbol = '.'.join([symbol, tick.exchange])

                tick.gatewayName = self.gatewayName
                self.tickDict[symbol] = tick
            else:
                tick = self.tickDict[symbol]

            rawData = data['data']
            tick.highPrice = float(rawData['high'])
            tick.lowPrice = float(rawData['low'])
            tick.lastPrice = float(rawData['last'])
            # tick.date, tick.time = self.generateDateTime(rawData['contractId'])
            tick.datetime = datetime.now()
            tick.limitHigh = float(rawData['limitHigh'])  # (string):最高买入限制价格
            tick.limitLow = float(rawData['limitLow'])  # (string):最低卖出限制价格
            tick.vol = float(rawData['vol'])  # (double):24小时成交量
            tick.sell = float(rawData['sell'])  # (double):卖一价格
            tick.buy = float(rawData['buy'])  # (double): 买一价格
            tick.unitAmount = float(rawData['unitAmount'])  # (double):合约价值
            tick.hold_amount = float(rawData['hold_amount'])  # (double):当前持仓量
            tick.contractId = rawData['contractId']  # (long):合约ID
            tick.high = float(rawData['high'])  #:24小时最高价格
            tick.low = float(rawData['low'])  #:24 小时最低价格
            '''
            if self.symbol == "eos_":
                #self.channelSymbolMap[channel] == ('ok_sub_futureusd_%s_ticker_quarter' % symbol).decode('utf-8'):
                tick.type = 3
                if symbol[0：3] == 'eos':
                    self.quarter_eos = tick.buy
                else:
                    self.quarter_btc = tick.buy

            elif channel == ('ok_sub_futureusd_%s_ticker_next_week' % symbol).decode('utf-8'):
                tick.type = 2
                if symbol[0：3] == 'eos':
                    self.next_week_eos = tick.buy
                else:
                    self.next_week_btc = tick.buy
            elif channel == ('ok_sub_futureusd_%s_ticker_this_week' % symbol).decode('utf-8'):
                tick.type = 1
                if symbol[0：3] == 'eos':
                    self.this_week_eos = tick.buy
                else:
                    self.this_week_btc = tick.buy
            if self.next_week_eos != 0 and self.this_week_eos != 0 and self.quarter_eos != 0:
                if symbol[0：3] == 'eos':

                    tick.nextweekvsthisweek = self.next_week_eos / self.this_week_eos - 1
                    tick.quartervsthisweek = self.quarter_eos / self.this_week_eos - 1
                    tick.quartervsnextweek = self.quarter_eos / self.next_week_eos - 1
                    tick.futureindex = self.futureindex_eos
                    if self.futureindex_eos != 0:
                        tick.thisweekvsspot = self.this_week_eos / self.futureindex_eos - 1

            if self.next_week_btc != 0 and self.this_week_btc != 0 and self.quarter_btc != 0:
                if symbol[0：3] == 'btc':
                    tick.futureindex = self.futureindex_btc
                    tick.nextweekvsthisweek = self.next_week_btc / self.this_week_btc - 1
                    tick.quartervsthisweek = self.quarter_btc / self.this_week_btc - 1
                    tick.quartervsnextweek = self.quarter_btc / self.next_week_btc - 1
            '''
            if self.forecast != 0:
                tick.forecast = self.forecast

            newtick = copy(tick)
            self.gateway.onTick(newtick)
        except Exception, e:
            print(e)

    # ----------------------------------------------------------------------
    def onIndex(self, data):
        try:
            channel = data['channel']
            if channel == 'addChannel':
                return
            rawData = data['data']
            '''
            if self.channelSymbolMap[channel] == 'eos':
                self.futureindex_eos = float(rawData['futureIndex'])
                print("futureindexEOS", self.futureindex_eos)
            else:
                self.futureindex_btc = float(rawData['futureIndex'])
                print("futureindexBTC", self.futureindex_btc)
            '''
        except Exception, e:
            print(e)

    # ----------------------------------------------------------------------
    def onForecast(self, data):
        # data = inflate(data)
        try:
            self.forecast = float(data['data'])
        except Exception, e:
            print(e)
            # ----------------------------------------------------------------------

    def onBar(self, data):
        # data = inflate(data)
        """"""
        if 'data' not in data:
            return

        channel = data['channel']
        if channel == 'addChannel':
            return
        try:
            self.channel = self.channelSymbolMap[channel]
            symbol = self.channel

            bar = VtBarData()
            bar.exchange = EXCHANGE_OKEX
            bar.symbol = '.'.join([symbol, bar.exchange])
            bar.vtSymbol = '.'.join([symbol, bar.exchange])

            bar.gatewayName = self.gatewayName

            rawData = data['data']
            bar.datetime = datetime.now()
            bar.open = rawData[0][1]
            bar.high = rawData[0][2]
            bar.low = rawData[0][3]
            bar.close = rawData[0][4]
            bar.amount = rawData[0][5]
            bar.amount_cur = rawData[0][6]
            '''
            if channel == ('ok_sub_futureusd_%s_kline_quarter_1min' % symbol).decode('utf-8'):
                bar.type = 6
            elif channel == ('ok_sub_futureusd_%s_kline_next_week_1min' % symbol).decode('utf-8'):
                bar.type = 5
            elif channel == ('ok_sub_futureusd_%s_kline_this_week_1min' % symbol).decode('utf-8'):
                bar.type = 4
            '''
            newbar = copy(bar)

            self.gateway.onTick(newbar)

        except Exception, e:
            print(e)

    # ----------------------------------------------------------------------
    def onDepth(self, data):
        # data = inflate(data)
        if 'data' not in data:
            return
        try:
            channel = data['channel']
            symbol = self.channelSymbolMap[channel]
        except Exception, e:
            symbol = None
        try:
            if symbol == None:
                return

            if symbol not in self.tickDict:
                tick = VtTickData()
                tick.symbol = symbol
                tick.vtSymbol = symbol
                tick.gatewayName = self.gatewayName
                self.tickDict[symbol] = tick
            else:
                tick = self.tickDict[symbol]

            if 'data' not in data:
                return
            rawData = data['data']

            tick.bidPrice1 = rawData['bids'][0][0]
            tick.bidPrice2 = rawData['bids'][1][0]
            tick.bidPrice3 = rawData['bids'][2][0]
            tick.bidPrice4 = rawData['bids'][3][0]
            tick.bidPrice5 = rawData['bids'][4][0]

            tick.bidVolume1 = rawData['bids'][0][2]
            tick.bidVolume2 = rawData['bids'][1][2]
            tick.bidVolume3 = rawData['bids'][2][2]
            tick.bidVolume4 = rawData['bids'][3][2]
            tick.bidVolume5 = rawData['bids'][4][2]

            tick.askPrice1 = rawData['asks'][-1][0]
            tick.askPrice2 = rawData['asks'][-2][0]
            tick.askPrice3 = rawData['asks'][-3][0]
            tick.askPrice4 = rawData['asks'][-4][0]
            tick.askPrice5 = rawData['asks'][-5][0]

            tick.askVolume1 = rawData['asks'][-1][2]
            tick.askVolume2 = rawData['asks'][-2][2]
            tick.askVolume3 = rawData['asks'][-3][2]
            tick.askVolume4 = rawData['asks'][-4][2]
            tick.askVolume5 = rawData['asks'][-5][2]

            tick.date, tick.time = self.generateDateTime(rawData['timestamp'])
            # print "Depth", tick.date, tick.time

            newtick = copy(tick)
            self.gateway.onTick(newtick)
        except Exception, e:
            print(e)

        '''
            def onSpotBalance(self, data):
                """交易发生金额变动之后会触发这个函数"""
                # print data

                rawData = data['data']
                info = rawData['info']

                for symbol in info["freezed"].keys():
                    pos = VtPositionData()
                    pos.gatewayName = self.gatewayName
                    pos.symbol = symbol + "." + EXCHANGE_OKEX
                    pos.vtSymbol = symbol + "." + EXCHANGE_OKEX
                    pos.direction = DIRECTION_NET
                    pos.frozen = float(info['freezed'][symbol])
                    pos.position = pos.frozen + float(info['free'][symbol])

                self.gateway.onPosition(pos)
                # Yifei
                self.spotUserInfo()
        '''

        # ----------------------------------------------------------------------

    def onFuturePositionInfo(self, data):
        try:
            data = data['data']

            for i in range(len(data['positions'])):

                value = data['positions'][i]

                pos = VtPositionData()
                pos.gatewayName = self.gatewayName
                pos.symbol = data['symbol']

                pos.position = value['position']
                pos.contract_name = value['contract_name']  # (string): 合约名称
                pos.costprice = value['costprice']  # (string): 开仓价格
                pos.bondfreez = value['bondfreez']  # (string): 当前合约冻结保证金
                pos.avgprice = value['avgprice']  # (string): 开仓均价
                pos.contract_id = value['contract_id']  # (long): 合约id
                pos.position_id = value['position_id']  # (long): 仓位id
                pos.hold_amount = value['hold_amount']  # (string): 持仓量
                pos.eveningup = value['eveningup']  # (string): 可平仓量
                if 'margin' in value:
                    pos.margin = value['margin']  #: 固定保证金
                    pos.realized = value['realized']  #:已实现盈亏
                    pos.levetype = 0
                else:
                    pos.balance = value['balance']  # (string): 合约账户余额
                    pos.forcedprice = value['forcedprice']  # (string): 强平价格
                    pos.profitreal = value['profitreal']  # (string): 已实现盈亏
                    pos.fixmargin = value['fixmargin']  # (double): 固定保证金
                    pos.lever_rate = value['lever_rate']  # (double): 杠杆倍数
                    pos.levetype = 1
                self.gateway.onPosition(copy(pos))

        except Exception, e:
            print(e)

    # ----------------------------------------------------------------------
    def onFutureUserInfo(self, data):
        try:
            data = data['data']

            for i in range(len(data['contracts'])):
                value = data['contracts'][i]
                # 账户资金
                account = VtAccountData()
                account.gatewayName = self.gatewayName
                account.symbol = data['symbol']
                account.balance = value['balance']

                if 'available' in value:

                    account.available = value['available']
                    account.bond = value['bond']
                    account.contract_id = value['contract_id']
                    account.freeze = value['freeze']
                    account.long_order_amount = value['long_order_amount']
                    account.pre_long_order_amount = value['pre_long_order_amount']
                    account.profit = value['profit']
                    account.short_order_amount = value['short_order_amount']
                    account.pre_short_order_amount = value['pre_short_order_amount']
                else:
                    account.keep_deposit = value['keep_deposit']  # (double)：保证金
                    account.profit_real = value['profit_real']  # (double)：已实现盈亏
                    account.unit_amount = value['unit_amount']  # (int)：合约价值

                self.gateway.onAccount(account)
        except Exception, e:
            print(e)

    # ----------------------------------------------------------------------
    def onFutureTradeInfo(self, data):
        # data = inflate(data)
        """委托信息查询回调"""
        try:
            if "error_code" in data.keys():
                print(data)
                return
            rawData = data['data']
            d = rawData
            self.localNo += 1
            localNo = str(self.localNo)
            orderId = str(d['orderid'])

            self.localNoDict[localNo] = orderId
            self.orderIdDict[orderId] = localNo

            if orderId not in self.orderDict:
                order = VtOrderData()
                order.gatewayName = self.gatewayName

                # order.symbol = spotSymbolMap[d['symbol']]
                # order.symbol = '.'.join([d["symbol"], EXCHANGE_OKEX])
                # order.vtSymbol = order.symbol

                order.orderID = localNo
                order.vtOrderID = '.'.join([self.gatewayName, order.orderID])

                order.price = d['price']
                # order.totalVolume = d['amount']
                # order.direction, priceType = priceTypeMap[d['type']]

                self.orderDict[orderId] = order
            else:
                order = self.orderDict[orderId]

            order.amount = d['amount']  # amount(double): 委托数量
            order.contract_name = d['contract_name']  # contract_name(string): 合约名称
            order.create_date = d['create_date']  # created_date(long): 委托时间
            order.create_date_str = d['create_date_str']  # create_date_str(string):委托时间字符串
            order.deal_amount = d['deal_amount']  # deal_amount(double): 成交数量
            order.fee = d['fee']  # fee(double): 手续费
            # order_id(long): 订单ID
            # price(double): 订单价格
            order.price_avg = d['price_avg']  # price_avg(double): 平均价格
            order.type = d['type']  # 订单类 1：开多2：开空 3：平多 4：平空
            #
            # status(int): 订单状态(0 等待成交 1 部分成交 2 全部成交 - 1 撤单 4 撤单处理中)
            # symbol(string): btc_usd   ltc_usd   eth_usd   etc_usd   bch_usd
            order.unit_amount = d['unit_amount']  # (double):合约面值
            order.lever_rate = d['lever_rate']  # (double):杠杆倍数
            # order.value = d['value']  #:10 / 20 默认10
            order.system_type = d['system_type']  # (int):订单类型0:普通1:交割2:强平4:全平5:系统反单

            # order.tradedVolume = d['deal_amount']
            # order.status = statusMap[d['status']]

            self.gateway.onOrder(copy(order))
        except Exception, e:
            print(e)

    '''
        def onSpotOrder(self, data):
            # Yifei
            print data
            rawData = data['data']
            if 'error_code' in rawData.keys():
                print data
                return

            orderId = str(rawData['order_id'])

            # 尽管websocket接口的委托号返回是异步的，但经过测试是
            # 符合先发现回的规律，因此这里通过queue获取之前发送的
            # 本地委托号，并把它和推送的系统委托号进行映射

            # localNo = self.orderIdDict.get(orderId, None)
            # if localNo == None:

            localNo = self.localNoQueue.get_nowait()

            self.localNoDict[localNo] = orderId
            self.orderIdDict[orderId] = localNo

            # print orderId, self.cache_some_order
            if orderId in self.cache_some_order.keys():
                arr = self.cache_some_order[orderId]
                for d in arr:
                    self.onSpotSubOrder(d)

                # 处理完就删除掉这里
                del self.cache_some_order[orderId]

            # 检查是否有系统委托号返回前就发出的撤单请求，若有则进
            # 行撤单操作
            if localNo in self.cancelDict:
                req = self.cancelDict[localNo]
                self.spotCancel(req)
                del self.cancelDict[localNo]
    '''
    '''
        # ----------------------------------------------------------------------
        def onSpotCancelOrder(self, data):
            """撤单回报"""
            # Yifei
            print data
            if 'data' not in data:
                return

            if 'error_code' in data["data"].keys():
                print '{0} - {1}; \n{2} - {3}; \n{4} - {5}'.format(
                    'hpb_eth',
                    self.tickDict['hpb_eth'].__dict__,
                    'eth_btc',
                    self.tickDict['eth_btc'].__dict__,
                    'hpb_btc',
                    self.tickDict['hpb_btc'].__dict__
                )
                self.onError(data)
                return

            rawData = data['data']
            orderId = str(rawData['order_id'])

            localNo = self.orderIdDict[orderId]

            if orderId not in self.orderDict:
                order = VtOrderData()
                order.gatewayName = self.gatewayName

                order.symbol = '.'.join([rawData['symbol'], EXCHANGE_OKEX])
                order.vtSymbol = order.symbol

                order.orderID = localNo
                order.vtOrderID = '.'.join([self.gatewayName, order.orderID])

                self.orderDict[orderId] = order
            else:
                order = self.orderDict[orderId]

            order.status = STATUS_CANCELLED
            self.gateway.onOrder(order)

            del self.orderDict[orderId]
            del self.orderIdDict[orderId]
            del self.localNoDict[localNo]

            if orderId in self.cache_some_order.keys():
                del self.cache_some_order[orderId]
    '''

    # ----------------------------------------------------------------------
    def sendOrder(self, req):
        """发单"""
        try:
            # symbol = spotSymbolMapReverse[req.symbol][:4]
            # symbol = (req.symbol.split('.'))[0]
            # type_ = priceTypeMapReverse[(req.direction, req.priceType)]
            # self.spotTrade(symbol, type_, str(req.price), str(req.volume))
            result = self.future_trade(req.symbol, req.contracttype, req.price, req.volume, req.tradetype, req.matchprice,
                              req.leverrate)

            # 若请求失败，则返回空字符串委托号
            if not result:
                return ''

            # 本地委托号加1，并将对应字符串保存到队列中，返回基于本地委托号的vtOrderID
            self.localNo += 1
            self.localNoQueue.put(str(self.localNo))
            vtOrderID = '.'.join([self.gatewayName, str(self.localNo)])

            # 缓存委托信息
            order = VtOrderData()
            order.gatewayName = self.gatewayName

            order.symbol = req.symbol
            order.exchange = EXCHANGE_OKEX
            order.vtSymbol = '.'.join([order.symbol,oder.contracttype, order.exchange])
            order.orderID = str(self.localNo)
            order.vtOrderID = vtOrderID
            order.direction = req.direction
            order.price = req.price
            order.totalVolume = req.volume

            self.localOrderDict[str(self.localNo)] = order

            return vtOrderID
        except Exception, e:
            print(e)


    # ----------------------------------------------------------------------
    def cancelOrder(self, req):
        """撤单"""
        try:
            # symbol = spotSymbolMapReverse[req.symbol][:4]
            # symbol = (req.symbol.split('.'))[0]
            localNo = req.orderID

            if localNo in self.localNoDict:
                orderID = self.localNoDict[localNo]
                self.future_cancel(req.symbol, req.contracttype, req.orderID)
            else:
                # 如果在系统委托号返回前客户就发送了撤单请求，则保存
                # 在cancelDict字典中，等待返回后执行撤单任务
                self.cancelDict[localNo] = req
        except Exception, e:
            print(e)

    # ----------------------------------------------------------------------
    def generateDateTime(self, s):
        """生成时间"""
        dt = datetime.fromtimestamp(float(s) / 1e3)
        time = dt.strftime("%H:%M:%S.%f")
        date = dt.strftime("%Y%m%d")
        return date, time


def inflate(data):
    try:
        decompress = zlib.decompressobj(-zlib.MAX_WBITS)
        inflated = decompress.decompress(data)
        inflated += decompress.flush()
        return inflated
    except Exception, e:
        print(e)