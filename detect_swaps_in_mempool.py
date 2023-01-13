import os
import sys
import traceback
from os.path import join, dirname
from web3.auto import Web3
from web3.exceptions import TransactionNotFound
import asyncio
from dotenv import load_dotenv
from pancake_swap_abi import pancake_swap_abi

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

ALCHEMY_AUTH_TOKEN = os.environ.get("ALCHEMY_AUTH_TOKEN")
wss = f'wss://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_AUTH_TOKEN}'
node = Web3(Web3.WebsocketProvider(wss))

assert node.isConnected()


# add an address you want to filter pending transactions for
# make sure the address is in the correct format
target = "pancake_swap"
print(f"waiting for a pending tx to appear for {target}")
exchanges = {
    "pancake_swap": '0x10ed43c718714eb63d5aa57b78b54704e256024e'
}
router = node.toChecksumAddress(exchanges[target])
Contract = node.eth.contract(address=router, abi=pancake_swap_abi)


def handle_event(event):

    tx_hash = event.hex()  # transaction = Web3.toJSON(event).strip('"')
    try:
        transaction = node.eth.get_transaction(tx_hash)
        to = transaction['to']
        input_data = transaction['input']
        # print("pancake swap:", to == router)
        if to == router:  # pancakeswap router
            decode = Contract.decode_function_input(input_data)
            # print the transaction and its details
            # you will be able to see the functions that are passed to the router
            # try printing the following:
            # - for function information use (decode[0])
            # - for amount in/out use decode[1]
            # - for the path use decode(['path'])
            # - for amountIn use decode('amountIn')
            print(decode)
            import ipdb
            ipdb.set_trace()
            sys.exit()

        else:
            print(f"Skipping since not {target}'s router address {router}")
    except TransactionNotFound:
        # Expect to see transactions people submitted with errors
        # etherscan shows not found txs as existing but many days old
        pass
    except Exception:
        print(traceback.format_exc())
        import ipdb
        ipdb.set_trace()


async def fetch_txs_in_mempool():
    poll_interval = 2
    # filter_params = {
    #     "fromBlock": "pending",
    #     "address": router
    # }
    while True:
        # for event in node.eth.filter(filter_params).get_new_entries():
        for event in node.eth.filter("pending").get_new_entries():
            handle_event(event)  # add this to the stack of work, and keep going....not blocking
        await asyncio.sleep(poll_interval)  # let event pool controller do other work now


def main():
    # python boilerplate to make an event loop so fetching event time does not block handling event time and vice versa
    # https://medium.com/@interfacer/intro-to-async-concurrency-in-python-and-node-js-69315b1e3e36
    # https://stackoverflow.com/questions/68139555/difference-between-async-await-in-python-vs-javascript
    event_loop = asyncio.get_event_loop()
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
