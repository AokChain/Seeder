from .connection import Connection
from multiprocessing import Pool
from .net import ProtocolError
from .net import init_db
from . import utils

def process_node(node):
    print(f"Connecting to {node.display}")
    conn = Connection(node, timeout=5)

    try:
        conn.open()

    except (OSError, ProtocolError):
        pass

    finally:
        conn.close()

    return {
        "peer_version_payload": conn.peer_version_payload,
        "nodes_discovered": conn.nodes_discovered,
        "node": conn.node
    }

def crawl_nodes():
    if utils.node_count() == 0:
        utils.insert_nodes(init_db())

    with Pool(10) as p:
        result = p.map(process_node, utils.next_nodes())

    utils.process_outputs(result)
    utils.assign_country()
