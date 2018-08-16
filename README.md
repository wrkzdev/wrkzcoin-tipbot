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

**Ubuntu 16**

***Compile python 3.6***
* `apt install build-essential checkinstall -y && apt install libreadline-gplv2-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev nano curl -y`
* `wget https://www.python.org/ftp/python/3.6.6/Python-3.6.6.tar.xz`
* `tar xvf Python-3.6.6.tar.xz`
* `cd Python-3.6.6/`
* `./configure`
* `make altinstall`

***Install mongodb-server***
* `apt install -y mongodb-server`

***Install pip3.6***
* `curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py`
* `python3.6m get-pip.py`

***Setup TipBot***
* `git clone https://github.com/wrkzdev/wrkzcoin-tipbot`
* `cd wrkzcoin-tipbot`
* `pip3.6 install tox pipenv click discord mongoengine yapf futures pyyaml munch requests`
* Run wrkz-service with existing wallet or new wallet and Wrkzd and note your defined ports.
* Edit `config.yml`
* Inside wrkztip-tipbot: `tox -r --notest`
* Finally run tipbot: `/usr/local/bin/python3.6m /root/wrkzdev/wrkzcoin-tipbot/wrkzcoin_tipbot/bot.py`
* Last, create discord bot and invite it to your discord server.

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
- `.stats`: Show WRKZ height, difficulty, etc.

## Local Env. Setup

This project uses `Pipfile`, `pipenv` and `tox`. To setup your environment
simply run `tox`. You can check the `tox.ini` file to see available environments
and commands that run within each of them.

## Donation
Wrkz: `WrkzRNDQDwFCBynKPc459v3LDa1gEGzG3j962tMUBko1fw9xgdaS9mNiGMgA9s1q7hS1Z8SGRVWzcGc8Sh8xsvfZ6u2wJEtoZB`

TRTL: `TRTLv2k5RgwQkcXsZpue9ELGq49PEQbgZ7sAncv82GqTc3rehKqRLM7jomrji4zek76hWiYkKKizQFfny1TvvcvyBxqnvcsTfKi`
