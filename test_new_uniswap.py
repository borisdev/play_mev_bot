"""
SEE https://ethereum.stackexchange.com/questions/103615/uniswap-web3-python


pip install uniswap-python
https://uniswap-python.com/getting-started.html


# Extend this to use MEV flashbots

    self._build_and_send_tx
    https://github.com/uniswap-python/uniswap-python/blob/da8c7ddd615a20203615014ab658db405d41957b/uniswap/uniswap.py#L179
    https://github.com/uniswap-python/uniswap-python/blob/da8c7ddd615a20203615014ab658db405d41957b/uniswap/uniswap.py#L1437

"""
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
import json
import time
from uniswap import Uniswap
import settings
import constants

etherscan = Etherscan(  # free plan allows 5 calls per second
    os.environ.get("ETHERSCAN_API_KEY"),
    net="main"
)

assert settings.USE_GOERLI is False
address = None          # or None if you're not going to make transactions
sender_address = address = settings.my_account.address
private_key = None  # or None if you're not going to make transactions
private_key = settings.MY_PRIVATE_KEY  # or None if you're not going to make transactions
version = 2                       # specify which version of Uniswap to use
provider = settings.PROVIDER  # can also be set through the environment variable `PROVIDER`
uniswap = Uniswap(address=address, private_key=private_key, version=version, provider=provider)

# Some token addresses we'll be using later in this guide
eth = "0x0000000000000000000000000000000000000000"
bat = "0x0D8775F648430679A709E98d2b0Cb6250d2887EF"
dai = "0x6B175474E89094C44Da98b954EedeAC495271d0F"

# Returns the amount of DAI you get for 1 ETH (10^18 wei)
amount_of_dai_per_eth = uniswap.get_price_input(eth, dai, 1)
print("amount of dai for 1 eth:", amount_of_dai_per_eth)

# Returns the amount of ETH you need to pay in wei for 1 DAI
amount_eth_per_dai = uniswap.get_price_output(eth, dai, 1)
print("amount eth for 1 dai", amount_eth_per_dai)

block = settings.w3.eth.block_number
rate = constants.dollars_per_eth
balance = settings.w3.eth.get_balance(address, block)
print("my wei balance:", balance)
print("my eth balance:", balance / 10**18)
print("my dollar balance:", balance / 10**18 * 1300)

# reconstruct contract in python
router_address = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"

with open('Uniswap_V2:_Router_2.abi') as file:
    uniswap_abi = json.load(file)

web3 = settings.w3
uniswap_contract = web3.eth.contract(address=router_address, abi=uniswap_abi)


balance = web3.eth.get_balance(sender_address)
print("This address has:", web3.fromWei(balance, "ether"), "ETH")
gas = 50000
gasPrice = 60 * (10**9)
value = int((1 / constants.dollars_per_eth) * 10**18)
total = (gas * gasPrice) + value
print("total token value trading with in dollars:", value / 10**18 * constants.dollars_per_eth)
print("total gas in dollars:", gas * gasPrice / 10**18 * constants.dollars_per_eth)
print("total needed for tx total wei:", total)
print("total needed for tx in eth:", total / 10**18)
print("total needed for tx in dollars:", total / 10**18 * rate)
token_to_buy = web3.toChecksumAddress(dai)

from dataclasses import dataclass
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
        self.address = web3.toChecksumAddress(address)
        self.contract = web3.eth.contract(
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

router = Router("DAI", dai)
# https://ethereum.stackexchange.com/questions/99890/get-balance-of-a-specific-token-in-python-using-web3-py-on-polygon-network
token = web3.eth.contract(address=dai, abi=router.get_abi(dai))  # declaring the token contract
token_balance = token.functions.balanceOf(address).call()  # returns int with balance, without decimals
print("My DAI token balance:", token_balance)
print(token.functions.name().call())
print(token.functions.symbol().call())
print(token.functions.balanceOf(address).call())
print("my address:", address)
import ipdb
ipdb.set_trace()
# specifty token to spend (WETH mainnet)
spend = web3.toChecksumAddress("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
nonce = web3.eth.getTransactionCount(sender_address)
start = time.time()  # start of the tx

# call solidity function
uniswap_tx = uniswap_contract.functions.swapExactETHForTokens(
    0, [spend, token_to_buy], sender_address, (int(time.time()) + 10000)
).build_transaction(
    {
        "from": sender_address,
        "value": value,
        "gas": gas,
        "gasPrice": gasPrice,
        "nonce": nonce,
    }
)
sign_tx = web3.eth.account.sign_transaction(
    uniswap_tx, private_key
)
tx_hash = web3.eth.send_raw_transaction(sign_tx.rawTransaction)
print(web3.toHex(tx_hash))
"""
### RESULTING OUTPUT

amount of dai for 1 eth: 1546
amount eth for 1 dai 1
my wei balance: 4921475458126492
my eth balance: 0.004921475458126492
my dollar balance: 6.39791809556444
This address has: 0.004921475458126492 ETH
total token value trading with in dollars: 1.2521600000000002e-15
total gas in dollars: 3.7564800000000003
total needed for tx total wei: 3000000000000001
total needed for tx in eth: 0.003000000000000001
total needed for tx in dollars: 3.7564800000000016
0xfd3597126985e19ec6a7fb84ed03d7e89facc02a55b97b0166bddd10441dbb2e
"""
