# encoding: UTF-8

from __future__ import print_function

import ssl
import hashlib
import json
import traceback
import zlib
from threading import Thread
from time import sleep

import websocket    
from HttpMD5Util import buildMySign, httpGet, httpPost

# OKEX网站
OKEX_SPOT_HOST = 'wss://real.okex.com:10441/websocket'               # OKEX 现货地址

OKEX_USD_CONTRACT = 'wss://real.okex.com:10440/websocket/okexapi'   # OKEX 期货地址
OKEX_usd_CONTRACT_REST = "www.okex.com"

SPOT_CURRENCY = ["usdt",
                 "btc",
                 "ltc",
                 "eth",
                 "etc",
                 "bch"]

SPOT_SYMBOL = ["ltc_btc",
               "eth_btc",
               "etc_btc",
               "bch_btc",
               "btc_usdt",
               "eth_usdt",
               "ltc_usdt",
               "etc_usdt",
               "bch_usdt",
               "etc_eth",
               "bt1_btc",
               "bt2_btc",
               "btg_btc",
               "qtum_btc",
               "hsr_btc",
               "neo_btc",
               "gas_btc",
               "qtum_usdt",
               "hsr_usdt",
               "neo_usdt",
               "gas_usdt"]

KLINE_PERIOD = ["1min",
                "3min",
                "5min",
                "15min",
                "30min",
                "1hour",
                "2hour",
                "4hour",
                "6hour",
                "12hour",
                "day",
                "3day",
                "week"]

CONTRACT_SYMBOL = ["btc",
                   "ltc",
                   "eth",
                   "etc",
                   "bch"]

CONTRACT_TYPE = ["this_week",
                 "next_week",
                 "quarter"]


