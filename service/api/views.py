from webargs.flaskparser import use_args
from flask import make_response
from datetime import datetime
from .args import filter_args
from ..models import PeerTick
from flask import Blueprint
from ..models import Peer
from pony import orm

blueprint = Blueprint("api", __name__)

@blueprint.route("/peers")
@orm.db_session
def peers():
    result = {"error": None, "result": []}

    peers = Peer.select(
        lambda p: p.user_agent is not None and p.visits_missed < 3
    )

    for peer in peers:
        result["result"].append(peer.display)
    
    return result

@blueprint.route("/peers/plain")
@orm.db_session
def peers_plain():
    result = ""

    peers = Peer.select(
        lambda p: p.user_agent is not None and p.visits_missed < 3
    )

    for peer in peers:
        result += peer.plain
        result += "\n"
    
    response = make_response(result, 200)
    response.mimetype = "text/plain"

    return response

@blueprint.route("/stats")
@orm.db_session
def stats():
    known = Peer.select().count()

    active = Peer.select(
        lambda p: p.user_agent is not None and p.visits_missed < 3
    ).count()

    countries_group = orm.select(
        (p.country_code, orm.count(p)) for p in Peer
        if p.user_agent is not None and p.visits_missed < 3
    ).order_by(orm.desc(2))

    countries = {}

    for country in countries_group:
        countries[country[0]] = country[1]

    change_24h_active = 0
    change_24h_known = 0

    ticks = PeerTick.select().order_by(
        lambda t: orm.desc(t.timestamp)
    ).limit(2)

    if len(ticks) == 2:
        change_24h_active = ticks[0].active - ticks[1].active
        change_24h_known = ticks[0].known - ticks[1].known

    return {"error": None, "result": {
        "countries": countries,
        "active": active,
        "known": known,
        "change": {
            "active": change_24h_active,
            "known": change_24h_known
        }
    }}

@blueprint.route("/chart")
@use_args(filter_args, location="query")
@orm.db_session
def chart(args):
    result = {"error": None, "result": []}

    ticks = PeerTick.select().order_by(
        lambda t: orm.desc(t.timestamp)
    )

    if args["after"]:
        ticks = ticks.filter(
            lambda t: t.timestamp < datetime.fromtimestamp(args["after"])
        )
    
    ticks = ticks.limit(30)

    for tick in ticks:
        result["result"].append({
            "timestamp": int(tick.timestamp.timestamp()),
            "active": tick.active,
            "known": tick.known
        })
    
    return result
