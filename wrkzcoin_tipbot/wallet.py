from typing import List, Dict

import sys
sys.path.append("..")
import rpc_client
from config import config


def register() -> str:
    result = rpc_client.call_method('createAddress')
    return result['address']


def send_transaction(from_address: str, to_address: str, amount: int) -> str:
    payload = {
        'addresses': [from_address],
        'transfers': [{
            "amount": amount,
            "address": to_address
        }],
        'fee': config.tx_fee,
        'anonymity': 0
    }
    result = rpc_client.call_method('sendTransaction', payload=payload)
    return result['transactionHash']

def send_transactionall(from_address: str, to_address) -> str:
    #print(to_address)
    payload = {
        'addresses': [from_address],
        'transfers': to_address,
        'fee': config.tx_fee,
        'anonymity': 1
    }
    result = rpc_client.call_method('sendTransaction', payload=payload)
    print(result)
    return result['transactionHash']

def get_wallet_balance(address: str) -> Dict[str, int]:
    result = rpc_client.call_method('getBalance', {'address': address})
    return result


def get_all_balances(wallet_addresses: List[str]) -> Dict[str, Dict]:
    wallets = {}
    for address in wallet_addresses:
        wallet = rpc_client.call_method('getBalance', {'address': address})
        wallets[address] = wallet
    return wallets
