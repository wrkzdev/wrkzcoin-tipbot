from typing import Dict
from uuid import uuid4

import requests

import sys
sys.path.append("..")
from config import config

class RPCException(Exception):
    def __init__(self, message):
        super(RPCException, self).__init__(message)

def call_get() -> Dict:
    resp = requests.get(f'http://{config.daemon.host}:{config.daemon.port}/getinfo')
    resp.raise_for_status()
    json_resp = resp.json()
    if 'error' in json_resp:
        raise RPCException(json_resp['error'])
    return resp.json()

def call_method(method_name: str, payload: Dict = None) -> Dict:
    full_payload = {
        'params': payload or {},
        'jsonrpc': '2.0',
        'id': str(uuid4()),
        'method': f'{method_name}'
    }
    resp = requests.post(
        f'http://{config.daemon.host}:{config.daemon.port}/json_rpc',
        json=full_payload)
    resp.raise_for_status()
    json_resp = resp.json()
    if 'error' in json_resp:
        raise RPCException(json_resp['error'])
    return resp.json().get('result', {})

def getheight() -> int:
    result = call_get()
    return "{:,}".format(result['height'])

def gethashrate() -> str:
    result = call_get()
    return hhashes(int(result['hashrate']))

def getdiff() -> int:
    result = call_get()
    return "{:,}".format(result['difficulty'])

def getsupply() -> str:
    data = call_method('getlastblockheader')
    last_block_hash = data['block_header']['hash']
    result = call_method('f_block_json', {'hash': last_block_hash})
    block = result['block']
    return "{:,}".format(int(block['alreadyGeneratedCoins'])/100)

def hhashes(num) -> str:
    for x in ['H/s','KH/s','MH/s','GH/s']:
        if num < 1000.0:
            return "%3.1f%s" % (num, x)
        num /= 1000.0
    return "%3.1f%s" % (num, 'TH/s')