########################################################################
class OkexApi(object):    
    """交易接口"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.host = ''          # 服务器
        self.apiKey = ''        # 用户名
        self.secretKey = ''     # 密码
  
        self.active = False     # 工作状态
        self.ws = None          # websocket应用对象
        self.wsThread = None    # websocket工作线程
        
        self.heartbeatCount = 0         # 心跳计数
        self.heartbeatThread = None     # 心跳线程
        self.heartbeatReceived = True   # 心跳是否收到
        
        self.reconnecting = False       # 重新连接中
    
    #----------------------------------------------------------------------
    def heartbeat(self):
        """"""
        while self.active:
            self.heartbeatCount += 1
            
            if self.heartbeatCount < 10:
                sleep(1)
            else:
                self.heartbeatCount = 0
                
                if not self.heartbeatReceived:
                    self.reconnect()
                else:
                    self.heartbeatReceived = False
                    d = {'event': 'ping'}
                    j = json.dumps(d)
                    
                    try:
                        self.ws.send(j) 
                    except:
                        msg = traceback.format_exc()
                        self.onError(msg)
                        self.reconnect()

    #----------------------------------------------------------------------
    def reconnect(self):
        """重新连接"""
        if not self.reconnecting:
            self.reconnecting = True
            
            self.closeWebsocket()           # 首先关闭之前的连接
            self.heartbeatReceived = True   # 将心跳状态设为正常
            self.initWebsocket()
        
            self.reconnecting = False
        
    #----------------------------------------------------------------------
    def connect(self, host, apiKey, secretKey, trace=False):
        """连接"""
        self.host = host
        self.apiKey = apiKey
        self.secretKey = secretKey
        
        websocket.enableTrace(trace)
        
        self.initWebsocket()
        self.active = True
        
    #----------------------------------------------------------------------
    def initWebsocket(self):
        """"""
        '''
        self.ws = websocket.WebSocketApp(self.host, 
                                         on_message=self.onMessageCallback,
                                         on_error=self.onErrorCallback,
                                         on_close=self.onCloseCallback,
                                         on_open=self.onOpenCallback)        
        '''
        self.ws = websocket.WebSocketApp(self.host,
                                         on_message=self.onMessage,
                                         on_error=self.onError,
                                         on_close=self.onClose,
                                         on_open=self.onOpen)

        kwargs = {'sslopt': {'cert_reqs': ssl.CERT_NONE}, 'ping_interval':25}
        self.wsThread = Thread(target=self.ws.run_forever, kwargs=kwargs)
        self.wsThread.start()

    #----------------------------------------------------------------------
    def readData(self, evt):
        """解码推送收到的数据"""
        # 先解压
        decompress = zlib.decompressobj(-zlib.MAX_WBITS)
        inflated = decompress.decompress(evt)
        inflated += decompress.flush()
        
        # 再转换为json
        data = json.loads(inflated)
        return data

    #----------------------------------------------------------------------
    def closeHeartbeat(self):
        """关闭接口"""
        if self.heartbeatThread and self.heartbeatThread.isAlive():
            self.active = False
            self.heartbeatThread.join()

    #----------------------------------------------------------------------
    def closeWebsocket(self):
        """关闭WS"""
        if self.wsThread and self.wsThread.isAlive():
            self.ws.close()
            self.wsThread.join()
    
    #----------------------------------------------------------------------
    def close(self):
        """"""
        self.closeHeartbeat()
        self.closeWebsocket()
        
    #----------------------------------------------------------------------
    def onMessage(self, data):
        """信息推送""" 
        print('onMessage')
        print(data)
        
    #----------------------------------------------------------------------
    def onError(self, data):
        """错误推送"""
        print('onError')
        print(data)
        
    #----------------------------------------------------------------------
    def onClose(self):
        """接口断开"""
        print('onClose')
        
    #----------------------------------------------------------------------
    def onOpen(self):
        """接口打开"""
        print('onOpen')
    
    #----------------------------------------------------------------------
    def onMessageCallback(self, ws, evt):
        """""" 
        data = self.readData(evt)
        if 'event' in data:
            self.heartbeatReceived = True
        else:
            self.onMessage(data[0])
        
    #----------------------------------------------------------------------
    def onErrorCallback(self, ws, evt):
        """"""
        self.onError(evt)
        
    #----------------------------------------------------------------------
    def onCloseCallback(self, ws):
        """"""
        self.onClose()
        
    #----------------------------------------------------------------------
    def onOpenCallback(self, ws):
        """"""
        if not self.heartbeatThread:
            self.heartbeatThread = Thread(target=self.heartbeat)
            self.heartbeatThread.start()
        
        self.onOpen()
        
    #----------------------------------------------------------------------
    def generateSign(self, params):
        """生成签名"""
        l = []
        for key in sorted(params.keys()):
            l.append('%s=%s' %(key, params[key]))
        l.append('secret_key=%s' %self.secretKey)
        sign = '&'.join(l)
        return hashlib.md5(sign.encode('utf-8')).hexdigest().upper()

    #----------------------------------------------------------------------
    def sendRequest(self, channel, params=None):
        """发送请求"""
        # 生成请求
        d = {}
        d['event'] = 'addChannel'
        d['channel'] = channel        
        
        # 如果有参数，在参数字典中加上api_key和签名字段
        if params is not None:
            params['api_key'] = self.apiKey
            params['sign'] = self.generateSign(params)
            d['parameters'] = params
        
        # 使用json打包并发送
        j = json.dumps(d)
        
        # 若触发异常则重连
        try:
            self.ws.send(j)
            return True
        except websocket.WebSocketConnectionClosedException:
            self.reconnect()
            return False

    #----------------------------------------------------------------------
    def login(self):
        params = {}
        params['api_key'] = self.apiKey
        params['sign'] = self.generateSign(params)
        
        # 生成请求
        d = {}
        d['event'] = 'login'
        d['parameters'] = params
        j = json.dumps(d)
        
        # 若触发异常则重连
        try:
            self.ws.send(j)
            return True
        except websocket.WebSocketConnectionClosedException:
            self.reconnect()
            return False


########################################################################
class OkexSpotApi(OkexApi):    
    """现货交易接口"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        super(OkexSpotApi, self).__init__()

    #----------------------------------------------------------------------
    def subscribeSpotTicker(self, symbol):
        """订阅现货的Tick"""
        channel = 'ok_sub_spot_%s_ticker' %symbol
        self.sendRequest(channel)

    #----------------------------------------------------------------------
    def subscribeSpotDepth(self, symbol, depth=0):
        """订阅现货的深度"""
        channel = 'ok_sub_spot_%s_depth' %symbol
        if depth:
            channel = channel + '_' + str(depth)
        self.sendRequest(channel)

    #----------------------------------------------------------------------
    def subscribeSpotDeals(self, symbol):
        channel = 'ok_sub_spot_%s_deals' %symbol
        self.sendRequest(channel)

    #----------------------------------------------------------------------
    def subscribeSpotKlines(self, symbol, period):
        channel = 'ok_sub_spot_%s_kline_%s' %(symbol, period)
        self.sendRequest(channel)

    #----------------------------------------------------------------------
    def spotOrder(self, symbol, type_, price, amount):
        """现货委托"""
        params = {}
        params['symbol'] = str(symbol)
        params['type'] = str(type_)
        params['price'] = str(price)
        params['amount'] = str(amount)
        
        channel = 'ok_spot_order'
        
        return self.sendRequest(channel, params)

    #----------------------------------------------------------------------
    def spotCancelOrder(self, symbol, orderid):
        """现货撤单"""
        params = {}
        params['symbol'] = str(symbol)
        params['order_id'] = str(orderid)
        
        channel = 'ok_spot_cancel_order'

        self.sendRequest(channel, params)
    
    #----------------------------------------------------------------------
    def spotUserInfo(self):
        """查询现货账户"""
        channel = 'ok_spot_userinfo'
        self.sendRequest(channel, {})

    #----------------------------------------------------------------------
    def spotOrderInfo(self, symbol, orderid):
        """查询现货委托信息"""
        params = {}
        params['symbol'] = str(symbol)
        params['order_id'] = str(orderid)
        
        channel = 'ok_spot_orderinfo'
        
        self.sendTradingRequest(channel, params)

    
    #----------------------------------------------------------------------
    def subSpotOrder(self, symbol):
        """订阅委托推送"""
        channel = 'ok_sub_spot_%s_order' %symbol
        self.sendRequest(channel)
    
    #----------------------------------------------------------------------
    def subSpotBalance(self, symbol):
        """订阅资金推送"""
        channel = 'ok_sub_spot_%s_balance' %symbol
        self.sendRequest(channel)


