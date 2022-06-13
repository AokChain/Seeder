from datetime import datetime
from pony import orm
import config

db = orm.Database()
db.bind(**config.db)

class Peer(db.Entity):
    _table_ = "service_peers"

    created = orm.Required(datetime, default=datetime.utcnow)
    next_visit = orm.Required(datetime, default=datetime.utcnow)
    last_seen = orm.Required(datetime, default=datetime.utcnow)
    user_agent = orm.Optional(str, nullable=True)
    visits_missed = orm.Required(int, default=0)
    ipv4 = orm.Required(bool, default=False)
    address = orm.Required(str)
    port = orm.Required(int)

    country = orm.Optional(str, nullable=True)
    country_code = orm.Optional(str, nullable=True)
    city = orm.Optional(str, nullable=True)
    latitude = orm.Optional(float, nullable=True)
    longitude = orm.Optional(float, nullable=True)

    @property
    def plain(self):
        return f"{self.address}:{self.port}"

    @property
    def display(self):
        return {
            "last_seen": int(self.last_seen.timestamp()),
            "created": int(self.created.timestamp()),
            "user_agent": self.user_agent,
            "ipv4": self.ipv4,
            "address": self.address,
            "port": self.port,
            "country": self.country,
            "country_code": self.country_code,
            "city": self.city,
            "latitude": self.latitude,
            "longitude": self.longitude,
        }

class PeerTick(db.Entity):
    _table_ = "service_ticks"

    active = orm.Required(int, default=0)
    known = orm.Required(int, default=0)
    timestamp = orm.Required(datetime)


db.generate_mapping(create_tables=True)
