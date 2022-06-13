from datetime import datetime, timedelta
from datetime import datetime
from requests import Session
from .models import Peer
from .node import Node
from pony import orm
import config
import re

INTERVAL = timedelta(**config.interval)

@orm.db_session
def insert_nodes(nodes):
    for node in nodes:
        if Peer.get(address=node.ip, port=node.port):
            continue

        peer = Peer(address=node.ip, port=node.port)

        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", peer.address):
            peer.ipv4 = True

@orm.db_session
def update_nodes(nodes):
    for node in nodes:
        peer = Peer.get(address=node.ip) 
        peer.next_visit = node.next_visit
        peer.visits_missed = node.visits_missed
        peer.user_agent = node.user_agent
        peer.last_seen = datetime.utcnow()

@orm.db_session
def next_nodes():
    now = datetime.utcnow()
    peers = Peer.select(lambda p: p.next_visit < now)
    nodes = []

    for peer in peers:
        nodes.append(Node(
            peer.address, peer.port, peer.user_agent,
            peer.next_visit, peer.visits_missed
        ))

    return nodes

@orm.db_session
def process_outputs(result):
    insert_nodes_args = []
    update_nodes_args = []

    for conn in result:
        for node in conn["nodes_discovered"]:
            insert_nodes_args.append(node)

        if conn["peer_version_payload"]:
            conn["node"].next_visit = datetime.utcnow() + INTERVAL
            conn["node"].visits_missed = 0

        else:
            conn["node"].next_visit = datetime.utcnow() + (2 * conn["node"].visits_missed * INTERVAL)
            conn["node"].visits_missed += 1

        update_nodes_args.append(conn["node"])

    insert_nodes(insert_nodes_args)
    update_nodes(update_nodes_args)

@orm.db_session
def node_count():
    return Peer.select().count()

@orm.db_session
def assign_country():
    session = Session()
    peers = Peer.select(lambda p: p.country is None)

    for peer in peers:
        req = session.get("http://ip-api.com/json/" + peer.address).json()
        peer.country = req["country"]
        peer.country_code = req["countryCode"]
        peer.city = req["city"]
        peer.latitude = req["lat"]
        peer.longitude = req["lon"]
