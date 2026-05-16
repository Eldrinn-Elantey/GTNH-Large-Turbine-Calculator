import pytest
from gtnh_turbine_calc.calc.common import find_dynamo_tier


def test_find_dynamo_tier_660():
    assert find_dynamo_tier(660) == "EV"


def test_find_dynamo_tier_58572():
    assert find_dynamo_tier(58572) == "ZPM"


def test_find_dynamo_tier_1188():
    assert find_dynamo_tier(1188) == "EV"
