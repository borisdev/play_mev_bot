WARNING: THIS IS STILL IN PROGRESS !!!!!!

# A Play MEV bot


## TODO reads

- [ ] BowTiedDevil's analysis and dcoding of  Uniswap's [Introducing Permit2 & Universal Router](https://uniswap.org/blog/permit2-and-universal-router) at [Uniswap Universal Router" in substack's Degen Code](https://degencode.substack.com/p/uniswap-universal-router?utm_source=substack&publication_id=607913&post_id=106704127&utm_medium=email&triggerSave=true)
- [ ] [degenbot](https://degencode.substack.com/p/uniswap-universal-router?utm_source=substack&publication_id=607913&post_id=106704127&utm_medium=email&triggerSave=true)
  Python classes to aid rapid development of Uniswap V2 & V3 arbitrage bots on
  EVM-compatible blockchains


## Why build a MEV bot?

This is purely a learning exercise on the following blockchain topics:

- Etheruem transactions
- DEX (Uniswap)
- Smart contracts

## And why code a MEV bot in Python versus Javascript?

- mypy gives you type checks
- asyncio gives you non-blocking event loop
- help other python devs since there are fewer Python bot examples online (most are javascript)
- this is easier to intergrate with future python based data science libraries such as pandas and numpy
- python is easier for me so I can concentrate on learning about blockchain rather than learning about new syntax 


# References

- [Beginner’s guide to troubleshooting MEV on Flashbots](https://fifikobayashi.medium.com/beginners-guide-to-troubleshooting-mev-on-flashbots-aee175048858)
- [Flashbots FAQ for searchers](https://collective.flashbots.net/c/searchers/12)
- [Flashbots Discord for searchers](https://discord.com/channels/755466764501909692/795777653197635596)
- https://docs.flashbots.net/flashbots-auction/searchers/quick-start
- https://ethereum.stackexchange.com/questions/98494/how-to-create-and-send-flashbot-transactions
- [bundle-alerts channl on flashbots discord](https://discord.com/channels/755466764501909692/802054563439444010)


# Python examples

make a uniswap trade

- https://www.publish0x.com/web3dev/web3py-walkthrough-to-swap-tokens-on-uniswap-pancakeswap-ape-xqmpllz

make a flashbots bundle

- https://cryptomarketpool.com/how-to-use-flashbots/
- https://github.com/flashbots/web3-flashbots/tree/master/examples

get uniswap data

- https://cryptomarketpool.com/use-web3-py-in-python-to-call-uniswap/

# Other bot examples

- https://github.com/flashbots/simple-arbitrage
- https://github.com/duoxehyon/mev-template-go

# References

- Flashbots Bundle Explorer
- mev-job-board


# Prereqs

```
pip install etherscan-python
git clone https://github.com/flashbots/web3-flashbots 
cd 
pip3 .
```

## TODOs

- [ ] `import dbm` to store transaction traces (observability)
- [ ] `import tradingstrategy` [Trading strategy](https://github.com/tradingstrategy-ai/trading-strategy)
- [ ] `import web3_defi`
- [ ] contribute to open source by adding libraries as submodules
- [ ] Research [Awesome Crypto Trading Bots](https://github.com/botcrypto-io/awesome-crypto-trading-bots)
- [ ] Research oracles 


