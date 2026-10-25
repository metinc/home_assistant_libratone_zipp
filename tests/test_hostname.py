"""Exercise hostname routing against the real upstream UDP hub and parser.

Only DNS, sockets and thread startup are replaced; no speaker or HA install is
needed. Loading the client modules separately avoids HA's package entry point.
"""
from collections import deque
from importlib import import_module, util
import json
from pathlib import Path
import socket
import sys
import threading
from types import ModuleType
from unittest.mock import Mock

import pytest

from python_libratone_zipp.LibratoneMessage import LibratoneMessage
from python_libratone_zipp.socket_hub import SocketHub


@pytest.fixture
def clients(monkeypatch):
    """Load the adapter and extended client without importing Home Assistant."""
    directory = Path(__file__).parents[1] / "custom_components" / "libratone_zipp"
    package_name = "_libratone_hostname_test"
    package = ModuleType(package_name)
    package.__path__ = [str(directory)]
    monkeypatch.setitem(sys.modules, package_name, package)
    loaded = {}
    for name in ("client", "extras"):
        module_name = f"{package_name}.{name}"
        spec = util.spec_from_file_location(module_name, directory / f"{name}.py")
        module = util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, module_name, module)
        spec.loader.exec_module(module)
        loaded[name] = module
    return loaded


@pytest.fixture
def hub(monkeypatch):
    """Use real IP dispatch without starting sockets or background threads."""
    hub = SocketHub.__new__(SocketHub)
    hub._devices = {}
    hub._lock = threading.Lock()
    hub._running = True
    hub._send_sock = Mock()
    library = import_module("python_libratone_zipp.LibratoneZipp")
    monkeypatch.setattr(library, "_hub_singleton", hub)
    monkeypatch.setattr(threading.Thread, "start", lambda self: None)
    return hub


def deliver(hub, address, port, command, data):
    """Feed one real protocol message through the upstream receive loop."""
    packet = LibratoneMessage(command=command, data=data).get_packet()
    incoming = deque([(packet, (address, 7777))])

    def receive(_size):
        if not incoming:
            raise OSError("End of simulated incoming packets")
        return incoming.popleft()

    receiver = Mock()
    receiver.recvfrom.side_effect = receive
    hub._rx_loop(receiver, port, port == 3333)


@pytest.mark.parametrize("client_module", ["client", "extras"])
@pytest.mark.parametrize("host", ["speaker.local", "192.168.5.11"])
@pytest.mark.parametrize("port", [3333, 7778])
def test_status_replies_reach_hostname_and_ip_clients(
    clients, hub, monkeypatch, client_module, host, port
):
    monkeypatch.setattr(socket, "gethostbyname", lambda _host: "192.168.5.11")
    module = clients[client_module]
    client_class = module.LibratoneZipp if client_module == "client" else module.ZippExtended
    client = client_class(host)

    deliver(hub, "192.168.5.11", port, 64, "37")
    assert client.volume == "37"
    assert client.host == "192.168.5.11"
    assert client.configured_host == host

    deliver(hub, "192.168.5.11", port, 5, "879")
    assert client.version == "879"

    deliver(hub, "192.168.5.11", port, 278, json.dumps({
        "play_title": "Radio station",
        "play_subtitle": "Current song",
    }))
    assert client.play_title == "Radio station"
    assert client.play_subtitle == "Current song"

    # A reply from a different speaker must not overwrite this client's state.
    deliver(hub, "192.168.5.12", port, 64, "99")
    assert client.volume == "37"

    client.exit()
    assert not hub._devices


def test_commands_target_the_resolved_address(clients, hub, monkeypatch):
    monkeypatch.setattr(socket, "gethostbyname", lambda _host: "192.168.5.11")
    client = clients["client"].LibratoneZipp("speaker.local")

    client.volume_set(23)

    packet, destination = hub._send_sock.sendto.call_args.args
    assert destination == ("192.168.5.11", 7777)
    message = LibratoneMessage(packet=packet)
    assert message.get_command_int() == 64
    assert message.data == b"23"
    client.exit()


def test_dns_failure_does_not_register_a_client(clients, hub, monkeypatch):
    resolver = Mock(side_effect=socket.gaierror("Name resolution failed"))
    monkeypatch.setattr(socket, "gethostbyname", resolver)

    with pytest.raises(socket.gaierror):
        clients["extras"].ZippExtended("missing.local")

    assert not hub._devices
    hub._send_sock.sendto.assert_not_called()


def test_reload_resolves_new_address_and_keeps_configured_hostname(
    clients, hub, monkeypatch
):
    resolver = Mock(side_effect=["192.168.5.11", "192.168.5.12"])
    monkeypatch.setattr(socket, "gethostbyname", resolver)
    old = clients["extras"].ZippExtended("speaker.local")
    old.exit()

    reloaded = clients["extras"].ZippExtended("speaker.local")
    deliver(hub, "192.168.5.12", 7778, 64, "42")

    assert reloaded.volume == "42"
    assert reloaded.host == "192.168.5.12"
    assert reloaded.configured_host == old.configured_host == "speaker.local"
    assert set(hub._devices) == {"192.168.5.12"}
    assert resolver.call_count == 2
    reloaded.exit()
