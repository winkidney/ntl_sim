from .netrual import Component

C = Component('EOS')


def test_basic():
    # step 0:
    C(1).auction('satoshi', 100)
    assert C(2).auction('satoshi', 50) is False
    # step 1:
    C(3).auction('satoshi', 200)

    C(3601).auction('satoshi', 1000)
    assert C(3601).min_bid == 100
    assert C.reserve == 100
    assert C.balance('satoshi') == 1000
