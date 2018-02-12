from .netrual import NLT_reserve, NLT_components, NLT_accounts, NLT_AUCTION_WINDOW


def highest(market_prices: dict):
    return max({
        t: NLT_reserve[t] * float(p)
        for t, p in market_prices.items()
        if t != 'timestamp'
    })


def lowest(market_prices: dict):
    return min({
        t: NLT_reserve[t] * float(p)
        for t, p in market_prices.items()
        if t != 'timestamp'
    })


def nlt_value(market_prices: dict):
    h = highest(market_prices)
    if NLT_components[h].total_supply == 0:
        return 0
    return (market_prices[h] * NLT_reserve[h])


def nlt_price(market_price: dict):
    total_supply = list(NLT_components.values())[0].total_supply
    if total_supply == 0:
        return 0
    return nlt_value(market_price) / total_supply


def get_worth_to_auction(market_price: dict):
    return {
        k: v for k, v in market_price.items() if v < nlt_price(market_price)
    }


def get_worth_to_redeem(market_price: dict):
    return {
        k: v for k, v in market_price.items() if v > nlt_price(market_price)
    }


def determin_auction_quantity(market_price: dict):
    planned = {
        k: nlt_price(market_price) * NLT_AUCTION_WINDOW / v
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
    return {
        k: nlt_price(market_price) / NLT_AUCTION_WINDOW / v
        for k, v
        in get_worth_to_auction(market_price).items()
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
