from collections import defaultdict
import logging
import pandas as pd

from sim.netrual import Component


EOS = 'EOS'
OMG = 'OMG'
USDT = 'USDT'
QTUM = 'QTUM'
ELF = 'ELF'
NTL = 'NTL'


class BotLogger:
    @classmethod
    def debug(cls, *args):
        return logging.debug(*args)

    @classmethod
    def error(cls, *args):
        return logging.error(*args)

    @classmethod
    def info(cls, *args):
        return logging.info(*args)


bot_logger = BotLogger()


def read_csv(name, type='5m'):
    return pd.read_csv(
    './csv/binance_%s_%s_kline.csv' %(name, type),
    names=[name, 'open', 'high', 'low', 'last', 'type', 'timestamp']
)


def get_usdt_price_pandas(target_symbol):
    target2eth = read_csv('%s_ETH' % target_symbol)
    eth2usdt = read_csv('ETH_USDT')
    target2eth2usdt = pd.merge(target2eth, eth2usdt, on='timestamp')
    target2eth2usdt['price_usdt'] = target2eth2usdt['last_x'] * target2eth2usdt['last_y']
    return target2eth2usdt


def get_price_with_impact_cost(min_price, premium_rate):
    return min_price * (1 + premium_rate or 0)


def get_auction_premium_rate():
    # return random.randint(1, 20) / 100.0
    return 0.03


def get_redeem_premium_rate():
    return 0.01


def get_ntl_flat_price_for_component(component_last_bid, component_flat_price):
    return component_last_bid * component_flat_price


def get_redeem_amount(ntl_total_amount):
    if ntl_total_amount > 0:
        return 1000


def is_auction_ok(current_price_of_ntl, average_price_of_ntl_per_k):
    current_price_of_ntl = get_price_with_impact_cost(
        current_price_of_ntl,
        get_auction_premium_rate()
    )
    # print("avg and current: ", average_price_of_ntl_per_k, current_price_of_ntl)
    return (
        average_price_of_ntl_per_k > current_price_of_ntl,
        (average_price_of_ntl_per_k - current_price_of_ntl) / float(
            current_price_of_ntl
        )
    )

def is_redeem_ok(current_price_of_ntl, average_price_of_ntl_per_k):
    current_price_of_ntl = get_price_with_impact_cost(
        current_price_of_ntl,
        get_redeem_premium_rate()
    )
    print("avg and current: ", average_price_of_ntl_per_k, current_price_of_ntl)
    return (
        average_price_of_ntl_per_k < current_price_of_ntl,
        (
            (current_price_of_ntl - average_price_of_ntl_per_k) / float(
                average_price_of_ntl_per_k
            )
        )
    )


class Exchange:
    num_ntl_each_round = 1000

    def __init__(self, symbols):
        """
        :type components: dict[str, sim.netrual.Component]
        """
        self.current_index = 0
        self.symbols = symbols
        self.prices = {}
        self.components = {}
        self.current_prices = defaultdict(int)
        _other_symbol = None
        for symbol in symbols:
            self.components[symbol] = Component(symbol)
            if symbol != USDT:
                _other_symbol = symbol
            else:
                continue
            self.prices[symbol] = get_usdt_price_pandas(symbol)

        self.prices[USDT] = pd.Series(
            dict(
                timestamp=self.prices[_other_symbol].timestamp,
                price_usdt=[1, ] * len(self.prices[_other_symbol]),
            )
        )

    def get_ntl_average_price_per_k(self):
        total_supply = None
        valued = 0
        for symbol, component in self.components.items():
            total_supply = component.total_supply
            flat_price = self.get_flat_price(symbol)
            valued += flat_price * component.reserve
        if total_supply == 0:
            # Maybe has bug
            return 0
        return valued / total_supply * 1000

    def get_current_price_for_symbol(self, symbol):
        component = self.components[symbol]
        flat_price = self.get_flat_price(symbol)
        return component.min_bid * float(flat_price)

    def update_kline(self):
        for symbol in self.symbols:
            component = self.components[symbol]
            prices = self.prices[symbol]
            try:
                ts = prices['timestamp'][self.current_index]
            except KeyError:
                raise ValueError("Data is gone.")
            component(ts)
            self.current_prices[symbol] = prices['price_usdt'][self.current_index]
        self.current_index += 1

    def bootstrap(self):
        for x in range(100):
            self.update_kline()
            for name, component in self.components.items():
                if name == ELF:
                    component.auction('the-god', 1 + x)
                else:
                    component.auction('the-god', 0.1 + x / 10.0)

    def get_flat_price(self, symbol):
        return self.current_prices[symbol]

    def get_ntl_min_price(self, token_name):
        component = self.components[token_name]
        return component.min_bid

    def redeem(self, symbol, sender_name, num_ntl):
        """
        return token.
        """
        component = self.components[symbol]
        _redeemed = component.redeem(sender_name, num_ntl)
        num_redeemed = 0
        ntl_cost = 0
        for redeemed in _redeemed:
            if redeemed is None:
                continue
            ntl_cost += 1000
            num_redeemed += redeemed
        # num_redeemed = _redeemed
        return num_redeemed, ntl_cost

    def buy(self, num_token, symbol, sender_name):
        """
        To buy given number of NTL buy token.
        Return num_amount of ntl if succeed, None if failed
        :param num_token: 10
        :param symbol: for example EOS
        :param sender_name: trader_name
        """
        component = self.components[symbol]
        result = component.auction(sender_name, num_token)
        if result:
            return self.num_ntl_each_round
        return None

    @classmethod
    def get_ntl_each_round(cls):
        return cls.num_ntl_each_round


