# Based on https://github.com/justinmoon/crawler

from datetime import datetime, timedelta
from .node import Node
from . import net
from . import db
import threading
import queue
import time
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


class Worker(threading.Thread):

    def __init__(self, worker_inputs, worker_outputs, timeout):
        super().__init__()
        self.worker_inputs = worker_inputs
        self.worker_outputs = worker_outputs
        self.timeout = timeout

    def run(self):
        while True:
            # Get next node and connect
            node = self.worker_inputs.get()

            try:
                conn = Connection(node, timeout=self.timeout)
                conn.open()

            except (OSError, net.ProtocolError):
                pass

            finally:
                conn.close()

            # Report results back to the crawler
            self.worker_outputs.put(conn)


class Crawler:
    def __init__(self, num_workers=10, timeout=10):
        self.timeout = timeout
        self.worker_inputs = queue.Queue()
        self.worker_outputs = queue.Queue()
        self.workers = [
            Worker(self.worker_inputs, self.worker_outputs, timeout)
            for _ in range(num_workers)
        ]

    @property
    def batch_size(self):
        return len(self.workers) * 10

    def add_worker_inputs(self):
        nodes = db.next_nodes(self.batch_size)
        for node in nodes:
            self.worker_inputs.put(node)

    def process_worker_outputs(self):
        # Get connections from output queue
        conns = []
        while self.worker_outputs.qsize():
            conns.append(self.worker_outputs.get())

        # Flush connection outputs to DB
        db.process_crawler_outputs(conns)

    def seed_db(self):
        db.insert_nodes(net.dns_seeds())

    def main_loop(self):
        loops = 0
        while True:
            if loops % 100:
                print(f"Running crawler {loops}")

            # Fill input queue if running low
            if self.worker_inputs.qsize() < self.batch_size:
                self.add_worker_inputs()

            # Process worker outputs if running high
            if self.worker_outputs.qsize() > self.batch_size:
                self.process_worker_outputs()

            # Only check once per second
            time.sleep(1)

    def crawl(self):
        # Seed database with initial nodes from DNS seeds
        self.seed_db()

        # Add to worker inputs
        self.add_worker_inputs()

        # Start workers
        for worker in self.workers:
            worker.start()

        # Manage workers until program ends
        self.main_loop()
