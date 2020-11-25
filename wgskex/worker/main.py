import logging

import pyroute2
import zmq

from wgskex.common import KexInfo, KexResult
from wgskex.worker.netlink import WireGuardClient, link_handler

# TODO make loglevel configurable
logging.basicConfig(format="%(levelname)s: %(message)s", level="DEBUG")


def main() -> None:
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    # TODO make the port configurable
    socket.bind("tcp://*:5555")

    while True:
        message = socket.recv_pyobj()

        if isinstance(message, KexInfo):
            logging.debug(f"Received object: {message!r}")

            client = WireGuardClient(public_key=message.public_key, domain=message.domain, remove=False)

            try:
                result = link_handler(client)
                logging.debug(f"Link handler: {result}")
                # TODO possible problems not handled via exception?
                socket.send_pyobj(KexResult(status="OK"))
            except pyroute2.netlink.exceptions.NetlinkError as nl_error:
                socket.send_pyobj(KexResult(status="error", message=f"exception processing netlink update: {nl_error}"))

        else:
            logging.warning(f"Received object of unknown type: {message.__class__}")
            socket.send_pyobj(KexResult(status="error", message="received invalid request"))
