import os
import os.path
import json
import traceback
from dataclasses import dataclass
from os.path import join, dirname
from web3.auto import Web3
from web3.exceptions import TransactionNotFound
import asyncio
from dotenv import load_dotenv
from etherscan import Etherscan
from web3.constants import WEI_PER_ETHER
import settings

assert (10**18 == WEI_PER_ETHER)

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

ALCHEMY_AUTH_TOKEN = os.environ.get("ALCHEMY_AUTH_TOKEN")
wss = f'wss://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_AUTH_TOKEN}'
node = Web3(Web3.WebsocketProvider(wss))
etherscan = Etherscan(  # free plan allows 5 calls per second
    os.environ.get("ETHERSCAN_API_KEY"),
    net="main"
)

assert node.isConnected()


@dataclass
class Router:
    """
    aka AMM
    aka Router
    makes exchanges between two token contracts at a dynamically generated price
    """
    name: str
    address: str
    abi: list
    contract: str

    def __init__(self, name: str, address: str):
        self.name = name
        self.address = node.toChecksumAddress(address)
        self.contract = node.eth.contract(
            address=self.address,
            abi=self.get_abi(self.address)
        )

    def contract_decode_tx(self, tx):
        # print the transaction and its details
        # you will be able to see the functions that are passed to the router
        # try printing the following:
        # - for function information use (decode[0])
        # - for amount in/out use decode[1]
        # - for the path use decode(['path'])
        # - for amountIn use decode('amountIn')
        # TODO: log info
        decoded = self.contract.decode_function_input(tx['input'])
        return decoded

    def get_abi(self, address):
        file_path = self.name + ".abi"
        # if abi exists then load it
        if os.path.exists(file_path):
            with open(file_path) as f:
                abi = json.load(f)
                return abi
        # if doesnt exist then fetch and save abi
        else:
            abi_json = etherscan.get_contract_abi(self.address)
            abi = json.loads(abi_json)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(abi, f, ensure_ascii=False, indent=4)
            return abi


# TODO: config yaml
routers = [
    # Router("Uniswap_V2:_Router_2", settings.uniswap_v2_router),  # depends on testnet vs mainnet
    # TODO why much less volume for V3 ???
    Router("Uniswap_V2:_Router_2", "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"),
    Router("Uniswap_V3:_Router", "0xE592427A0AEce92De3Edee1F18E0157C05861564"),
    Router("Uniswap_V3:_Router_2", "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45")
]
# "pancake_swap": '0x10ed43c718714eb63d5aa57b78b54704e256024e',  # Binance smart chain
address2router = {router.address: router for router in routers}
target_addresses = address2router.keys()

counter = 0


def handle_tx(tx):
    """
    general: event handling in event loop
    specific: callback to process the node's response of a pending transaction

    >>> swap
    {
        'amountOutMin': 2814456810484855304,
        'deadline': 1635723516,
        'path': ['0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', '0x4da08a1Bff50BE96bdeD5C7019227164b49C2bFc'],
        'to': '0x4f9CA6eff61eFf64f43FfAFe2fA3b891c10Eb128'
    }
    """
    global counter
    tx_hash = tx.hex()
    try:
        tx = node.eth.get_transaction(tx_hash)
        potential_swap_address = tx['to']
        if potential_swap_address in target_addresses:
            router = address2router[potential_swap_address]
            decoded_tx = router.contract_decode_tx(tx)
            print("====================")
            print(router.name)
            print("function called:", decoded_tx[0])
            swap = decoded_tx[1]
            try:
                min_token_out_in_dollars = swap['amountOutMin'] / WEI_PER_ETHER * 1455
                print("min_token_out_in_dollars", min_token_out_in_dollars)
            except Exception as err:
                print(err)
            from pprint import pprint
            pprint(swap)
            import ipdb
            ipdb.set_trace()
        else:
            print(f"tx count {counter} - not a target router")
            counter = counter + 1
            pass
    except TransactionNotFound:
        # TODO: why do we see error "not found"?
        # - people submit transactions with errors
        # - strangely though etherscan show these not found txs as existing but many days old
        pass
    except Exception:
        print(traceback.format_exc())
        import ipdb
        ipdb.set_trace()


async def fetch_txs_in_mempool():
    poll_interval = 1
    while True:
        for event in node.eth.filter("pending").get_new_entries():
            handle_tx(event)  # this task to process the response doesnt block the fetch task, and vice versa
        await asyncio.sleep(poll_interval)


def main():
    event_loop = asyncio.get_event_loop()  # one event loop started in one thread
    try:
        event_loop.run_until_complete(
            asyncio.gather(
                fetch_txs_in_mempool()
            )
        )

    finally:
        event_loop.close()


if __name__ == '__main__':
    main()
