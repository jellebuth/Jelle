#!/usr/bin/env python

from typing import NamedTuple

from hummingbot.strategy.market_trading_pair_tuple import MarketTradingPairTuple


class Limit_order1_MarketPair(NamedTuple):
    """
    Specifies a pair of markets for arbitrage
    """
    maker: MarketTradingPairTuple
    taker: MarketTradingPairTuple
