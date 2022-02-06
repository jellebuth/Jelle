from decimal import Decimal
import logging
from hummingbot.core.event.events import OrderType
from hummingbot.strategy.market_trading_pair_tuple import MarketTradingPairTuple
from hummingbot.logger import HummingbotLogger
from hummingbot.connector.exchange_base import ExchangeBase
from hummingbot.strategy.strategy_py_base import StrategyPyBase
hws_logger = None


class LimitOrder1(StrategyPyBase):
    # We use StrategyPyBase to inherit the structure. We also
    # create a logger object before adding a constructor to the class.
    @classmethod
    def logger(cls) -> HummingbotLogger:
        global hws_logger
        if hws_logger is None:
            hws_logger = logging.getLogger(__name__)
        return hws_logger

    def init_params(self,
                    maker_market_info: MarketTradingPairTuple,
                    taker_market_info: MarketTradingPairTuple,
                    target_base_balance,
                    min_order_amount,
                    slippage_buffer_fix,
                    waiting_time,
                    counter = 0,
                    fix_count = 0,
                    ):

        self._maker_market_info = maker_market_info
        self._taker_market_info = taker_market_info
        self._min_order_amount = min_order_amount
        self._counter = counter
        self._waiting_time = waiting_time
        self._all_markets_ready = True
        self._fix_count = fix_count
        self._target_base_balance = target_base_balance
        self._slippage_buffer_fix = slippage_buffer_fix
        self._connector_ready = False
        self._order_completed = False
        self._maker_order_ids = []
        self.add_markets([self._maker_market_info.market, self._taker_market_info.market])

    # After initializing the required variables, we define the tick method.
    # The tick method is the entry point for the strategy.
    def tick(self, timestamp: float):

        if not self._all_markets_ready:
            self._all_markets_ready = all([market.ready for market in self.active_markets])
            if not self._all_markets_ready:
                return
            else:
                self.logger().info("Markets are ready.")
                self.logger().info("Trading started.")

        self._last_timestamp = timestamp

        self._balance_fix_fix(self._maker_market_info, self._taker_market_info)

    # Emit a log message when the order complete

    def did_complete_buy_order(self, order_completed_event):
        self.logger().info(f"Your limit buy order {order_completed_event.order_id} has been executed")
        self.logger().info(order_completed_event)

    def _balance_fix_check(self):
        if self._order_size_base > self._min_order_amount:
            self.logger().info(f"Base balance too high or too low. Order_size base: {self._order_size_base} Base Balance: {self._maker_available_balance_base + self._taker_available_balance_base}, Target Balance: {self._target_base_balance}, Diff: {self._pref_base_min_actual}")
            self._counter = self._counter + 1

        else:
            self._counter = 0

    def _check_available_balance(self, is_buy: bool):
        # actual balance lower than wanted, thus need to buy
        if is_buy:
            #  check balance to check weather you can buy the asset
            if self._taker_available_balance_quote > self._taker_order_size_in_quote:  # check if availabale balance is enough
                self.logger().info("Taker enough quote balance, will place a taker buy order")
                return "buy_taker"
            elif self._maker_available_balance_quote > self._maker_order_size_in_quote:  # check if availabale balance is enough
                self.logger().info("Maker enough quote balance, will place a maker buy order")
                return "buy_maker"  # not enough balance to buy
            else:
                if (self._maker_available_balance_quote + self._taker_available_balance_quote) > self._maker_order_size_in_quote:
                    return "buy_maker_taker"
                    self.logger().info("Enough quote balane on both exchanges only, will place maker and taker buy")
                else:
                    self.logger().info(f"Not enough quote balance to buy Order size: {self._order_size_base}. Maker Quote balance: {self._maker_available_balance_quote}, Taker Quote balance:{self._taker_available_balance_quote} Order size in quote: {self._maker_order_size_in_quote}")
                return False

        else:
            # check balance to chech weather you can sell the asset
            if self._taker_available_balance_base > self._order_size_base:
                self.logger().info("Taker enough base balance, will place a taker sell order")
                return "sell_taker"
            elif self._maker_available_balance_base > self._order_size_base:
                self.logger().info("Maker enough base balance, will place a Maker sell order")
                return "sell_maker"

            else:  # not enough balance to place it on one available exchange
                if (self._maker_available_balance_base + self._taker_available_balance_base) > self._order_size_base:
                    return "sell_maker_taker"
                    self.logger().info("Enough base balane on both exchanges only, will place taker and maker sell")
                else:
                    self.logger().info(f"Not enough base balance to sell. order size: {self._order_size_base} Base balance:, Available base balance:")
                    return False

    def _place_fixing_order(self, is_maker: bool, is_buy: bool):
        if is_buy and is_maker:
            self.logger().info("Going to place a maker buy order")
            self.buy_with_specific_market(
                self._maker_market_info,  # market_trading_pair_tuple
                self._order_size_base,  # amount
                OrderType.LIMIT,    # order_type
                Decimal(self._mid_price_taker_buy_price)      # price
            )

        if is_buy and not is_maker:
            self.logger().info("Going to place a taker buy order")
            self.buy_with_specific_market(
                self._taker_market_info,  # market_trading_pair_tuple
                self._order_size_base,  # amount
                OrderType.LIMIT,    # order_type
                Decimal(self._mid_price_taker_buy_price)    # price
            )
            self.logger().info(f"This is a test to check, the info of the exchange {self._taker_market_info} this is the maker {self._maker_market_info} ")

        if not is_buy and is_maker:
            self.logger().info("Going to place a maker sell order")
            self.sell_with_specific_market(
                self._maker_market_info,  # market_trading_pair_tuple
                self._order_size_base,  # amount
                OrderType.LIMIT,    # order_type
                Decimal(self._mid_price_taker_sell_price)          # price
            )

        if not is_buy and not is_maker:
            self.logger().info("Going to place a taker sell order")
            self.sell_with_specific_market(
                self._taker_market_info,  # market_trading_pair_tuple
                self._order_size_base,  # amount
                OrderType.LIMIT,    # order_type
                Decimal(self._mid_price_taker_sell_price)         # price
            )

    def _balance_fix_fix(self, _maker_market_info, _taker_market_info):
        self._mid_price_taker = self._taker_market_info.get_mid_price()
        self._mid_price = self._taker_market_info.get_mid_price()
        self._mid_price_taker_buy_price: Decimal = self._mid_price * (Decimal("1") + self._slippage_buffer_fix)
        self._mid_price_taker_sell_price: Decimal = self._mid_price * (Decimal("1") - self._slippage_buffer_fix)
        self._maker_market: ExchangeBase = self._maker_market_info.market
        self._taker_market: ExchangeBase = self._taker_market_info.market
        self._maker_base_balance: Decimal = self._maker_market_info.base_balance
        self._taker_base_balance: Decimal = self._taker_market_info.base_balance
        self._maker_quote_balance: Decimal = self._maker_market_info.quote_balance
        self._taker_quote_balance: Decimal = self._taker_market_info.quote_balance
        self._total_base_balance: Decimal = self._taker_market_info.base_balance + self._maker_market_info.base_balance
        self._pref_base_min_actual = Decimal(self._target_base_balance - self._total_base_balance)
        self._maker_available_balance_quote = self._maker_market.get_available_balance(self._maker_market_info.quote_asset)
        self._taker_available_balance_quote = self._taker_market.get_available_balance(self._taker_market_info.quote_asset)
        self._maker_available_balance_base = self._maker_market.get_available_balance(self._maker_market_info.base_asset)
        self._taker_available_balance_base = self._taker_market.get_available_balance(self._taker_market_info.base_asset)
        self._order_size_base: abs = abs(self._pref_base_min_actual)
        self._maker_order_size_in_quote = (self._order_size_base * self._mid_price_taker_buy_price)
        self._taker_order_size_in_quote = (self._order_size_base * self._mid_price_taker_buy_price)

        self._balance_fix_check()

        if self._counter > self._waiting_time:
            if self._pref_base_min_actual > 0 and self._order_size_base > self._min_order_amount:  # second time checking if there is a difference, if there is, place buy order
                # here you would want to cancell all orders on the exchanges
                self.logger().info(f"Timer passes {self._waiting_time} seconds, current value of Timer: {self._counter} Order_size base: {self._order_size_base} Base Balance: {self._maker_available_balance_base + self._taker_available_balance_base}, Target Balance: {self._target_base_balance}, Diff: {self._pref_base_min_actual}")
                # available balance with a buy order on maker side
                if self._check_available_balance(is_buy = True) == "buy_maker":
                    self._place_fixing_order(is_maker = True, is_buy = True)  # place maker buy order
                    self.logger().info("Maker buy order placed")

                # available balance with a buy order on taker side
                if self._check_available_balance(is_buy = True) == "buy_taker":
                    self._place_fixing_order(is_maker = False, is_buy = True)  # place taker buy order
                    self.logger().info("Taker buy order placed")

                # buy on maker and taker
                if self._check_available_balance(is_buy = True) == "buy_maker_taker":
                    # buy as much as possible on the taker exchange
                    self.buy_with_specific_market(
                        self._taker_market_info,  # market_trading_pair_tuple
                        Decimal((self._taker_available_balance_quote / self._mid_price_taker_buy_price)),  # amount
                        OrderType.LIMIT,    # order_type
                        Decimal(self._mid_price_taker_buy_price))  # price
                    self.logger().info(f"Place buy order on taker and maker - Taker buy order is placed with most available balance. Available balance quote: {self._taker_available_balance_quote}, Buy price: {self._mid_price_taker_buy_price}, Order size: {Decimal((self._taker_available_balance_quote * self._mid_price_taker_buy_price))}  ")

                    # if there is enough remaining on the maker exchange, also place an order on the maker exchange with the remainging volume
                    if self._maker_order_size_in_quote - (self._taker_available_balance_quote * self._mid_price_taker_buy_price > self._maker_available_balance_quote * self._mid_price * (Decimal("1"))):
                        self.buy_with_specific_market(
                            self._maker_market_info,  # market_trading_pair_tuple
                            Decimal((self._taker_order_size_in_quote - (self._taker_available_balance_quote / self._mid_price_taker_buy_price))),  # amount, this is left to be placed
                            OrderType.LIMIT,    # order_type
                            Decimal(self._mid_price_taker_buy_price))
                        self.logger().info(f"Place buy order on taker and maker - The remaining amount of buy order is placed on the maker exchange Taker available quote: {self._taker_available_balance_quote}")

                    else:  # if there is not enough on the maker exchange, just buy whatever you can buy
                        if Decimal(self._maker_available_balance_quote / self._mid_price_taker_buy_price) > self._min_order_amount:
                            self.buy_with_specific_market(
                                self._maker_market_info,  # market_trading_pair_tuple
                                Decimal(self._maker_available_balance_quote / self._mid_price_taker_buy_price),  # amount
                                OrderType.LIMIT,    # order_type
                                Decimal(self._mid_price_taker_buy_price))
                            self.logger().info("Place buy order on taker and maker - An order with as much maker buy available is placed as last option")
                        else:
                            pass

                # if not one of these situations
                else:  # what if there is not enough balance, add an argument that will buy
                    self.logger().info("All availablity arguments were passed for a buy order, should place max buy and max sell")
                    # cancel all orders for pair
                    # place new order

            if self._pref_base_min_actual < 0 and self._order_size_base > self._min_order_amount:  # after checking again if there is a difference in balance
                self.logger().info("There is still too much on the exchange, going to place a sell order")

                # available balance with a sell order on taker side
                if self._check_available_balance(is_buy = False) == "sell_taker":
                    self._place_fixing_order(is_maker = False, is_buy = False)  # place taker sell order
                    self.logger().info("Taker sell order placed")

                # available balance with a sell order on maker side
                if self._check_available_balance(is_buy = False) == "sell_maker":
                    self._place_fixing_order(is_maker = True, is_buy = False)  # place maker sell order
                    self.logger().info("Maker sell order placed")

                # sell on maker and taker, place a taker sell order with as much as possible
                if self._check_available_balance(is_buy = False) == "sell_maker_taker":
                    # place order on the taker exchange with volume available balance
                    self.sell_with_specific_market(
                        self._taker_market_info,  # market_trading_pair_tuple
                        self._taker_available_balance_base,  # amount
                        OrderType.LIMIT,    # order_type
                        self._mid_price_taker_sell_price)      # price
                    self.logger().info("Place sell order on taker and maker - Taker sell order is placed with most available balance")

                    # if there is enough remaining on the maker exchange, also place an order on the maker exchange with the remainging value
                    if self._order_size_base - self._taker_available_balance_base > self._maker_available_balance_base:
                        self.sell_with_specific_market(
                            self._maker_market_info,  # market_trading_pair_tuple
                            (self._order_size_base - self._taker_available_balance_base),  # amount what is left needs to be placed
                            OrderType.LIMIT,    # order_type
                            self._mid_price_taker_sell_price)
                        self.logger().info("Place sell order on taker and maker - The remaining amount of sell order is placed on the maker exchange")

                    else:  # sell all availabe balance on the maker
                        if self._maker_available_balance_base > self._min_order_amount:
                            self.sell_with_specific_market(
                                self._maker_market_info,  # market_trading_pair_tuple
                                self._maker_available_balance_base,  # amount what is left needs to be placed
                                OrderType.LIMIT,    # order_type
                                self._mid_price_taker_sell_price)
                            self.logger().info("Place sell order on taker and maker - An order with as much maker sell available is placed as last option")
                        else:
                            pass

                else:
                    # just place the available balance on the maker and taker to get as close as pooible
                    self.logger().info("all check availability arguments were passes for a sell order")

                # cancel order
                # place order
