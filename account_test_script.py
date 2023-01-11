import os
from time import sleep
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
# network = eth_mainnet
network = eth_testnet
# *******

web3 = network.web_socket_connection()
assert web3.isConnected()
web3.middleware_onion.add(construct_sign_and_send_raw_middleware(account))


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
                # TODO: save to DB
                q.task_done()  # https://stackoverflow.com/questions/49637086/python-what-is-queue-task-done-used-for
                print("Success ...found tx_reciept: ", tx_reciept)
                import ipdb
                ipdb.set_trace()
            except TransactionNotFound:
                tx.__dict__['poll_round'] = tx.__dict__['poll_round'] + 1
                q.put(tx)
        except queue.Empty:
            sleep(.5)
            print("waiting for item to be put in the polling queue")


threading.Thread(target=tx_reciept_polling_worker, daemon=True).start()  # Turn-on the worker thread.

if network.name == "Ethereum Mainnet":
    boris = "borisdev.eth"
else:
    boris = account.address

# get the nonce.  Prevents one from sending the transaction twice
nonce = web3.eth.getTransactionCount(boris)

# build a transaction in a dictionary
tx = {
    'nonce': nonce,
    'to': chuck,
    'value': 1,
    'gas': 2000000,
    'gasPrice': web3.toWei('50', 'gwei')
}

# sign the transaction
signed_tx = web3.eth.account.sign_transaction(tx, private_key)

addresses = {
    "boris": boris,
    "chuck": chuck
}

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

# send transaction
tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
# get transaction from hash returned to caller/requestor
tx = web3.eth.getTransaction(tx_hash)
tx.__dict__['poll_round'] = 0
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
# - account amount before tx
# - account amount after tx
# - logs -- uniswap price before
# - logs -- uniswap price after


# Block main thread until all items in the queue have been gotten and processed
q.join()
print('All work completed')
