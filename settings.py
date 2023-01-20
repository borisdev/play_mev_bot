import os
from os.path import join, dirname
from dotenv import load_dotenv
from eth_account import Account
from eth_account.signers.local import LocalAccount
# from web3.middleware import construct_sign_and_send_raw_middleware
from web3.auto import Web3
from flashbots import flashbot

load_dotenv(join(dirname(__file__), '.env'))

FLASHBOTS_RELAY = True  # true means send transaction bundle privately, not in pulblic mempool
USE_GOERLI = False  # True  # Test blockchain so I dont waste money
CHAIN_ID = 5 if USE_GOERLI else 1
CHUCKS_PUBLIC_ADDRESS = os.environ.get("CHUCKS_PUBLIC_ADDRESS")
ALCHEMY_AUTH_TOKEN = os.environ.get("ALCHEMY_AUTH_TOKEN")
MY_PRIVATE_KEY = os.environ.get("MY_PRIVATE_KEY")  # $$$ careful...don't push this to github
assert MY_PRIVATE_KEY is not None, "You must set PRIVATE_KEY environment variable using a local .env file"
assert MY_PRIVATE_KEY.startswith("0x"), "Private key must start with 0x hex prefix"
my_account: LocalAccount = Account.from_key(MY_PRIVATE_KEY)  # aka ETH_ACCOUNT_SIGNATURE in flashbots code

if USE_GOERLI:
    rpc_endpoint = "eth-goerli.g.alchemy.com/v2/"  # P2P network node
    w3 = Web3(Web3.WebsocketProvider(f"wss://{rpc_endpoint}{ALCHEMY_AUTH_TOKEN}"))
    assert w3.isConnected()
    flashbot(w3, my_account, "https://relay-goerli.flashbots.net")
    PROVIDER = f"https://eth-goerli.g.alchemy.com/v2/{ALCHEMY_AUTH_TOKEN}"
    # https://ethereum.stackexchange.com/questions/132880/where-to-find-uniswap-contract-addresses-on-goerli-testnet
    uniswap_v2_router = "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984"
else:
    rpc_endpoint = "eth-mainnet.g.alchemy.com/v2/"
    w3 = Web3(Web3.WebsocketProvider(f"wss://{rpc_endpoint}{ALCHEMY_AUTH_TOKEN}"))
    assert w3.isConnected()
    flashbot(w3, my_account)
    PROVIDER = f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_AUTH_TOKEN}"
    uniswap_v2_router = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
    uniswap_v3_router = "0xE592427A0AEce92De3Edee1F18E0157C05861564"