class Trader:
    """
    A trader that always wants more flat-money.
    """
    name = 'greed-is-good'

    def __init__(self, symbols, assets, exchange):
        """
        :type exchange: Exchange
        """
        self.assets = assets
        self.symbols = symbols
        self.exchange = exchange

    def one_cycle(self):
        """
        Should be run each round.
        """
        redeem_result = []
        for symbol in self.symbols:
            auction_ok, rate = is_auction_ok(
                self.exchange.get_current_price_for_symbol(symbol),
                self.exchange.get_ntl_average_price_per_k(),
            )
            if auction_ok:
                self.do_transition(symbol, get_auction_premium_rate())
                continue
            redeem_ok, return_rate = is_redeem_ok(
                self.exchange.get_current_price_for_symbol(symbol),
                self.exchange.get_ntl_average_price_per_k(),
            )
            if redeem_ok:
                redeem_result.append((symbol, return_rate))
        if len(redeem_result) <= 0:
            return
        symbols, returns = list(zip(*redeem_result))
        max_return = max(returns)
        symbol = symbols[returns.index(max_return)]
        self.do_redeem(symbol, self.assets[NTL])

    def do_transition(self, source, premium_rate):
        price = self.exchange.get_ntl_min_price(source)
        price = get_price_with_impact_cost(price, premium_rate)
        source_cost = price
        assert price > 0

        if self.assets[source] < source_cost:
            bot_logger.error(
                "Source cost is too much, %s, price is %s"
                % (source_cost, price)
            )
            return False
        ntl_got = self.exchange.buy(source_cost, source, self.name)
        if ntl_got is None:
            bot_logger.error(
                "You do with %s auction at cycle: %s but got no ntl"
                % (
                    source,
                    self.exchange.components[source].cycle,
                )
            )
            return False
        self.assets[NTL] += ntl_got
        self.assets[source] -= source_cost
        bot_logger.debug("buy succeed: %s" % self.assets)
        return True

    def do_redeem(self, target, num_ntl):
        bot_logger.debug(
            "%s: redeeming, you have %s, accounts %s"
            % (
                self.exchange.components[target].cycle,
                self.assets,
                self.exchange.components[target].accounts,
            )
        )
        num_target_got, ntl_cost = self.exchange.redeem(
            target,
            self.name,
            num_ntl,
        )
        self.assets[NTL] -= ntl_cost
        self.assets[target] += num_target_got
        if num_target_got == 0:
            bot_logger.error(
                "%s: Failed to redeem, you have %s, accounts %s"
                % (
                    self.exchange.components[target].cycle,
                    self.assets,
                    self.exchange.components[target].accounts,
                )
            )
            return False
        return True


class Statistics:

    def __init__(self):
        self.ntl_prices = defaultdict(list)
        self.reversed_amounts = defaultdict(list)
        self.flat_prices = defaultdict(list)
        self.ntl_total_supply_amounts = defaultdict(list)
        self.ts = []

    def record(self, exchange):
        self.ts.append(exchange.components['EOS'].timestamp)
        for symbol in exchange.symbols:
            self.ntl_prices[symbol].append(
                exchange.components[symbol].min_bid
            )
            self.reversed_amounts[symbol].append(
                exchange.components[symbol].reserve
            )
            self.ntl_total_supply_amounts[symbol].append(
                exchange.components[symbol].total_supply
            )
            self.flat_prices[symbol].append(
                exchange.get_flat_price(symbol)
            )
        self.flat_prices[NTL].append(
            exchange.get_ntl_average_price_per_k()
        )

    def get_data_frame(self, exchange):
        data_frames = []
        for symbol in exchange.symbols:
            all_data = dict(
                (
                    (
                        'ntl_%s_price' % symbol,
                        pd.Series(
                            self.ntl_prices[symbol],
                            index=self.ts,
                        )
                    ),
                    (
                        '%s_reserved' % symbol,
                        pd.Series(
                            self.reversed_amounts[symbol],
                            index=self.ts,
                        )
                    ),
                    (
                        'ntl_total_supply_%s' % symbol,
                        pd.Series(
                            self.ntl_total_supply_amounts[symbol],
                            index=self.ts,
                        )
                    ),
                    (
                        '%s_flat_price' % symbol,
                        pd.Series(
                            [float(price) for price in self.flat_prices[symbol]],
                            index=self.ts,
                        )
                    ),
                    (
                        'ntl_flat_price_%s' % symbol,
                        pd.Series(
                            self.flat_prices[NTL],
                            index=self.ts,
                        )
                    ),
                )
            )
            data_frames.append(
                pd.DataFrame(all_data)
            )
        return data_frames



def run():
    symbols = [EOS, OMG, ELF, USDT, QTUM]
    exchange = Exchange(symbols)
    statistic_tool = Statistics()
    trader = Trader(
        symbols=symbols,
        assets={
            EOS:  1000,
            OMG: 1000,
            USDT: 1000 * 10,
            QTUM: 1000,
            ELF: 1000 * 10,
            NTL: 0,
        },
        exchange=exchange,
    )
    exchange.bootstrap()
    counter = 0
    while True:
        counter += 1
        # import time
        # time.sleep(0.1)
        try:
            exchange.update_kline()
        except ValueError:
            bot_logger.info("Has no kline data, exited.")
            break
        statistic_tool.record(exchange)
        # print('NTL price: ', statistic_tool.flat_prices[NTL][-1])
        trader.one_cycle()
    df = statistic_tool.get_data_frame(exchange)
    print(trader.assets)
    return df


def main():
    result = run()
    return result


if __name__ == "__main__":
    main()
