import os
from enum import Enum
from time import (
    sleep,
    perf_counter)
import threading
import queue
from os.path import join, dirname
from dotenv import load_dotenv
# import polling2
from dataclasses import dataclass
from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3.middleware import construct_sign_and_send_raw_middleware
from web3.auto import Web3
from web3.exceptions import TransactionNotFound
from web3.types import TxParams, Wei
from flashbots import flashbots

USE_GOERLI = TEST = True
CHAIN_ID = 5 if USE_GOERLI else 1
USE_OLD_TX_PARAMS_SCHEMA = False

wei_per_eth = 10**18
dollars_per_eth = 1252.16


class tx_field(Enum):
    gas_price_in_dollars = "gas_price_in_dollars"


q = queue.Queue()  # inter-thread message channel

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

chuck = os.environ.get("CHUCKS_PUBLIC_ETH_ADDRESS")  # $$$$$$$$$$$$$$$$$ key
private_key = os.environ.get("PRIVATE_KEY")  # $$$$$$$$$$$$$$$$$ key
account: LocalAccount = Account.from_key(private_key)
assert private_key is not None, "You must set PRIVATE_KEY environment variable"
assert private_key.startswith("0x"), "Private key must start with 0x hex prefix"


ALCHEMY_AUTH_TOKEN = os.environ.get("ALCHEMY_AUTH_TOKEN")


@dataclass
class Network:
    """Class for keeping track of info on a web3 network."""
    name: str
    rpc_endpoint: str
    block_explorer: str

    def web_socket_connection(self):
        wss = f"wss://{self.rpc_endpoint}{ALCHEMY_AUTH_TOKEN}"
        web3 = Web3(Web3.WebsocketProvider(wss))
        return web3


eth_mainnet = Network("Ethereum Mainnet", "eth-mainnet.g.alchemy.com/v2/", "https://etherscan.io/")
eth_testnet = Network("Goerli Testnet", "eth-goerli.g.alchemy.com/v2/", "https://goerli.etherscan.io/")  # Faucet: https://goerlifaucet.com/


# *******
# TODO: make this a CLI arg
if TEST:
    network = eth_testnet
else:
    network = eth_mainnet
# *******

web3 = network.web_socket_connection()
assert web3.isConnected()
web3.middleware_onion.add(construct_sign_and_send_raw_middleware(account))


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
        print("---- debug gas ----")
        print("price in gwei:", reciept.effectiveGasPrice / 10**9)
        print("gas used:", reciept.gasUsed)
        print("gas fee in dollars:", self.gas_fee_in_dollars)
        print()


def tx_reciept_polling_worker():
    # each thread requires its own web socket connection (I think)
    web3 = network.web_socket_connection()
    assert web3.isConnected()
    while True:
        try:
            tx = q.get(block=False)  # If `False`, the program is not blocked
            try:
                print(f"polling for tx receipt round {tx['poll_round']}")
                sleep(.5)
                tx_reciept = web3.eth.getTransactionReceipt(tx.hash.hex())
                tx = dict(
                    reciept=tx_reciept,
                    meta=TxMeta(tx, tx_reciept)
                )
                # TODO: save this tx to a DB
                q.task_done()  # https://stackoverflow.com/questions/49637086/python-what-is-queue-task-done-used-for

                from pprint import pprint
                pprint(tx)
                import ipdb
                ipdb.set_trace()

            except TransactionNotFound:
                tx.__dict__['poll_round'] = tx.__dict__['poll_round'] + 1
                q.put(tx)
        except queue.Empty:
            sleep(.5)
            print("waiting for item to be put in the polling queue")


if network.name == "Ethereum Mainnet":
    boris = "borisdev.eth"
else:
    boris = account.address

# The base unit in the Ethereum protocol is wei (not Ether or gwei)
# build a transaction in a dictionary

my_gas_limit = 30000  # meansured by computational steps
my_gas_price = web3.toWei(100, 'gwei')

