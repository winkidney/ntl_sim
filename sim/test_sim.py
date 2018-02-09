from .netrual import Component

C = Component('EOS')


def test_basic():
    start = 1234566
    gap = 3600
    # cycle 0:
    assert C.cycle == 0
    C(start).auction('satoshi', 100)
    assert C(start + 1).auction('satoshi', 50) is False
    C(start + 20).auction('satoshi', 200)

    C(start + gap).auction('satoshi', 1000)
    assert C.cycle == 1

    assert C.min_bid == 200
    assert C.reserve == 200
    assert C.balance('satoshi') == 1000

    C(start + gap * 2).auction('satoshi_blalba', 1000)
    assert C.cycle == 2
    assert C.balance('satoshi') == 2000

    C(start + gap * 3).auction('satoshi_blalba', 1000)
    assert C.cycle == 3
    assert C.redeem('satoshi', 1000) > 0
    assert C.redeem('satoshi_blalba', 1000) > 0

