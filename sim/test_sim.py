from .netrual import Component

C = Component('EOS')


def test_basic():
    start = 1234566
    gap = 3600
    # cycle 0:
    assert C.cycle == 0
    assert C(start).auction('satoshi', 100)
    assert C(start + 1).auction('satoshi', 50) is False
    assert C(start + 20).auction('satoshi', 200)

    assert C(start + gap).auction('satoshi', 1000)
    assert C.cycle == 12
    assert C.min_bid == 200

    assert C.min_bid == 200
    assert C.reserve == 200
    assert C.balance('satoshi') == 1000

    assert C(start + gap * 2).auction('satoshi_blalba', 1001)
    assert C.cycle == 24
    assert C.balance('satoshi') == 2000

    assert C(start + gap * 3).auction('satoshi_blalba', 1002)
    assert C.cycle == 36
    assert C.min_bid == 1001

    assert C.redeem('satoshi', 1000) > 0
    assert C.redeem('satoshi_blalba', 1000) > 0