total_gas_liability = my_gas_limit * my_gas_price
total_gas_liability_dollars = gwei2dollars(total_gas_liability / 10**9)
print("*** total gas dollars ***:", total_gas_liability_dollars)
assert total_gas_liability_dollars < 4, "tx canceled! ...gas cost too high"

# https://web3py.readthedocs.io/en/stable/gas_price.html
# Gas price strategy is only supported for legacy transactions.
# The London fork introduced maxFeePerGas and maxPriorityFeePerGas transaction parameters which should be used over gasPrice whenever possible.

params: TxParams = {
    # 'from': boris,
    'to': chuck,
    'value': 2,  # wei
    'nonce': web3.eth.getTransactionCount(boris),  # prevents sending dupes
}

old_params_schema = dict(
    gas=my_gas_limit,
    gasPrice=my_gas_price
)

new_params_schema = dict(
    gas=my_gas_limit,  # aka computation units
    maxFeePerGas=my_gas_price,  # aka max cost per compute unit
    maxPriorityFeePerGas=10,  # aka give a tip to miner to prefer this tx over others
    chainId=CHAIN_ID,
    type=2,
)

if USE_OLD_TX_PARAMS_SCHEMA:
    params.update(old_params_schema)
else:
    params.update(new_params_schema)

signed_tx = web3.eth.account.sign_transaction(params, private_key)

addresses = {
    "boris": boris,
    "chuck": chuck
}

for name, address in addresses.items():
    wei_balance = web3.eth.getBalance(address)
    ether_balance = web3.fromWei(wei_balance, "ether")
    balance_views = {}
    balance_views = {
        "wei": wei_balance,
        # "ether by me": wei_balance / wei_per_eth,
        "ether": ether_balance,
        f"dollars @{dollars_per_eth} rate": float(ether_balance) * dollars_per_eth
    }
    print()
    print(f"{name}'s account in {network.name}")
    print("=========================")
    for k, v in balance_views.items():
        print(f"{round(v,2)} {k}")

# send transaction
tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
threading.Thread(target=tx_reciept_polling_worker, daemon=True).start()  # Turn-on the worker thread.
# get transaction from hash returned to caller/requestor
tx = web3.eth.getTransaction(tx_hash)
# add more meta data so during call back we can add even more meta data
tx.__dict__['poll_round'] = 0
tx.__dict__['tx_start_time'] = perf_counter()
tx.__dict__['start_block_number'] = web3.eth.block_number
# print("tx: ", tx)

# put item in polling work queue..waiting for transaction to be mined and then we get the receipt
q.put(tx)

for name, address in addresses.items():
    wei_per_eth = 10**18
    dollars_per_eth = 1252.16
    wei_balance = web3.eth.getBalance(address)
    ether_balance = web3.fromWei(wei_balance, "ether")
    balance_views = {}
    balance_views = {
        "wei": wei_balance,
        # "ether by me": wei_balance / wei_per_eth,
        "ether": ether_balance,
        f"dollars @{dollars_per_eth} rate": float(ether_balance) * dollars_per_eth
    }
    print()
    print(f"{name}'s account in {network.name}")
    print("=========================")
    for k, v in balance_views.items():
        print(f"{round(v,2)} {k}")


# Now you can use web3.eth.send_transaction(), Contract.functions.xxx.transact() functions
# with your local private key through middleware and you no longer get the error
# "ValueError: The method eth_sendTransaction does not exist/is not available

# https://docs.python.org/3/library/queue.html

# TODO: add new fields to tx reciept
# - time span to get transaction
# - start tx block number
# - block number
# - sender account amount before tx
# - sender account amount after tx
# - reciever account amount before tx
# - reciever account amount after tx
# - logs -- uniswap price before
# - logs -- uniswap price after


# Block main thread until all items in the queue have been gotten and processed
q.join()
print('All work completed')