########################################################################
class OkexFuturesApi(OkexApi):
    """期货交易接口
    
    交割推送信息：
    [{
        "channel": "btc_forecast_price",
        "timestamp":"1490341322021",
        "data": "998.8"
    }]
    data(string): 预估交割价格
    timestamp(string): 时间戳
    
    无需订阅，交割前一小时自动返回
    """

    #----------------------------------------------------------------------
    def __init__(self, apikey, secretkey):
        """Constructor"""
        super(OkexFuturesApi, self).__init__()

        self.__url = OKEX_usd_CONTRACT_REST
        self.__apikey = apikey
        self.__secretkey = secretkey

    #----------------------------------------------------------------------
    def subsribeFuturesTicker(self, symbol, contractType):
        """订阅期货行情"""
        channel ='ok_sub_futureusd_%s_ticker_%s' %(symbol, contractType)
        self.sendRequest(channel)

    #----------------------------------------------------------------------
    def subscribeFuturesKline(self, symbol, contractType, period):
        """订阅期货K线"""
        channel = 'ok_sub_futureusd_%s_kline_%s_%s' %(symbol, contractType, period)
        self.sendRequest(channel)

    #----------------------------------------------------------------------
    def subscribeFuturesDepth(self, symbol, contractType, depth=0):
        """订阅期货深度"""
        channel = 'ok_sub_futureusd_%s_depth_%s' %(symbol, contractType)
        if depth:
            channel = channel + '_' + str(depth)
        self.sendRequest(channel)

    ##----------------------------------------------------------------------
    #def subscribeFuturesTrades(self, symbol, contractType):
    #    """订阅期货成交"""
    #    channel = 'ok_sub_futureusd_%s_trade_%s' %(symbol, contractType)
    #    self.sendRequest(channel)

    #----------------------------------------------------------------------
    def subscribeFuturesIndex(self, symbol):
        """订阅期货指数"""
        channel = 'ok_sub_futureusd_%s_index' %symbol
        self.sendRequest(channel)
        
    '''
    #----------------------------------------------------------------------
    def futuresTrade(self, symbol, contractType, type_, price, amount, matchPrice='0', leverRate='10'):
        """期货委托"""
        params = {}
        params['symbol'] = str(symbol)
        params['contract_type'] = str(contractType)
        params['price'] = str(price)
        params['amount'] = str(amount)
        params['type'] = type_                # 1:开多 2:开空 3:平多 4:平空
        params['match_price'] = matchPrice    # 是否为对手价： 0:不是 1:是 当取值为1时,price无效
        params['lever_rate'] = leverRate
        
        channel = 'ok_futureusd_trade'
        
        self.sendTradingRequest(channel, params)

    #----------------------------------------------------------------------
    def futuresCancelOrder(self, symbol, orderid, contractType):
        """期货撤单"""
        params = {}
        params['symbol'] = str(symbol)
        params['order_id'] = str(orderid)
        params['contract_type'] = str(contractType)
        
        channel = 'ok_futureusd_cancel_order'

        self.sendTradingRequest(channel, params)

    #----------------------------------------------------------------------
    def futuresUserInfo(self):
        """查询期货账户"""
        channel = 'ok_futureusd_userinfo'
        self.sendTradingRequest(channel, {})

    #----------------------------------------------------------------------
    def futuresOrderInfo(self, symbol, orderid, contractType, status, current_page, page_length=10):
        """查询期货委托"""
        params = {}
        params['symbol'] = str(symbol)
        params['order_id'] = str(orderid)
        params['contract_type'] = str(contractType)
        params['status'] = str(status)
        params['current_page'] = str(current_page)
        params['page_length'] = str(page_length)
        
        channel = 'ok_futureusd_orderinfo'
        
        self.sendTradingRequest(channel, params)
    '''
    '''    #----------------------------------------------------------------------
    def subscribeFuturesTrades( self):
        channel = 'ok_sub_futureusd_trades'
        self.sendTradingRequest(channel, {})

    #----------------------------------------------------------------------
    def subscribeFuturesUserInfo(self):
        """订阅期货账户信息"""
        channel = 'ok_sub_futureusd_userinfo' 
        self.sendTradingRequest(channel, {})
        
    #----------------------------------------------------------------------
    def subscribeFuturesPositions(self):
        """订阅期货持仓信息"""
        channel = 'ok_sub_futureusd_positions' 
        self.sendTradingRequest(channel, {})
    '''


    # 用于访问OKCOIN 期货REST API
    '''
    # OKCOIN期货行情信息
    def future_ticker(self, symbol, contractType):
        FUTURE_TICKER_RESOURCE = "/api/v1/future_ticker.do"
        params = ''
        if symbol:
            params += '&symbol=' + symbol if params else 'symbol=' + symbol
        if contractType:
            params += '&contract_type=' + contractType if params else 'contract_type=' + symbol
        return httpGet(self.__url, FUTURE_TICKER_RESOURCE, params)

    # OKCoin期货市场深度信息
    def future_depth(self, symbol, contractType, size):
        FUTURE_DEPTH_RESOURCE = "/api/v1/future_depth.do"
        params = ''
        if symbol:
            params += '&symbol=' + symbol if params else 'symbol=' + symbol
        if contractType:
            params += '&contract_type=' + contractType if params else 'contract_type=' + symbol
        if size:
            params += '&size=' + size if params else 'size=' + size
        return httpGet(self.__url, FUTURE_DEPTH_RESOURCE, params)

    # OKCoin期货交易记录信息
    def future_trades(self, symbol, contractType):
        FUTURE_TRADES_RESOURCE = "/api/v1/future_trades.do"
        params = ''
        if symbol:
            params += '&symbol=' + symbol if params else 'symbol=' + symbol
        if contractType:
            params += '&contract_type=' + contractType if params else 'contract_type=' + symbol
        return httpGet(self.__url, FUTURE_TRADES_RESOURCE, params)

    # OKCoin期货指数
    def future_index(self, symbol):
        FUTURE_INDEX = "/api/v1/future_index.do"
        params = ''
        if symbol:
            params = 'symbol=' + symbol
        return httpGet(self.__url, FUTURE_INDEX, params)
    '''
    # 获取美元人民币汇率
    def exchange_rate(self):
        EXCHANGE_RATE = "/api/v1/exchange_rate.do"
        return httpGet(self.__url, EXCHANGE_RATE, '')

    # 获取预估交割价
    def future_estimated_price(self, symbol):
        FUTURE_ESTIMATED_PRICE = "/api/v1/future_estimated_price.do"
        params = ''
        if symbol:
            params = 'symbol=' + symbol
        return httpGet(self.__url, FUTURE_ESTIMATED_PRICE, params)

    # 期货全仓账户信息
    def future_userinfo(self):
        FUTURE_USERINFO = "/api/v1/future_userinfo.do?"
        params = {}
        params['api_key'] = self.__apikey
        params['sign'] = buildMySign(params, self.__secretkey)
        return httpPost(self.__url, FUTURE_USERINFO, params)

    # 期货全仓持仓信息
    def future_position(self, symbol, contractType):
        try:
            FUTURE_POSITION = "/api/v1/future_position.do?"
            params = {
                'api_key': self.__apikey,
                'symbol': symbol,
                'contract_type': contractType
            }
            params['sign'] = buildMySign(params, self.__secretkey)
            result = httpPost(self.__url, FUTURE_POSITION, params)
            result = result.encode().replace('true', '1')
            result = result.replace('false', '0')


            return eval(result)
        except Exception,e:
            print(e)
    # 期货下单
    def future_trade(self, symbol, contractType, price='', amount='', tradeType='', matchPrice='', leverRate=''):
        FUTURE_TRADE = "/api/v1/future_trade.do?"
        params = {
            'api_key': self.__apikey,
            'symbol': symbol,
            'contract_type': contractType,
            'amount': amount,
            'type': tradeType,
            'match_price': matchPrice,
            'lever_rate': leverRate
        }
        if price:
            params['price'] = price
        params['sign'] = buildMySign(params, self.__secretkey)
        return httpPost(self.__url, FUTURE_TRADE, params)

    # 期货批量下单
    def future_batchTrade(self, symbol, contractType, orders_data, leverRate):
        FUTURE_BATCH_TRADE = "/api/v1/future_batch_trade.do?"
        params = {
            'api_key': self.__apikey,
            'symbol': symbol,
            'contract_type': contractType,
            'orders_data': orders_data,
            'lever_rate': leverRate
        }
        params['sign'] = buildMySign(params, self.__secretkey)
        return httpPost(self.__url, FUTURE_BATCH_TRADE, params)

    # 期货取消订单
    def future_cancel(self, symbol, contractType, orderId):
        FUTURE_CANCEL = "/api/v1/future_cancel.do?"
        params = {
            'api_key': self.__apikey,
            'symbol': symbol,
            'contract_type': contractType,
            'order_id': orderId
        }
        params['sign'] = buildMySign(params, self.__secretkey)
        return httpPost(self.__url, FUTURE_CANCEL, params)

    # 期货获取订单信息
    def future_orderinfo(self, symbol, contractType, orderId, status, currentPage, pageLength):
        FUTURE_ORDERINFO = "/api/v1/future_order_info.do?"
        params = {
            'api_key': self.__apikey,
            'symbol': symbol,
            'contract_type': contractType,
            'order_id': orderId,
            'status': status,
            'current_page': currentPage,
            'page_length': pageLength
        }
        params['sign'] = buildMySign(params, self.__secretkey)
        return httpPost(self.__url, FUTURE_ORDERINFO, params)

    # 期货逐仓账户信息
    def future_userinfo_4fix(self):
        FUTURE_INFO_4FIX = "/api/v1/future_userinfo_4fix.do?"
        params = {'api_key': self.__apikey}
        params['sign'] = buildMySign(params, self.__secretkey)
        return httpPost(self.__url, FUTURE_INFO_4FIX, params)

    # 期货逐仓持仓信息
    def future_position_4fix(self, symbol, contractType, type1):
        FUTURE_POSITION_4FIX = "/api/v1/future_position_4fix.do?"
        params = {
            'api_key': self.__apikey,
            'symbol': symbol,
            'contract_type': contractType,
            'type': type1
        }
        params['sign'] = buildMySign(params, self.__secretkey)
        return httpPost(self.__url, FUTURE_POSITION_4FIX, params)
