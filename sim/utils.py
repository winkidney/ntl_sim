import operator
from .netrual import NLT_reserve, NLT_components, NLT_accounts


def highest(market_prices: dict):
    return max({
        #        t: NLT_reserve[t] * float(p)
        #        t: float(p)
        t: float(p) * NLT_components[t].min_bid

        for t, p in market_prices.items()
        if t != 'timestamp'
    }.items(), key=operator.itemgetter(1))[0]


def lowest(market_prices: dict):
    return min({
        t: float(p) * NLT_components[t].min_bid
        # t: NLT_reserve[t] * float(p)
        for t, p in market_prices.items()
        if t != 'timestamp'
    }.items(), key=operator.itemgetter(1))[0]


def nlt_price_2(market_price: dict):
    if NLT_components['EOS'].total_supply == 0:
        return nlt_price(market_price) * 10
    return sum([market_price[t] * v for t, v in NLT_reserve.items()]) / 8000

    # h = highest(market_prices)
    # return (market_prices[h] * NLT_reserve[h])


def nlt_price(market_price: dict):
    h = highest(market_price)
    return (market_price[h] * NLT_components[h].min_bid) / 1000
    # total_supply = list(NLT_components.values())[0].total_supply
    # return nlt_value(market_price) / total_supply


def get_worth_to_auction(market_price: dict):
    return {
        k: v for k, v in market_price.items() if v * NLT_components[k].min_bid / 1000 < nlt_price(market_price)
    }


def get_worth_to_redeem(market_price: dict):
    return {
        k: v for k, v in market_price.items() if v * NLT_components[k].min_bid / 1000 > nlt_price_2(market_price)
    }


def determin_auction_quantity(market_price: dict):
    planned = {
        k: nlt_price(market_price) * 1000 / v
        for k, v
        in get_worth_to_auction(market_price).items()
    }
    return {
        k: v
        for k, v
        in planned.items()
        if v >= NLT_components[k].min_bid
    }


def determin_redeem_quantity(market_price: dict):
    # redeemed = self.reserve / self.total_supply * quantity

    def quantity(token, t_price, n_price):
        q = 0
        while NLT_components[token].get_redeem_rate(q) * t_price > n_price:
            q += 1000
        return q
    planned = {
        k: quantity(k, v, nlt_price_2(market_price))
        for k, v
        in get_worth_to_auction(market_price).items()
    }

    return {
        k: v
        for k, v in planned.items()
        if v != 0
    }


def check_status():
    return {k: v.minted for k, v in NLT_components.items()}


def check_min_bid():
    return {k: v.min_bid for k, v in NLT_components.items()}


def redeem(token, market_price, sender, rate=0.002):
    balance = NLT_accounts.get(sender, float(0))
    return NLT_components[token].redeem(sender, balance * rate)


def redeem_strategy(plan: dict, sender: str, ts: int):
    return {
        'redeemed': NLT_components[t](ts).redeem(sender, q)
        for t, q in plan.items()
    }


def auction_strategy(plan: dict, sender: str, ts: int):
    return {
        'auctioned': NLT_components[t](ts).auction(sender, bid)
        for t, bid in plan.items()
    }
