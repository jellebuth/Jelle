from hummingbot.strategy.market_trading_pair_tuple import MarketTradingPairTuple
from hummingbot.strategy.limit_order1 import LimitOrder1
from hummingbot.strategy.limit_order1.limit_order1_config_map import limit_order1_config_map as c_map
from decimal import Decimal


def start(self):
    maker_market = c_map.get("maker_market").value
    taker_market = c_map.get("taker_market").value
    min_order_amount = c_map.get("min_order_amount").value
    maker_trading_pair = c_map.get("maker_market_trading_pair").value
    taker_trading_pair = c_map.get("taker_market_trading_pair").value
    target_base_balance = c_map.get("target_base_balance").value
    waiting_time = c_map.get("waiting_time").value
    slippage_buffer_fix = c_map.get("slippage_buffer_fix").value / Decimal("100")

    self._initialize_markets([(maker_market, [maker_trading_pair]), (taker_market, [taker_trading_pair])])
    base_1, quote_1 = maker_trading_pair.split("-")
    base_2, quote_2 = taker_trading_pair.split("-")

    maker_market_info = MarketTradingPairTuple(self.markets[maker_market], maker_trading_pair, base_1, quote_1)
    taker_market_info = MarketTradingPairTuple(self.markets[taker_market], taker_trading_pair, base_2, quote_2)

    self.market_trading_pair_tuples = [maker_market_info, taker_market_info]

    self.strategy = LimitOrder1()
    self.strategy.init_params(maker_market_info,
                              taker_market_info,
                              target_base_balance,
                              min_order_amount,
                              slippage_buffer_fix,
                              waiting_time=waiting_time)
