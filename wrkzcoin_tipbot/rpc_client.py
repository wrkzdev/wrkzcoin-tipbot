from typing import Dict
from uuid import uuid4

import requests

import sys
sys.path.append("..")
from config import config

class RPCException(Exception):
    def __init__(self, message):
        super(RPCException, self).__init__(message)


def call_method(method_name: str, payload: Dict = None) -> Dict:
    full_payload = {
        'params': payload or {},
        'jsonrpc': '2.0',
        'id': str(uuid4()),
        'method': f'{method_name}'
    }
    resp = requests.post(
        f'http://{config.wallet.host}:{config.wallet.port}/json_rpc',
        json=full_payload)
    resp.raise_for_status()
    json_resp = resp.json()
    if 'error' in json_resp:
        raise RPCException(json_resp['error'])
    return resp.json().get('result', {})
