import random
from pandas import DataFrame
import time

from .netrual import Component, NLT_reserve, NLT_components  # noqa
from .utils import redeem_strategy, auction_strategy, nlt_price
from .utils import determin_auction_quantity, determin_redeem_quantity


def warmup(start_timestamp, sender):
    begin = start_timestamp - Component.auction_window - 1
    for c in NLT_components.values():
        bid = float(random.randint(0, 100))
        print('inital bid %s' % bid)
        res = c(begin).auction(sender, random.randint(0, 100))
        print(res)


def sim_loop(market_prices: DataFrame, sender='satoshi'):
    '''
    [{token: price}]
    '''
    ret = []
    tokens = [t for t in market_prices.columns if t != 'timestamp']
    [Component(t) for t in tokens]  # inital
    warmup(market_prices.timestamp[0], sender)

    for i, data in market_prices.iterrows():
        print('==' * 20)
        print(dict(data))
        print('PRICE OF NLT %s' % nlt_price(data))
        ts = data['timestamp']
        [c(ts) for c in NLT_components.values()]
        market_price = {k: v for k, v in data.items() if k != 'timestamp'}

        ret.append({
            'ts': ts,
            'price': nlt_price(market_price)
        })
        print(ts, nlt_price(market_price))

        plan_to_auction = determin_auction_quantity(market_price)
        plan_to_redeem = determin_redeem_quantity(market_price)
        print('plan to aucthon %s, plan to redeem %s ' % (plan_to_auction, plan_to_redeem))
        time.sleep(0.001)
        redeemed = redeem_strategy(plan_to_redeem, sender, ts)
        auctioned = auction_strategy(plan_to_auction, sender, ts)
        print(redeemed)
        print(auctioned)
    return ret
