#!/usr/bin/env python3
import re
import hashlib

from salt.utils.network import mac2eui64
from textwrap import wrap
from typing import Dict, List
from pyroute2 import WireGuard, IPRoute
from pyroute2.netlink.rtnl import ndmsg
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class WireGuardClient:
    """WireGuardClient describes complete configuration for a specific WireGuard client

    Attributes:
        public_key: WireGuard Public key
        domain: Domain Name of the WireGuard peer
        lladdr: IPv6 lladdr of the WireGuard peer
        wg_interface: Name of the WireGuard interface this peer will use
        vx_interface: Name of the VXLAN interface we set a route for the lladdr to
        remove: Are we removing this peer or not?
    """

    public_key: str
    domain: str
    lladdr: str
    wg_interface: str
    vx_interface: str
    remove: bool


# we receive stuff from wgkex-broker
def generate_lladdr(public_key: str) -> str:
    m = hashlib.md5()

    m.update(public_key.encode("ascii") + b"\n")
    hashed_key = m.hexdigest()
    hash_as_list = wrap(hashed_key, 2)
    temp_mac = ":".join(["02"] + hash_as_list[:5])

    lladdr = re.sub(r"/\d+$", "/128", mac2eui64(mac=temp_mac, prefix="fe80::/10"))
    return lladdr


def generate_ifname(peer: WireGuardClient) -> WireGuardClient:
    peer.wg_interface = "wg-" + peer.domain
    peer.vx_interface = "vx-" + peer.domain

    return peer


def wg_flush_stale_peers(domain: str) -> List[Dict]:
    stale_clients = find_stale_wireguard_clients("wg-" + domain)
    result = []
    for stale_client in stale_clients:
        stale_wireguard_client = WireGuardClient(
            public_key=stale_client,
            lladdr=generate_lladdr(stale_client),
            domain=domain,
            wg_interface="",
            vx_interface="",
            remove=True,
        )
        stale_wireguard_client = generate_ifname(stale_wireguard_client)
        result = link_handler(stale_wireguard_client)
    return result


# pyroute2 stuff
def link_handler(client: WireGuardClient) -> Dict:
    results = {}

    results.update({"Wireguard": wireguard_handler(client)})
    try:
        results.update({"Route": route_handler(client)})
    except Exception as e:
        results.update({"Route": e})
    results.update({"Bridge FDB": bridge_fdb_handler(client)})

    return results


def bridge_fdb_handler(client: WireGuardClient) -> Dict:

    action = "append"
    if client.remove:
        action = "del"

    with IPRoute() as ip:
        return ip.fdb(
            action,
            ifindex=ip.link_lookup(ifname=client.vx_interface)[0],
            lladdr="00:00:00:00:00:00",
            dst=re.sub("\/\d+$", "", client.lladdr),
        )


def wireguard_handler(client: WireGuardClient) -> Dict:
    wg = WireGuard()

    wg_peer = {
        "public_key": client.public_key,
        "persistent_keepalive": 15,
        "allowed_ips": [client.lladdr],
        "remove": client.remove,
    }

    return wg.set(client.wg_interface, peer=wg_peer)


def route_handler(client: WireGuardClient) -> Dict:
    with IPRoute() as ip:
        return ip.route(
            "del" if client.remove else "add",
            dst=client.lladdr,
            oif=ip.link_lookup(ifname=client.wg_interface)[0],
        )


def find_stale_wireguard_clients(wg_interface: str) -> List:
    wg = WireGuard()

    clients = wg.info(wg_interface)[0].WGDEVICE_A_PEERS.value

    three_hours_ago = (datetime.now() - timedelta(hours=3)).timestamp()

    stale_clients = []
    for client in clients:
        latest_handshake = client.WGPEER_A_LAST_HANDSHAKE_TIME["tv_sec"]
        if latest_handshake < int(three_hours_ago):
            stale_clients.append(client.WGPEER_A_PUBLIC_KEY["value"].decode("utf-8"))

    return stale_clients
