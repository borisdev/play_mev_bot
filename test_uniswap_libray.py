"""
SEE https://ethereum.stackexchange.com/questions/103615/uniswap-web3-python


pip install uniswap-python
https://uniswap-python.com/getting-started.html


# Extend this to use MEV flashbots

    self._build_and_send_tx
    https://github.com/uniswap-python/uniswap-python/blob/da8c7ddd615a20203615014ab658db405d41957b/uniswap/uniswap.py#L179
    https://github.com/uniswap-python/uniswap-python/blob/da8c7ddd615a20203615014ab658db405d41957b/uniswap/uniswap.py#L1437

"""
from uniswap import Uniswap
import settings
import constants


assert settings.USE_GOERLI is False
address = None          # or None if you're not going to make transactions
sender_address = address = settings.my_account.address
private_key = None  # or None if you're not going to make transactions
private_key = settings.MY_PRIVATE_KEY  # or None if you're not going to make transactions
version = 2                       # specify which version of Uniswap to use
provider = settings.PROVIDER  # can also be set through the environment variable `PROVIDER`

## TODO: in below constructor set a custom Web3 instance for gas pricing
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
print("START ETH Balance")
print("============")
print("my ETH wei balance:", balance)
print("my ETH eth balance:", balance / 10**18)
print("my ETH dollar balance:", balance / 10**18 * 1300)

print("START DAI Balance")
print("============")
print("my DAI dollar balance:", settings.w3.eth.get_balance(dai, block))

# uniswap.make_trade_output(dai, eth, 1)  # buy DAI for 100 Wei ETH

print("Returns the amount of DAI you get for 1 ETH (10^18 wei)", uniswap.get_price_input(eth, dai, 10**18))
print("Returns the amount of DAI you get for 1 ETH (1000 wei)", uniswap.get_price_input(eth, dai, 1000))
print("Returns the amount of DAI you get for 1 ETH (10000 wei)", uniswap.get_price_input(eth, dai, 10000))
# THIS WORKS BUT SHOW NO MONEY ??
# uniswap.make_trade_output(eth, dai, 10000)  # buy DAI for 10000 Wei ETH
uniswap.make_trade_output(dai, eth, 1)  # buy ETH for 1 DAI
# print("TRANSACTION JUST RUN uniswap.make_trade_output(eth, dai, 10000)")
"""


balance = settings.w3.eth.get_balance(address)
print("RESULT ETH Balance")
print("============")
print("my ETH wei balance:", balance)
print("my ETH eth balance:", balance / 10**18)
print("my ETH dollar balance:", balance / 10**18 * 1300)
"""

print("RESULT DAI Balance")
print("============")
print("my DAI dollar balance:", settings.w3.eth.get_balance(dai))
