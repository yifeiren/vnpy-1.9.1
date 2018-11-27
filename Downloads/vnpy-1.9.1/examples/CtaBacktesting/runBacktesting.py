# encoding: UTF-8

"""
展示如何执行策略回测。
"""

from __future__ import division
import sys
sys.path.append("/home/yf/Downloads/vnpy-1.9.1/vnpy/trader/app/ctaStrategy/strategy")


from vnpy.trader.app.ctaStrategy.ctaBacktesting import BacktestingEngine, MINUTE_DB_NAME


if __name__ == '__main__':
    from vnpy.trader.app.ctaStrategy.strategy.strategyKingKeltner import KkStrategy
    from vnpy.trader.app.ctaStrategy.strategy.strategyAtrRsi import AtrRsiStrategy
    from vnpy.trader.app.ctaStrategy.strategy.strategyBollChannel import BollChannelStrategy
    from vnpy.trader.app.ctaStrategy.strategy.strategyDoubleMa import DoubleMaStrategy
    from vnpy.trader.app.ctaStrategy.strategy.strategyDualThrust import DualThrustStrategy
    from vnpy.trader.app.ctaStrategy.strategy.strategyMultiSignal import MultiSignalStrategy
    from vnpy.trader.app.ctaStrategy.strategy.strategyTurtleTrading import TurtleTradingStrategy

    # 创建回测引擎
    engine = BacktestingEngine()
    
    # 设置引擎的回测模式为K线
    engine.setBacktestingMode(engine.BAR_MODE)

    # 设置回测用的数据起始日期
    engine.setStartDate('20180801')
    #engine.setStartDate('20130104')
    #engine.setStartDate('20110101')
    # 设置产品相关参数
    engine.setSlippage(0.0001)     # 股指1跳
    engine.setRate(0.3/1000)   # 万0.3
    engine.setSize(1)         # 股指合约大小
    engine.setPriceTick(0.0001)    # 股指最小价格变动
    
    # 设置使用的历史数据库
    #engine.setDatabase(MINUTE_DB_NAME, 'IF99')
    #engine.setDatabase(MINUTE_DB_NAME, 'eosquarter.OKEX')
    engine.setDatabase('Matrixdata_bar', 'EOS/USD.OK.TW')
    # 在引擎中创建策略对象
    d = {}
    engine.initStrategy(TurtleTradingStrategy, d)
    
    # 开始跑回测
    engine.runBacktesting()
    
    # 显示回测结果
    engine.showBacktestingResult()