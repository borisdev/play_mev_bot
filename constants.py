import decimal
from enum import Enum

wei_per_eth = 10**18
dollars_per_eth_decimal = decimal.Decimal(1252.16)
dollars_per_eth = 1252.16


class Token(Enum):
    """
    Etheruem token contract addresses
    # USD https://etherscan.io/token/0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48
    # WETH https://etherscan.io/token/0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2
    """
    USD = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
