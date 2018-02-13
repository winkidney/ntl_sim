from sim.netrual import Component, NLT_reserve, NLT_components, NLT_accounts  # noqa
from sim.data import get_batch_price
from sim.simulator import sim_loop


target = ['EOS', 'OMG', 'ELF', 'BNB', 'INS', 'MANA', 'IOST', 'ARK']

market_prices = get_batch_price(target)


NLT_accounts['satoshi'] = 10000000000000

sim_loop(market_prices)
quit()
