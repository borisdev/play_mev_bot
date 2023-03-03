#!/usr/bin/python3
"""
brownie test tests/test_uniswap_exchange.py::test_boris_playing -s
"""
import pytest
import traceback
import sys
from brownie import network


@pytest.fixture(scope="module")
def play_token(Exchange, Token, accounts):
    play_token = Token.deploy(
            "Play Token",
            "PLAY",
            18,
            1000000,
            # 1e21,
            {
                'from': accounts[0]
            }
        )
    return play_token


@pytest.fixture(scope="module")
def play_exchange(Exchange, play_token, accounts):
    play_exchange = Exchange.deploy(
            play_token,
            {
                'from': accounts[0]
            }
        )
    return play_exchange


def test_boris_playing(accounts, play_token, play_exchange, token):

    print("state 1")
    tx = play_token.approve(accounts[0], 1000)
    tx = token.approve(accounts[0], 1000)
    print("tx.call_trace():")
    tx.call_trace()
    print("tx.events:", tx.events)
    my_balance = play_token.balanceOf(accounts[0])
    n_accounts = len(accounts)

    for idx, account in enumerate(accounts):
        balance_idx = play_token.balanceOf(accounts[idx])
        print(f"play_token.balanceOf for # idx {idx} - {balance_idx}")
    amount = my_balance // n_accounts

    print("transfer event")
    tx = play_token.transfer(accounts[1], amount, {'from': accounts[0]})
    tx.call_trace()

    print("state 2")
    for idx, account in enumerate(accounts):
        balance_idx = play_token.balanceOf(accounts[idx])
        print(f"play_token.balanceOf for # idx {idx} - {balance_idx}")
    # assert play_token.balanceOf(accounts[0]) == my_balance - amount

    play_token_reserve = play_exchange.getReserve()
    print("play token reserve 1 of 2:", play_token_reserve)
    my_balance = play_token.balanceOf(accounts[0])
    print("my_balance", my_balance)
    play_token.approve(play_exchange, 1000)
    allowance = play_token.allowance(accounts[0], play_exchange)
    print("allowance:", allowance)
    # tx = play_exchange.addLiquidity(1)
    tx = play_exchange.addLiquidity(allowance)
    import ipdb
    ipdb.set_trace()
    # play_exchange.addLiquidity(1, {'from': accounts[0]})

    #try:
    #    tx = play_exchange.addLiquidity(allowance)
    #except Exception:
    #    print(tx.events)
    #    print(traceback.format_exc())
    #    # or
    #    print(sys.exc_info()[2])
    #    import ipdb
    #    ipdb.set_trace()

    play_token_reserve = play_exchange.getReserve()
    print("play token reserve 2 of 2:", play_token_reserve)
