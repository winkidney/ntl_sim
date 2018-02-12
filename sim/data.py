import pandas as pd


def read_csv(name, type='5m'):
    return pd.read_csv(
        './csv/binance_%s_%s_kline.csv' % (name, type),
        names=[name, 'open', 'high', 'low', 'last', 'type', 'timestamp']
    )


def get_price(token, eth_usdt=None):  # None for cache able
    if not eth_usdt:
        eth_usdt = read_csv('ETH_USDT')
    eth_target = read_csv('%s_ETH' % token)
    merged = pd.merge(eth_target, eth_usdt, on='timestamp')
    return pd.DataFrame({
        token: merged['last_x'] * merged['last_y'],
        'timestamp': merged['timestamp']
#        'timestamp': pd.to_datetime(merged['timestamp'], unit='s')
    })


def get_batch_price(tokens, eth_usdt=None):
    df = pd.concat(
        [get_price(t) for t in tokens], axis=1
    )
    # https://stackoverflow.com/questions/32041245/fast-method-for-removing-duplicate-columns-in-pandas-dataframe
    return df.loc[:, ~df.columns.duplicated()]
