import redis

from threading import Thread
from typing import Dict
from redistimeseries.client import Client

from ..grafana.grafana import Grafana
from ..model import Service, Repository, CService, CEntrypoint
from ..scenario import Scenario


class Daemon(object):
    """Daemon which will run and parse probes in realtime"""

    def __init__(self, scenario: Scenario) -> None:
        self.scenario = scenario
        self.grafana: Grafana = Grafana.load_grafana("localhost:3000")
        self.redis: redis.Redis = redis.Redis(
            host='localhost', port=6379, password="secure_password")
        self.redistimeseries: Client = Client(conn=self.redis)
        self.folder = None
        self.started = False

    def initialize(self, folder):
        self.folder = folder

    def parse_slice(self, identity, n_ue):
        pass

    def start(self):

        slices = self.scenario.repository.get_misc("slices")
        n_slice = len(slices)
        n_ue = len(self.scenario.repository.get_misc("users"))
        for k in range(n_slice):
            self.parse_slice(k, n_ue)

        return None

    def stop(self):
        return None
