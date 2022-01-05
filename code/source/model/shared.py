from . import Service, Repository, CService, CEntrypoint
from ..utils.utils import HexInt, representer, find_network


class GRAFANA(Service):

    docker_image = "grafana/grafana-enterprise"

    def configure(self, repository: Repository) -> None:
        """Configure the GRAFANA service"""
        pass

    def configure_compose(self, repository: Repository) -> None:
        """Add a Compose configuration to the GRAFANA Service"""

        compose: CService = CService.New(self.name, self.docker_image)
        compose.networks = self.networks
        compose.ports = ["3000:3000"]
        compose.environment = {
            "GF_INSTALL_PLUGINS": "redis-datasource",
            "GF_SECURITY_ADMIN_USER": "admin",
            "GF_SECURITY_ADMIN_PASSWORD": "admin"
        }
        self.compose = compose


class REDIS(Service):

    docker_image = "redislabs/redistimeseries:edge"

    def configure(self, repository: Repository) -> None:
        """Configure the REDIS service"""
        pass

    def configure_compose(self, repository: Repository) -> None:
        """Add a Compose configuration to the REDIS Service"""

        compose: CService = CService.New(self.name, self.docker_image)
        compose.networks = self.networks
        compose.command = "redis-server --requirepass secure_password --loadmodule /usr/lib/redis/modules/redistimeseries.so"
        compose.ports = ["6379:6379"]
        compose.environment = {
            "REDIS_REPLICATION_MODE": "master"
        }
        self.compose = compose
