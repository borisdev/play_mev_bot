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
from pprint import pprint
import os
from enum import Enum
from time import (
    sleep,
    perf_counter)
from os.path import join, dirname
from dotenv import load_dotenv
from dataclasses import dataclass
from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3.middleware import construct_sign_and_send_raw_middleware
from web3.auto import Web3
from web3.exceptions import TransactionNotFound
from web3.types import TxParams

USE_GOERLI_TEST = True
CHAIN_ID = 5 if USE_GOERLI_TEST else 1

wei_per_eth = 10**18
dollars_per_eth = 1252.16


class tx_field(Enum):
    gas_price_in_dollars = "gas_price_in_dollars"


dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

chuck = os.environ.get("CHUCKS_PUBLIC_ETH_ADDRESS")  # $$$$$$$$$$$$$$$$$ key
private_key = os.environ.get("PRIVATE_KEY")  # $$$$$$$$$$$$$$$$$ key
account: LocalAccount = Account.from_key(private_key)
assert private_key is not None, "You must set PRIVATE_KEY environment variable"
assert private_key.startswith("0x"), "Private key must start with 0x hex prefix"


ALCHEMY_AUTH_TOKEN = os.environ.get("ALCHEMY_AUTH_TOKEN")


@dataclass
class Blockchain:
    """Class for keeping track of info on a web3 network."""
    name: str
    rpc_endpoint: str
    block_explorer: str

    def web_socket_connection(self):
        wss = f"wss://{self.rpc_endpoint}{ALCHEMY_AUTH_TOKEN}"
        web3 = Web3(Web3.WebsocketProvider(wss))
        return web3


eth_mainnet = Blockchain("Ethereum Mainnet", "eth-mainnet.g.alchemy.com/v2/", "https://etherscan.io/")
eth_testnet = Blockchain("Goerli Testnet", "eth-goerli.g.alchemy.com/v2/", "https://goerli.etherscan.io/")  # Faucet: https://goerlifaucet.com/


# *******
if USE_GOERLI_TEST:
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
        print("success - got a response back from the network on what happened to tx request")
        print("---- debug gas ----")
        print("gas price in gwei:", reciept.effectiveGasPrice / 10**9)
        print("gas used:", reciept.gasUsed)
        print("total transaction cost - gas fee in dollars:", self.gas_fee_in_dollars)
        print()
        # TODO: persist ... in DB or log file ?


if network.name == "Ethereum Mainnet":
    boris = "borisdev.eth"
else:
    boris = account.address


my_gas_limit = 30000  # meansured by computational steps
my_gas_price = web3.toWei(100, 'gwei')

total_gas_liability = my_gas_limit * my_gas_price
total_gas_liability_dollars = gwei2dollars(total_gas_liability / 10**9)
print(" *** start new transaction ***")
print("total potential liability in gas dollars:", total_gas_liability_dollars)
assert total_gas_liability_dollars < 4, "tx canceled! ...gas cost too high"

params: TxParams = {
    'to': chuck,
    'value': 2,
    'nonce': web3.eth.getTransactionCount(boris),  # prevent dupes
    'gas': my_gas_limit,  # compute units
    'maxFeePerGas': my_gas_price,  # max price per compute unit
    'maxPriorityFeePerGas': 10,  # incentive to validator to mine this
    'chainId': CHAIN_ID,
    'type': 2,
}

signed_tx = web3.eth.account.sign_transaction(params, private_key)

bundle = [
    {"signed_transaction": signed_tx}
]

pprint(params)

print("sending transaction....")

tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)  # could have been done via middleware
tx_request = web3.eth.getTransaction(tx_hash)
tx_request.__dict__['tx_start_time'] = perf_counter()
tx_request.__dict__['start_block_number'] = web3.eth.block_number

# Polling
poll_round = 0
while True:
    try:
        tx_reciept = web3.eth.getTransactionReceipt(tx_hash.hex())
        tx = dict(
            reciept=tx_reciept,
            meta=TxMeta(tx_request, tx_reciept)
        )
        break
    except TransactionNotFound:
        print(f"polling round {poll_round} transaction to get transaction reciept...", end='\r')
        poll_round = poll_round + 1
        if poll_round > 120:
            raise Exception("reached polling time out 1m")
        sleep(.5)
