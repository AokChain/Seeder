from datetime import datetime, timedelta
from .models import Peer
from .node import Node
from pony import orm
import re

INTERVAL = timedelta(minutes=10)

@orm.db_session
def insert_nodes(nodes):
    total = 0

    for node in nodes:
        if not Peer.get(address=node.ip):
            peer = Peer(address=node.ip, port=node.port)

            if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", peer.address):
                peer.ipv4 = True

            total += 1

    print(f"Added {total} nodes")

@orm.db_session
def update_nodes(nodes):
    for node in nodes:
        peer = Peer.get(address=node.ip)
        peer.next_visit = node.next_visit
        peer.visits_missed = node.visits_missed
        peer.user_agent = node.user_agent
        peer.last_seen = datetime.utcnow()

@orm.db_session
def next_nodes(n):
    now = datetime.utcnow()
    peers = Peer.select(lambda p: p.next_visit < now).limit(n)
    nodes = []

    for peer in peers:
        nodes.append(Node(
            peer.address, peer.port, peer.user_agent,
            peer.next_visit, peer.visits_missed
        ))

    return nodes

@orm.db_session
def nodes_total():
    return Peer.select().count()

def process_crawler_outputs(conns):
    print("Updating db")
    insert_nodes_args = []
    update_nodes_args = []

    for conn in conns:
        for node in conn.nodes_discovered:
            insert_nodes_args.append(node)

        if conn.peer_version_payload:
            conn.node.next_visit = datetime.utcnow() + INTERVAL
            conn.node.visits_missed = 0

        else:
            conn.node.next_visit = datetime.utcnow() + (2 * conn.node.visits_missed * INTERVAL)
            conn.node.visits_missed += 1

        update_nodes_args.append(conn.node)

    insert_nodes(insert_nodes_args)
    update_nodes(update_nodes_args)
