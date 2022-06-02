from datetime import datetime
from decimal import Decimal
from pony import orm

db = orm.Database()
db.bind(provider="sqlite", filename="../seed.db", create_db=True)

class Peer(db.Entity):
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



db.generate_mapping(create_tables=True)
