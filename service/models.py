from datetime import datetime
from pony import orm

db = orm.Database()
db.bind(provider="sqlite", filename="../seed.db", create_db=True)

class Peer(db.Entity):
    next_visit = orm.Required(datetime, default=datetime.utcnow())
    user_agent = orm.Optional(str, nullable=True)
    visits_missed = orm.Required(int, default=0)
    ipv4 = orm.Required(bool, default=False)
    address = orm.Required(str)
    port = orm.Required(int)


db.generate_mapping(create_tables=True)
