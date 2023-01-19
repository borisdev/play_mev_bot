"""
TODO:

Test I make a basic transaction (tranfer money) via the public mempool

Test I can make a basic transaction via using a private fashbot bundle


 - pytest
 - settings.py
 - data_classes.py
 - CLI args for bot exec
 - persist tx in mongo DB or log
 - track account changes
 - use trading ai utils
 - use web3 defi utils

Notes:

- The base unit in the Ethereum protocol is wei (not Ether or gwei)

"""
from pprint import pprint
from uuid import uuid4
from time import (
    perf_counter)
from dataclasses import dataclass
# from web3.middleware import construct_sign_and_send_raw_middleware
from web3.auto import Web3
from web3.exceptions import TransactionNotFound
from web3.types import TxParams, Wei
import constants
import settings


receiverAddress = settings.CHUCKS_PUBLIC_ADDRESS

w3 = settings.web_socket_connection(use_flashbots_relay=True)

# pytest these
# utils to test my understanding


def gwei2dollars(gwei):
    """
    - all gas prices are in gwei
    - 1 gwei is 10**9 wei
    - gwie denotes giga-wei
    - wie is the smallest denomination
    - 1 eth is 10**9 gwie
    """

    eth = gwei / 10**9
    dollars = constants.dollars_per_eth * eth
    return dollars


def wei2dollars(wei):
    """
    - all gas prices are in gwei
    - 1 gwei is 10**9 wei
    - gwie denotes giga-wei
    - wie is the smallest denomination
    - 1 eth is 10**9 gwie
    """

    eth = wei / 10**18
    rate = constants.dollars_per_eth
    # rate = constants.dollars_per_eth_decimal
    dollars = rate * eth
    return dollars


def get_dollar_balance(address, block_number):
    rate = constants.dollars_per_eth
    balance = w3.eth.get_balance(address, block_number)
    try:
        result = balance * rate
    except TypeError:  # use a decimal rate
        rate = constants.dollars_per_eth_decimal
        result = balance * rate
    return result


@dataclass
class TxMeta:

    elapsed_seconds: float
    gas_fee_in_dollars: float
    start_block_number: int

    def __init__(self, tx, reciept):
        self.elapsed_seconds = perf_counter() - tx.__dict__['tx_start_time']
        self.start_block_number = tx.__dict__['start_block_number']
        self.gas_fee_in_dollars = wei2dollars(reciept.effectiveGasPrice * reciept.gasUsed)
        print("success - got a response back from the network on what happened to tx request")
        print("---- debug gas ----")
        print("gas price in gwei:", reciept.effectiveGasPrice / 10**9)
        print("gas used:", reciept.gasUsed)
        print("total transaction cost - gas fee in dollars:", self.gas_fee_in_dollars)
        print()
        # TODO: persist ... in DB or log file ?


def send_flashbots_transaction_bundle(
        bundle: list,
        flashbot_relayer=True,
        print_stats=False):

    # keep trying to send bundle until it gets mined
    round = 0
    while True:
        block = w3.eth.block_number
        try:
            print(f"Round {round} attempt ....Simulating on block {block}")
            w3.flashbots.simulate(bundle, block)
            print("Simulation successful.")
        except Exception as e:
            print("Simulation error", e)
            print(" *** traceback *** ")
            print("-------------------")
            import traceback
            print(traceback.format_exc())
            break

        # send bundle targeting next block
        print(f"Sending bundle targeting block {block+1}")
        replacement_uuid = str(uuid4())
        print(f"replacementUuid {replacement_uuid}")
        send_result = w3.flashbots.send_bundle(
            bundle,
            target_block_number=block + 1,
            opts={"replacementUuid": replacement_uuid},
        )
        bundle_hash = w3.toHex(send_result.bundle_hash())

        if print_stats:
            stats_v1 = w3.flashbots.get_bundle_stats(bundle_hash, block)
            print(" *** bundleStats v1 ***")
            pprint(stats_v1.__dict__)

            stats_v2 = w3.flashbots.get_bundle_stats_v2(bundle_hash(), block)
            print(" *** bundleStats v2 *** ")
            pprint(stats_v2.__dict__)

        send_result.wait()
        try:
            receipts = send_result.receipts()
            block_number = receipts[0].blockNumber
            print("-------")
            print("My account before tx:", get_dollar_balance(settings.my_account.address, block_number - 1))
            print("Recievers account before tx:", get_dollar_balance(receiverAddress, block_number - 1))
            print("-------")
            print("My account after tx:", get_dollar_balance(settings.my_account.address, block_number))
            print("Recievers account after tx:", get_dollar_balance(receiverAddress, block_number))

            return receipts
        except TransactionNotFound:
            round = round + 1
            print(f"Bundle not found in block {block+1}")
            # essentially a no-op but it shows that the function works
            cancel_res = w3.flashbots.cancel_bundles(replacement_uuid)
            print(f"canceled {cancel_res}")
            print("==================")


if __name__ == "__main__":

    nonce = w3.eth.get_transaction_count(settings.my_account.address)
    tx1: TxParams = {
        'to': receiverAddress,
        'value': Wei(2),
        'gas': 100000,  # compute units
        'maxFeePerGas': Web3.toWei(200, 'gwei'),  # max price per compute unit
        "maxPriorityFeePerGas": Web3.toWei(100, "gwei"),  # incentive to validator to mine this
        'nonce': nonce,
        'chainId': settings.CHAIN_ID,
        'type': 2,
    }

    sender = settings.my_account
    tx1_signed = sender.sign_transaction(tx1)

    tx2: TxParams = {
        "to": receiverAddress,
        "value": Wei(2),
        "gas": 100000,
        "maxFeePerGas": Web3.toWei(200, "gwei"),
        "maxPriorityFeePerGas": Web3.toWei(100, "gwei"),
        "nonce": nonce + 1,
        "chainId": settings.CHAIN_ID,
        "type": 2,
    }
    bundle = [
        {"signed_transaction": tx1_signed.rawTransaction},
        {"signer": sender, "transaction": tx2},
    ]
    # safety check that I do not blow away money
    MAX_LIABILITY = 100  # dollars
    raw_txs = [tx1, tx2]
    assert len(raw_txs) == len(bundle)
    total_gas_liability = 0
    for tx in raw_txs:
        tx_gas_liability = tx["gas"] * (tx["maxFeePerGas"] + tx["maxPriorityFeePerGas"])
        total_gas_liability = total_gas_liability + tx_gas_liability
    total_gas_liability_dollars = gwei2dollars(total_gas_liability / 10**9)
    print("total potential liability in gas dollars:", total_gas_liability_dollars)
    assert total_gas_liability_dollars < MAX_LIABILITY, "tx canceled! ...gas cost too high"

    send_flashbots_transaction_bundle(
        bundle,
        flashbot_relayer=True)
