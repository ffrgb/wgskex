import logging
from typing import Dict

import zmq
from fastapi import FastAPI

from wgskex.common import KexInfo, KexResult

app = FastAPI()

context = zmq.Context()
socket = context.socket(zmq.REQ)
# TODO make the port configurable
socket.connect("tcp://localhost:5555")

# TODO make loglevel configurable
logging.basicConfig(format="%(levelname)s: %(message)s", level="DEBUG")


@app.post("/api/v1/wg/key/exchange")
def wg_key_exchange(kex_info: KexInfo) -> Dict:
    """Submit a public key to be installed into a given mesh domain"""
    logging.debug(f"Received request for domain {kex_info.domain} with public key: {kex_info.public_key}.")
    socket.send_pyobj(kex_info)
    result = socket.recv_pyobj()
    if isinstance(result, KexResult):
        return result.dict()
    else:
        return {"status": "error", "message": "received invalid response"}
