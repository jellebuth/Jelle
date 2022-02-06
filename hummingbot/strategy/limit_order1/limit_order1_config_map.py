from hummingbot.client.config.config_var import ConfigVar
from hummingbot.client.config.config_validators import (
    validate_exchange,
)
from hummingbot.client.settings import (
    required_exchanges,
)
import hummingbot.client.settings as settings


def maker_trading_pair_prompt():
    maker_market = limit_order1_config_map.get("maker_market").value
    example = settings.AllConnectorSettings.get_example_pairs().get(maker_market)
    return "Enter the token trading pair you would like to trade on maker market: %s%s >>> " % (
        maker_market,
        f" (e.g. {example})" if example else "",
    )


def taker_trading_pair_prompt():
    taker_market = limit_order1_config_map.get("taker_market").value
    example = settings.AllConnectorSettings.get_example_pairs().get(taker_market)
    return "Enter the token trading pair you would like to trade on taker market: %s%s >>> " % (
        taker_market,
        f" (e.g. {example})" if example else "",
    )


def exchange_on_validated(value: str) -> None:
    required_exchanges.append(value)


# List of parameters defined by the strategy
limit_order1_config_map = {
    "strategy":
        ConfigVar(key="strategy",
                  prompt="",
                  default="limit_order",
                  ),
    "maker_market":
        ConfigVar(key="maker_market",
                  prompt="Enter the name of the maker_market >>> ",
                  validator=validate_exchange,
                  on_validated=lambda value: settings.required_exchanges.append(value),
                  prompt_on_new = True,
                  ),


    "taker_market":
        ConfigVar(key="taker_market",
                  prompt="Enter the name of the taker_market >>> ",
                  validator=validate_exchange,
                  on_validated=lambda value: required_exchanges.append(value),
                  prompt_on_new=True,
                  ),

    "maker_market_trading_pair": ConfigVar(
        key="maker_market_trading_pair",
        prompt=maker_trading_pair_prompt,
        prompt_on_new=True),


    "taker_market_trading_pair": ConfigVar(
        key="taker_market_trading_pair",
        prompt=taker_trading_pair_prompt,
        prompt_on_new=True,),

    "target_base_balance":
        ConfigVar(key="target_base_balance",
                  prompt="target_base_balance >>> ",
                  type_str="decimal",
                  prompt_on_new=True,
                  ),

    "slippage_buffer_fix":
        ConfigVar(key="slippage_buffer_fix",
                  prompt="slippage_buffer_fix >>> ",
                  type_str="decimal",
                  prompt_on_new=True,
                  ),

    "min_order_amount":
        ConfigVar(key="min_order_amount",
                  prompt="min_order_amount >>> ",
                  type_str="decimal",
                  prompt_on_new=True,
                  ),

    "waiting_time":
    ConfigVar(key="waiting_time",
              prompt="waiting_time >>> ",
              type_str="decimal",
              prompt_on_new=True,
              ),

}
