from datetime import datetime

class Node:
    def __init__(self, ip, port, user_agent=None, next_visit=None, visits_missed=0):
        if next_visit is None:
            next_visit = datetime.utcnow()

        self.ip = ip
        self.port = port
        self.next_visit = next_visit
        self.visits_missed = visits_missed
        self.user_agent = user_agent

    @property
    def display(self):
        return f"{self.ip}:{self.port}"

    @property
    def address(self):
        return (self.ip, self.port)
