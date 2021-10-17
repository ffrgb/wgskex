import logging
import threading
import time

import pyroute2
import zmq

from wgskex.common import KexInfo, KexResult
from wgskex.worker.netlink import WireGuardClient, find_wireguard_domains, link_handler, wg_flush_stale_peers

logging.basicConfig(format="%(name)s: %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)
# TODO make loglevel configurable
logger.setLevel("DEBUG")


def flusher() -> None:
    while True:
        domains = find_wireguard_domains()
        for domain in domains:
            result = wg_flush_stale_peers(domain)
            if len(result) > 0:
                logger.debug(f"Flushed stale peers: {result}")
        time.sleep(30)


def main() -> None:
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    # TODO make the port configurable
    socket.bind("tcp://127.0.0.1:5555")

    # run background flusher to remove stale clients
    thread = threading.Thread(target=flusher)
    thread.start()

    while True:
        message = socket.recv_pyobj()

        if isinstance(message, KexInfo):
            logger.debug(f"Received object: {message!r}")

            client = WireGuardClient(public_key=message.public_key, domain=message.domain, remove=False)

            try:
                result = link_handler(client)
                logger.debug(f"Link handler: {result}")
                # TODO possible problems not handled via exception?
                socket.send_pyobj(KexResult(status="OK"))
            except pyroute2.netlink.exceptions.NetlinkError as nl_error:
                logger.warning(f"Link handler Exception: {nl_error}")
                socket.send_pyobj(KexResult(status="error", message=f"exception processing netlink update: {nl_error}"))

        else:
            logger.warning(f"Received object of unknown type: {message.__class__}")
            socket.send_pyobj(KexResult(status="error", message="received invalid request"))
