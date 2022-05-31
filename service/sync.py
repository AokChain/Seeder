from requests import Session
from .models import Peer
from pony import orm

@orm.db_session
def assign_country():
    session = Session()
    peers = Peer.select()

    for peer in peers:
        req = session.get("http://ip-api.com/json/" + peer.address).json()
        peer.country = req["country"]
        peer.country_code = req["countryCode"]
        peer.city = req["city"]
        peer.latitude = req["lat"]
        peer.longitude = req["lon"]