from decimal import Decimal


def _get_ntl_relative_price(
    source_token_quantity4ntl, target_token_quantity4ntl, premium_rate=None
):
    if premium_rate is not None:
        target_token_quantity4ntl = target_token_quantity4ntl * (Decimal('1') + premium_rate)
    return target_token_quantity4ntl / source_token_quantity4ntl


def _get_token_relative_price(source_usd_price, target_usd_price):
    return target_usd_price / source_usd_price


def should_convert2target(
        source_token_usd_price,
        source_token_quantity4ntl,
        target_token_usd_price,
        target_token_quantity4ntl,
        premium_rate=None
):
    """
    source: eos
    target: omg

    source_token_usd_price = 1 usd
    source_token_quantity4ntl = 10 eos

    target_token_usd_price = 1 usd
    target_token_quantity4ntl = 5 omg

    ntl_relative_price = 10 eos / 5 omg = 2
    flat_relative_price = 1 usd / 1 usd = 1

    ntl_relative_price > flat_relative_price ==> we should not redeem eos to get omg
    """
    premium_rate = premium_rate or 0
    ntl_relative_price = _get_ntl_relative_price(
        source_token_quantity4ntl, target_token_quantity4ntl, premium_rate=premium_rate
    )
    flat_relative_price = _get_token_relative_price(source_token_usd_price, target_token_usd_price)
    if ntl_relative_price < flat_relative_price:
        return True
    return False