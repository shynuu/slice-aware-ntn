"""
Copyright (c) 2021 Youssouf Drif

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from ..utils.utils import HexInt, representer
from typing import Dict, List
from ruamel import yaml
import codecs
import ipaddress
import os
import logging
import sys


class Repository(object):
    """Repository holds all the necessarily informations"""

    def __init__(self) -> None:
        self.services = {}
        self.miscs = {}
        self.results_folder = None
        self.containers_folder = None
        self.configurations_folder = None
        self.output_configuration_folder = None
        self.scenario_folder = None

    def add_service(self, name: str, service: object) -> object:
        self.services[name] = service
        return service

    def get_service(self, name) -> object:
        return self.services.get(name)

    def add_misc(self, name: str, misc: object) -> object:
        self.miscs[name] = misc
        return misc

    def get_misc(self, name: str) -> object:
        return self.miscs.get(name)

    def new_service(self, name: str, service: object) -> object:
        o = service(name, self)
        self.services[name] = o
        return o


class Service(object):
    """Service class"""

    configuration_file = None
    docker_image = None

    def __init__(self, name: str, repository: Repository) -> None:
        self.name = name
        self.networks: Dict[str, ipaddress.IPv4Address] = {}
        self.compose = None
        self.entrypoint = None

        if self.configuration_file != None:
            path = f"{repository.configurations_folder}/{self.configuration_file}"
            with codecs.open(path, mode="r", encoding="utf8") as f:
                self.configuration = yaml.load(
                    f.read(), Loader=yaml.RoundTripLoader)

    def attach_network(self, name: str, address: ipaddress.IPv4Address):
        """Add a network address to the service"""
        self.networks[name] = address

    def write_configuration(self, folder_path: str) -> None:
        """
        Write the configuration file of the service
        """

        if self.configuration_file != None:
            path = f"{folder_path}/{self.name}.yaml"
            yam = yaml.YAML()
            yam.indent(sequence=4, offset=2)
            with codecs.open(path, "w", encoding="utf-8") as configuration:
                yam.representer.add_representer(HexInt, representer)
                yam.dump(self.configuration, configuration)

    def configure(self, repository: Repository) -> None:
        """Configure the service"""
        logging.error(
            f"{self.name} service function configure not implemented, I QUIT !")
        sys.exit(1)

    def configure_compose(self, repository: Repository) -> None:
        """Configure the service docker compose"""
        logging.error(
            f"{self.name} service function configure_compose not implemented, I QUIT !")
        sys.exit(1)

    def configure_entrypoint(self, repository: Repository) -> None:
        """Configure the entrypoint if necessarily"""
        if self.compose.entrypoint != None:
            logging.error(
                f"{self.name} service function configure_entrypoint not implemented, I QUIT !")
            sys.exit(1)

    def write_entrypoint(self, repository: Repository) -> None:
        """Write the entrypoint if necessarily"""
        if self.entrypoint != None:
            self.entrypoint.write(repository.containers_folder, self.name)


class Networker(object):
    """Networker generates networks corresponding to RFC 1918 or custom networks"""

    def __init__(self, custom: List[str] = None) -> None:
        if custom != None and len(custom) > 0:
            self.pools: List[List[ipaddress.IPv4Network]] = [list(ipaddress.ip_interface(
                a).network.subnets(new_prefix=24)) for a in custom]
            self.pool_index: List[int] = [0 for j in range(self.pools)]
            return
        self.pools: List[List[ipaddress.IPv4Network]] = [list(ipaddress.ip_interface(
            a).network.subnets(new_prefix=24)) for a in ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]]
        self.pool_index: List[int] = [0, 0, 0]
        self.networks: Dict[ipaddress.IPv4Network, int] = {}
        self.networks_name: Dict[str, ipaddress.IPv4Network] = {}

    def new_network(self, name: str = None, pool: int = 0) -> ipaddress.IPv4Network:
        """Return the first available network belonging to `pool`"""
        network = self.pools[pool][self.pool_index[pool]]
        self.pool_index[pool] += 1
        self.networks[network] = 0
        if name == None:
            name = str(len(self.networks_name))
        if name in self.networks_name:
            logging.error(f"Network name {name} already defined, I QUIT !")
            sys.exit(1)
        self.networks_name[name] = network
        return network

    def get_address(self, name: str, index=None) -> ipaddress.IPv4Address:
        """Return the first available network address of network `name`"""
        network = self.networks_name[name]
        self.networks[network] += 1
        hosts = list(network.hosts())
        if index != None:
            return hosts[index]
        address = hosts[self.networks[network]]
        return address

    def get_address_from_network(self, network: ipaddress.IPv4Network) -> ipaddress.IPv4Address:
        """Return the first available network address of `network`"""
        self.networks[network] += 1
        hosts = list(network.hosts())
        address = hosts[self.networks[network]]
        return address


class CEntrypoint(object):
    """Docker bash script entrypoint class"""

    def __init__(self, name) -> None:
        self.name = name
        self.entrypoint = ["#!/bin/bash"]

    def add_line(self, line: str) -> None:
        self.entrypoint.append(line)

    def add_multiple_lines(self, lines: List[str]) -> None:
        self.entrypoint.extend(lines)

    def write(self, path: str, name: str) -> None:
        """Write the entrypoint bash script to the specified `path`"""

        path = f"{path}/{name}.sh"
        with codecs.open(path, "w", encoding="utf-8") as entrypoint:
            entrypoint.write(str(self))
        os.chmod(path, 0o777)

    def __str__(self) -> str:
        return "\n".join(self.entrypoint)

    @classmethod
    def New(cls):
        return CEntrypoint("entrypoint")


class CService(object):
    """Docker compose service class"""

    def __init__(self, name: str) -> None:
        self.name: str = name
        self.tty: bool = None
        self.container_name: str = name
        self.build_context: str = None
        self.build_args: Dict[str, str] = None
        self.image: str = None
        self.ports: List[str] = None
        self.entrypoint: str = None
        self.command: str = None
        self.expose: List[str] = None
        self.volumes: List[str] = None
        self.cap_add: List[str] = None
        self.devices: List[str] = None
        self.environment: Dict[str, str] = None
        self.networks: Dict[str, ipaddress.IPv4Address] = None
        self.depends_on: List[str] = None

    def generate(self):
        """Generate the dict corresponding to the service compose yaml"""

        self.configuration = {}

        if self.tty != None:
            self.configuration["tty"] = self.tty

        if self.container_name != None:
            self.configuration["container_name"] = self.container_name

        if self.build_context != None:
            self.configuration["build"] = {"context": self.build_context}

        if self.build_args != None:
            self.configuration['build']['args'] = self.build_args

        if self.image != None:
            self.configuration['image'] = self.image

        if self.ports != None:
            self.configuration['ports'] = [port for port in self.ports]

        if self.entrypoint != None:
            self.configuration['entrypoint'] = self.entrypoint

        if self.command != None:
            self.configuration['command'] = self.command

        if self.expose != None:
            self.configuration['expose'] = self.expose

        if self.volumes != None:
            self.configuration['volumes'] = self.volumes

        if self.cap_add != None:
            self.configuration["cap_add"] = self.cap_add

        if self.devices != None:
            self.configuration["devices"] = self.devices

        if self.environment != None:
            self.configuration["environment"] = self.environment

        if self.networks != None:
            self.configuration["networks"] = {}
            for network_name, network_address in self.networks.items():
                self.configuration["networks"][network_name] = {
                    "ipv4_address": str(network_address)}

        if self.depends_on != None:
            self.configuration["depends_on"] = self.depends_on

        return self.configuration

    @classmethod
    def New(cls, name: str, image: str) -> object:
        """`custom` constructor with image"""

        cs = CService(name)
        cs.image = image
        return cs


# class Model(object):

#     name = "model"
#     config = "model"

#     pass
