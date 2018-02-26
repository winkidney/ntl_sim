from collections import defaultdict
import logging

from decimal import Decimal
import pandas as pd

from sim.netrual import Component
from utils import should_convert2target


EOS = 'EOS'
OMG = 'OMG'
USDT = 'USDT'
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


class Exchange:
    num_ntl_each_round = Decimal('1000')

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
        self.update_kline()
        for component in self.components.values():
            component.auction('the-god', Decimal('2'))

    def get_flat_price(self, symbol):
        return Decimal(self.current_prices[symbol])

    def get_ntl_min_price(self, token_name):
        component = self.components[token_name]
        return Decimal(component.min_bid)

    def redeem(self, num_ntl, symbol, sender_name):
        """
        return token.
        """
        component = self.components[symbol]
        num_redeemed = component.redeem(sender_name, num_ntl)
        if num_redeemed is False:
            return None
        return Decimal(num_redeemed)

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

    def __init__(self, source, target, assets, exchange):
        """
        :type exchange: Exchange
        """
        self.assets = assets
        self.source = source
        self.target = target
        self.exchange = exchange

    @staticmethod
    def get_price_with_impact_cost(min_price, premium_rate):
        return min_price * (1 + premium_rate)

    @staticmethod
    def get_premium_rate():
        # return random.randint(1, 20) / 100.0
        return 0.01

    def one_cycle(self):
        """
        Should be run each round.
        """
        source_ntl_price = self.exchange.get_ntl_min_price(self.source)
        target_ntl_price = self.exchange.get_ntl_min_price(self.target)
        source_market_price = self.exchange.get_flat_price(self.source)
        target_market_price = self.exchange.get_flat_price(self.target)

        premium_rate = Decimal(str(self.get_premium_rate()))
        if should_convert2target(
            source_market_price,
            source_ntl_price,
            target_market_price,
            target_ntl_price,
            premium_rate=premium_rate,
        ):
            if self.do_transition(self.source, self.target):
                return lambda : self.do_redeem(self.source, self.target)
        if should_convert2target(
            source_market_price,
            source_ntl_price,
            target_market_price,
            target_ntl_price,
            premium_rate=premium_rate,
        ):
            if self.do_transition(self.target, self.source):
                return lambda: self.do_redeem(self.target, self.source)

    def do_transition(self, source, target):
        price = self.exchange.get_ntl_min_price(source) + 1
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
                "You do auction with cycle: %s ntl_got: %s"
                % (
                    self.exchange.components[self.source].cycle,
                    ntl_got,
                )
            )
            return False
        self.assets[NTL] += ntl_got
        self.assets[source] -= source_cost
        bot_logger.debug("buy succeed: %s" % self.assets)
        return True

    def do_redeem(self, source, target):
        bot_logger.debug(
            "%s: redeeming, you have %s, accounts %s"
            % (
                self.exchange.components[target].cycle,
                self.assets,
                self.exchange.components[target].accounts,
            )
        )
        num_target_got = self.exchange.redeem(
            self.assets[NTL],
            target,
            self.name
        )
        if num_target_got is None:
            bot_logger.error(
                "%s: Failed to redeem, you have %s, accounts %s"
                % (
                    self.exchange.components[target].cycle,
                    self.assets,
                    self.exchange.components[target].accounts,
                )
            )
            return False
        self.assets[NTL] = 0
        self.assets[target] += num_target_got
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
                        'ntl_total_supply',
                        pd.Series(
                            self.ntl_total_supply_amounts[symbol],
                            index=self.ts,
                        )
                    ),
                    (
                        '%s_flat_price' % symbol,
                        pd.Series(
                            self.flat_prices[symbol],
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
    exchange = Exchange([EOS, OMG])
    statistic_tool = Statistics()
    trader = Trader(
        source=EOS,
        target=OMG,
        assets={
            EOS:  Decimal('1000'),
            OMG: Decimal('1000'),
            USDT: Decimal('1000'),
            NTL: Decimal('0'),
        },
        exchange=exchange,
    )
    exchange.bootstrap()
    fn = None
    counter = 0
    while True:
        counter += 1
        try:
            exchange.update_kline()
        except ValueError:
            bot_logger.info("Has no kline data, exited.")
            break
        statistic_tool.record(exchange)
        if callable(fn):
            fn()
        fn = trader.one_cycle()
    return statistic_tool.get_data_frame(exchange)


def main():
    result = run()
    return result


if __name__ == "__main__":
    main()
