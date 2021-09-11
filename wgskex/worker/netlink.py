import hashlib
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from textwrap import wrap
from typing import Dict, List

from pyroute2 import IPRoute, NDB, WireGuard

from wgskex.common.utils import mac2eui64

logger = logging.getLogger(__name__)
# TODO make loglevel configurable
logger.setLevel("DEBUG")


@dataclass
class WireGuardClient:
    public_key: str
    domain: str
    remove: bool

    @property
    def lladdr(self) -> str:
        m = hashlib.md5()

        m.update(self.public_key.encode("ascii") + b"\n")
        hashed_key = m.hexdigest()
        hash_as_list = wrap(hashed_key, 2)
        temp_mac = ":".join(["02"] + hash_as_list[:5])

        lladdr = re.sub(r"/\d+$", "/128", mac2eui64(mac=temp_mac, prefix="fe80::/10"))
        return lladdr

    @property
    def vx_interface(self) -> str:
        return f"vx-{self.domain}"

    @property
    def wg_interface(self) -> str:
        return f"wg-{self.domain}"

    """WireGuardClient describes complete configuration for a specific WireGuard client

    Attributes:
        public_key: WireGuard Public key
        domain: Domain Name of the WireGuard peer
        lladdr: IPv6 lladdr of the WireGuard peer
        wg_interface: Name of the WireGuard interface this peer will use
        vx_interface: Name of the VXLAN interface we set a route for the lladdr to
        remove: Are we removing this peer or not?
    """


def wg_flush_stale_peers(domain: str) -> List[Dict]:
    stale_clients = find_stale_wireguard_clients("wg-" + domain)
    result = []
    for stale_client in stale_clients:
        stale_wireguard_client = WireGuardClient(
            public_key=stale_client,
            domain=domain,
            remove=True,
        )
        result.append(link_handler(stale_wireguard_client))
    return result


# pyroute2 stuff
def link_handler(client: WireGuardClient) -> Dict[str, Dict]:
    results = {}

    results.update({"Wireguard": wireguard_handler(client)})
    try:
        results.update({"Route": route_handler(client)})
    except Exception as e:
        results.update({"Route": {"Exception": e}})
    results.update({"Bridge FDB": bridge_fdb_handler(client)})

    return results


def bridge_fdb_handler(client: WireGuardClient) -> Dict:
    with IPRoute() as ip:
        return ip.fdb(
            "del" if client.remove else "append",
            # FIXME this list may be empty if the interface is not existing
            ifindex=ip.link_lookup(ifname=client.vx_interface)[0],
            lladdr="00:00:00:00:00:00",
            dst=re.sub(r"/\d+$", "", client.lladdr),
            nda_ifindex=ip.link_lookup(ifname=client.wg_interface)[0],
        )


def wireguard_handler(client: WireGuardClient) -> Dict:
    with WireGuard() as wg:

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


def find_wireguard_domains() -> List[str]:
    with NDB() as ndb:

        # ndb.interfaces[{"kind": "wireguard"}]] seems to trigger https://github.com/svinota/pyroute2/issues/737
        iface_values = ndb.interfaces.values()
        interfaces = [iface.get("ifname", "") for iface in iface_values if iface.get("kind", "") == "wireguard"]
        result = [iface.removeprefix("wg-") for iface in interfaces if iface.startswith("wg-")]

        return result


def find_stale_wireguard_clients(wg_interface: str) -> List[str]:
    with WireGuard() as wg:

        all_clients = []
        infos = wg.info(wg_interface)
        for info in infos:
            clients = info.get_attr("WGDEVICE_A_PEERS")
            if clients is not None:
                all_clients.extend(clients)

        three_minutes_ago = (datetime.now() - timedelta(minutes=3)).timestamp()

        stale_clients = [
            client.get_attr("WGPEER_A_PUBLIC_KEY").decode("utf-8")
            for client in all_clients
            # TODO add never connected peers to a list and remove them on next call
            if 0 < client.get_attr("WGPEER_A_LAST_HANDSHAKE_TIME").get("tv_sec", int()) < three_minutes_ago
        ]

        return stale_clients
