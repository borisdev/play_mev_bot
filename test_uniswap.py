"""
SEE https://ethereum.stackexchange.com/questions/103615/uniswap-web3-python


pip install uniswap-python
https://uniswap-python.com/getting-started.html


# Extend this to use MEV flashbots

    self._build_and_send_tx
    https://github.com/uniswap-python/uniswap-python/blob/da8c7ddd615a20203615014ab658db405d41957b/uniswap/uniswap.py#L179
    https://github.com/uniswap-python/uniswap-python/blob/da8c7ddd615a20203615014ab658db405d41957b/uniswap/uniswap.py#L1437

"""
import json
import time
from uniswap import Uniswap
import settings


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

import settings
import constants

block = settings.w3.eth.block_number
rate = constants.dollars_per_eth
balance = settings.w3.eth.get_balance(address, block)
print("my wei balance:", balance)
print("my eth balance:", balance / 10**18)
print("my dollar balance:", balance / 10**18 * 1300)
# uniswap.make_trade_output(dai, eth, 100)  # buy DAI for 100 Wei ETH




#try:
    # result = uniswap.make_trade(dai, eth, int((1/1300) * 10**18))  # buy 1 dollar or DAI
    # result = uniswap.make_trade(eth, dai, 5)  # buy 1 dollar or DAI
    # print(result)
    # import ipdb
    #ipdb.set_trace()
#except Exception as e:
#    print(e)


# reconstruct contract in python
router_address = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"

with open('Uniswap_V2:_Router_2.abi') as file:
    uniswap_abi = json.load(file)

web3 = settings.w3
uniswap_contract = web3.eth.contract(address=router_address, abi=uniswap_abi)


# define the sender address and prints the balance (in ETH)
# sender_address = "YOUR_ADDRESS_HERE"
# private_key = "YOUR_PRIVATE_KEY"
balance = web3.eth.get_balance(sender_address)
print("This address has:", web3.fromWei(balance, "ether"), "ETH")
gas = 2000000,
gasPrice = web3.toWei("60", "gwei")
value = 10**9
total = (gas * gasPrice) + value
print("tx total wei:", total)

# specify token to buy
# token_to_buy = web3.toChecksumAddress("TOKEN_ADDRESS")
token_to_buy = web3.toChecksumAddress(dai)

# specifty token to spend (WETH mainnet)
spend = web3.toChecksumAddress("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")

# get nonce for the sender address
nonce = web3.eth.getTransactionCount(sender_address)

start = time.time()  # start of the tx



# call solidity function
"""
- `swapExactETHForTokens` takes your ETH and returns WETH (the ERC 20 token equivalent)
- `swapExactTokensForETH` does the inverse of the above
"""
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

# sign transaction
sign_tx = web3.eth.account.sign_transaction(
    uniswap_tx, private_key
)  # use the private key to sign the transaction

# send transaction
tx_hash = web3.eth.send_raw_transaction(sign_tx.rawTransaction)

# get transaction confirmation and print hash
print(web3.toHex(tx_hash))
