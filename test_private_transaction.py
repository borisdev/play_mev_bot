"""
Test I make a basic transaction (tranfer money) via the public mempool

Test I can make a basic transaction via using a private fashbot bundle

TODO:

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
from uuid import uuid4
import os
from time import (
    perf_counter)
from os.path import join, dirname
from dotenv import load_dotenv
from dataclasses import dataclass
from eth_account import Account
from eth_account.signers.local import LocalAccount
# from web3.middleware import construct_sign_and_send_raw_middleware
from web3.auto import Web3
from web3.exceptions import TransactionNotFound
from web3.types import TxParams  # ,Wei
from flashbots import flashbot

# settings.py and constants.py
USE_GOERLI = True
CHAIN_ID = 5 if USE_GOERLI else 1

USE_GOERLI_TEST = True
wei_per_eth = 10**18
dollars_per_eth = 1252.16
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)
chuck = os.environ.get("CHUCKS_PUBLIC_ETH_ADDRESS")  # $$$$$$$$$$$$$$$$$ key
ALCHEMY_AUTH_TOKEN = os.environ.get("ALCHEMY_AUTH_TOKEN")
private_key = os.environ.get("PRIVATE_KEY")  # $$$$$$$$$$$$$$$$$ key
assert private_key is not None, "You must set PRIVATE_KEY environment variable"
assert private_key.startswith("0x"), "Private key must start with 0x hex prefix"
my_account: LocalAccount = Account.from_key(private_key)  # ETH_ACCOUNT_SIGNATURE
# my_public_address = my_account.address if USE_GOERLI_TEST else "borisdev.eth"

my_gas_limit = 30000  # meansured by computational steps
my_gas_price = Web3.toWei(100, 'gwei')


def web_socket_connection():
    if USE_GOERLI_TEST:
        rpc_endpoint = "eth-goerli.g.alchemy.com/v2/"  # P2P network node
        w3 = Web3(Web3.WebsocketProvider(f"wss://{rpc_endpoint}{ALCHEMY_AUTH_TOKEN}"))
        assert w3.isConnected()
        flashbot(w3, my_account, "https://relay-goerli.flashbots.net")
    else:
        rpc_endpoint = "eth-mainnet.g.alchemy.com/v2/"
        w3 = Web3(Web3.WebsocketProvider(f"wss://{rpc_endpoint}{ALCHEMY_AUTH_TOKEN}"))
        assert w3.isConnected()
        flashbot(w3, my_account)

    # OPTIONAL w3.middleware_onion.add(construct_sign_and_send_raw_middleware(my_account))

    return w3


# from settings import w3
w3 = web_socket_connection()

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
    dollars = dollars_per_eth * eth
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
    dollars = dollars_per_eth * eth
    return dollars


@dataclass
class TxMeta:
    """
    effectiveGasPrice - Number:
        The actual value per gas deducted from the senders account.
        Before EIP-1559, this is equal to the transaction’s gas price.
        After, it is equal to baseFeePerGas + min(maxFeePerGas - baseFeePerGas, maxPriorityFeePerGas).
    """

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


total_gas_liability = my_gas_limit * my_gas_price
total_gas_liability_dollars = gwei2dollars(total_gas_liability / 10**9)
print(" *** start new transaction ***")
print("total potential liability in gas dollars:", total_gas_liability_dollars)
assert total_gas_liability_dollars < 4, "tx canceled! ...gas cost too high"

nonce = w3.eth.get_transaction_count(my_account.address)
CHAIN_ID = 5 if USE_GOERLI else 1
tx1: TxParams = {
    'to': chuck,
    'value': 2,
    'gas': my_gas_limit,  # compute units
    'maxFeePerGas': my_gas_price,  # max price per compute unit
    "maxPriorityFeePerGas": Web3.toWei(50, "gwei"),  # incentive to validator to mine this
    'nonce': nonce,
    'chainId': CHAIN_ID,
    'type': 2,
}

sender = my_account
tx1_signed = sender.sign_transaction(tx1)
receiverAddress = chuck
tx2: TxParams = {
    "to": receiverAddress,
    "value": Web3.toWei(0.001, "ether"),
    "gas": 21000,
    "maxFeePerGas": Web3.toWei(200, "gwei"),
    "maxPriorityFeePerGas": Web3.toWei(50, "gwei"),
    "nonce": nonce + 1,
    "chainId": CHAIN_ID,
    "type": 2,
}

bundle = [
    {"signed_transaction": tx1_signed.rawTransaction},
    {"signer": sender, "transaction": tx2},
]

bundle = [
    {"signed_transaction": tx1_signed.rawTransaction},
    {"signer": sender, "transaction": tx2},
]

# keep trying to send bundle until it gets mined
while True:
    block = w3.eth.block_number
    print(f"Simulating on block {block}")
    # simulate bundle on current block
    try:
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
    print("bundleHash", w3.toHex(send_result.bundle_hash()))

    stats_v1 = w3.flashbots.get_bundle_stats(
        w3.toHex(send_result.bundle_hash()), block
    )
    print("bundleStats v1", stats_v1)

    stats_v2 = w3.flashbots.get_bundle_stats_v2(
        w3.toHex(send_result.bundle_hash()), block
    )
    print("bundleStats v2", stats_v2)

    send_result.wait()
    try:
        receipts = send_result.receipts()
        print(f"\nBundle was mined in block {receipts[0].blockNumber}\a")
        break
    except TransactionNotFound:
        print(f"Bundle not found in block {block+1}")
        # essentially a no-op but it shows that the function works
        cancel_res = w3.flashbots.cancel_bundles(replacement_uuid)
        print(f"canceled {cancel_res}")

receiverAddress = chuck
print(
    f"Sender account balance: {w3.fromWei(w3.eth.get_balance(my_account.address), 'ether')} ETH"
)
print(
    f"Receiver account balance: {w3.fromWei(w3.eth.get_balance(receiverAddress), 'ether')} ETH"
)
