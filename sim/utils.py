from .netrual import NLT_reserve, NLT_components


def highest(market_prices: dict):
    return max({
        t: NLT_reserve[t] * float(p)
        for t, p in market_prices.items()
    })


def lowest(market_prices: dict):
    return min({
        t: NLT_reserve[t] * float(p)
        for t, p in market_prices.items()
    })


def nlt_value(market_prices: dict):
    h = highest(market_prices)
    return (market_prices[h] * NLT_reserve[h]) / NLT_components[h].total_supply


def redeem_strategy(market_prices: dict, balance, rate=0.05):
    return {
        'redeemed': NLT_components[t].redeem(balance * rate)
        for t, p in market_prices.items()
        if market_prices[t] < nlt_value(market_prices)
    }


def auction_strategy(market_prices: dict, rate=1.05):
    return {
        'Bidd': NLT_components[t].redeem(NLT_components[t].min_bid * 1.05)
        for t, p in market_prices.items()
        if market_prices[t] > nlt_value(market_prices)
    }

