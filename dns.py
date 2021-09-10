from nserver import NameServer, Response, A
from service.models import Peer
from pony import orm

ns = NameServer("seed-dns")

@ns.rule("seedaok.codepillow.io", ["A"])
def wildcard_example(query):
    response = Response()

    with orm.db_session:
        seeds = Peer.select(
            lambda p: p.visits_missed == 0
        ).random(20)

        for peer in seeds:
            response.additional.append(A(query.name, peer.address))

    return response


if __name__ == "__main__":
    ns.settings.SERVER_PORT = 9001
    ns.run()
