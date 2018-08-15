# wrkzcoin-tipbot for discord server
Based on original code: https://github.com/MarcDufresne/m0rkcoin-tip-bot

## Features:

- Deposit Wrkz.
- Tip Wrkz to Discord user.
- Check your account balance, deposit address.
- Withdraw Wrkz to your registered wallet address.
- Get WRKZ block height, network hashrate, current difficulty, circulating supply.

## Installation
**Requirements**

- MongoDB
- Wrkzd (Wrkz Daemon)
- wrkz-service (wallet daemon)
- Python 3.6
- [Discord Bot Token](https://discordapp.com/developers/applications/me)

* TODO GUIDE MORE DETAIL

## Usage
**In-discord Commands**

- `.help`: Shows help message.
- `.balance`: Check your WRKZ balance.
- `.register <wallet_address>`: Register or change your deposit address.
- `.withdraw <amount>`: Withdraw WRKZ from your balance to registered Wrkz address.
- `.tip <member> <amount>`: Give WRKZ to a user from your balance.
- `.height`: Show WRKZ current block height.
- `.hash`: Show WRKZ network hashrate.
- `.diff`: Show WRKZ current difficulty.
- `.supply`: Show WRKZ circulating supply.

## Local Env. Setup

This project uses `Pipfile`, `pipenv` and `tox`. To setup your environment
simply run `tox`. You can check the `tox.ini` file to see available environments
and commands that run within each of them.


