from datetime import datetime, timedelta
from .node import Node
from . import net
import io

class Connection:
    def __init__(self, node, timeout):
        self.node = node
        self.timeout = timeout
        self.sock = None
        self.stream = None
        self.start = None

        # Results
        self.peer_version_payload = None
        self.nodes_discovered = []

    def send_version(self):
        payload = net.serialize_version_payload()
        msg = net.serialize_msg(command=b"version", payload=payload)
        self.sock.sendall(msg)

    def send_verack(self):
        msg = net.serialize_msg(command=b"verack")
        self.sock.sendall(msg)

    def send_pong(self, payload):
        res = net.serialize_msg(command=b"pong", payload=payload)
        self.sock.sendall(res)

    def send_getaddr(self):
        self.sock.sendall(net.serialize_msg(b"getaddr"))

    def handle_version(self, payload):
        # Save their version payload
        stream = io.BytesIO(payload)
        self.peer_version_payload = net.read_version_payload(stream)
        self.node.user_agent = self.peer_version_payload["user_agent"].decode("utf-8")

        # Acknowledge
        self.send_verack()

    def handle_verack(self, payload):
        # Request peer"s peers
        self.send_getaddr()

    def handle_ping(self, payload):
        self.send_pong(payload)

    def handle_addr(self, payload):
        payload = net.read_addr_payload(io.BytesIO(payload))
        if len(payload["addresses"]) > 1:
            self.nodes_discovered = [
                Node(a["ip"], a["port"]) for a in payload["addresses"]
            ]

    def handle_msg(self):
        msg = net.read_msg(self.stream)
        command = msg["command"].decode()
        method_name = f"handle_{command}"
        if hasattr(self, method_name):
            getattr(self, method_name)(msg["payload"])

    def remain_alive(self):
        timed_out = datetime.utcnow() - self.start > timedelta(seconds=self.timeout)
        return not timed_out and not self.nodes_discovered

    def open(self):
        # Set start time
        self.start = datetime.utcnow()

        # Open TCP connection
        self.sock = net.create_connection(self.node.address,
                                          timeout=self.timeout)
        self.stream = self.sock.makefile("rb")

        # Start version handshake
        self.send_version()

        # Handle messages until program exists
        while self.remain_alive():
            self.handle_msg()

    def close(self):
        # Clean up socket"s file descriptor
        if self.sock:
            self.sock.close()
