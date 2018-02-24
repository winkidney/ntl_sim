from decimal import Decimal as D

import pytest
from trader import utils


@pytest.mark.parametrize(
    'eos_flat, eos_per_1k_ntl, omg_flat, omg_per_1k_ntl, premium_rate, result',
    (
        (1, 1, 1, 1, None, False),
        (2, 2, 1, 1, None, False),
        (1, 0.5, 1, 1, None, False),
        (1, 1, 2, 1, None, True),
        (2, 1, 1, 1, None, False),
        (1, 2, 1, 1, None, True),
        (1, 2, 1, 1, 1, False),
        (1, 2, 1, 1, 0.9, True),
        (1, 2, 1, 1, 1.1, False),
    )
)
def test_should_redeem_target_token(
        eos_flat, eos_per_1k_ntl, omg_flat, omg_per_1k_ntl, premium_rate, result,
):
    assert utils.should_convert2target(
        D(str(eos_flat)),
        D(str(eos_per_1k_ntl)),
        D(str(omg_flat)),
        D(str(omg_per_1k_ntl)),
        premium_rate=D(str(premium_rate)) if premium_rate is not None else None,
    ) is result
