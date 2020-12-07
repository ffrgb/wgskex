import logging
from typing import Dict

import zmq
from fastapi import FastAPI

from wgskex.common import KexInfo, KexResult

app = FastAPI()
context = zmq.Context()

# TODO make loglevel configurable
logging.basicConfig(format="%(levelname)s: %(message)s", level="DEBUG")


@app.post("/api/v1/wg/key/exchange")
def wg_key_exchange(kex_info: KexInfo) -> Dict:
    """Submit a public key to be installed into a given mesh domain"""
    logging.debug(f"Received request for domain {kex_info.domain} with public key: {kex_info.public_key}.")
    socket = context.socket(zmq.REQ)
    # TODO make the port configurable
    socket.connect("tcp://localhost:5555")
    socket.send_pyobj(kex_info)
    # TODO make timeout configurable
    if socket.poll(5000):
        result = socket.recv_pyobj()
        if isinstance(result, KexResult):
            return result.dict()
        else:
            logging.warning(f"received invalid response from worker: \"{result!r}\"")
            return {"status": "error", "message": "received invalid response from worker"}
    else:
        logging.warning("timeout waiting for response from worker")
        return {"status": "error", "message": "timeout waiting for response from worker"}
