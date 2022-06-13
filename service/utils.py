from datetime import datetime, timedelta
from .crawler.node import Node
from datetime import datetime
from requests import Session
from .models import PeerTick
from .models import Peer
from pony import orm
import config
import re

INTERVAL = timedelta(**config.interval)

def round_day(created):
    return created - timedelta(
        days=created.day % 1,
        hours=created.hour,
        minutes=created.minute,
        seconds=created.second,
        microseconds=created.microsecond
    )

@orm.db_session
def build_chart():
    timestamp = round_day(datetime.utcnow())

    if not (tick := PeerTick.get(timestamp=timestamp)):
        tick = PeerTick(timestamp=timestamp)

    tick.known = Peer.select().count()
    tick.active = Peer.select(
        lambda p: p.user_agent is not None and p.visits_missed < 3
    ).count()

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
            conn["node"].visits_missed = 0
            conn["node"].next_visit = datetime.utcnow() + INTERVAL

        else:
            conn["node"].visits_missed += 1
            conn["node"].next_visit = datetime.utcnow() + (
                2 * conn["node"].visits_missed * INTERVAL
            )

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
        print(f"Looking up country of {peer.address}")
        req = session.get("https://geolocation-db.com/json/" + peer.address).json()
        peer.country = req["country_name"]
        peer.country_code = req["country_code"]
        peer.city = req["city"]
        peer.latitude = req["latitude"]
        peer.longitude = req["longitude"]
