"""
MIT License

Copyright (c) 2021 Youssouf Drif

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import logging
import sys
import codecs
from typing import Dict
from cerberus import Validator
from ruamel import yaml
from ..model import Networker, Repository, Service
from ..utils.utils import HexInt, representer


class Scenario(object):
    """Generic Scenario Interface"""

    validation_schema = None
    scenario_type = "generic"

    def __init__(self, definition: Dict) -> None:
        self.name = definition['name']
        self.definition = definition
        self.networker = Networker()
        self.repository = Repository()

    def set_path(self, results_folder: str, containers_folder: str, configurations_folder: str, output_configuration_folder: str, scenario_folder: str):
        """
        Set the path for the output folders
        """

        self.repository.results_folder = results_folder
        self.repository.containers_folder = containers_folder
        self.repository.configurations_folder = configurations_folder
        self.repository.output_configuration_folder = output_configuration_folder
        self.repository.scenario_folder = scenario_folder

    def prepare_scenario(self) -> None:
        """
        Prepare all the requirements prior to the generation of the scenario topology
        """

        logging.info(
            f"[{self.name}] prepare_scenario function undefined, I QUIT !")
        sys.exit(1)

    def generate_networks(self) -> None:
        """
        Generate the networks of the testbed
        """

        logging.info(
            f"[{self.name}] generate_networks function undefined, I QUIT !")
        sys.exit(1)

    def generate_topology(self) -> None:
        """
        Create all the services and generate the network topology of the scenario
        """

        logging.info(
            f"[{self.name}] generate_topology function undefined, I QUIT !")
        sys.exit(1)

    def configure_services(self) -> None:
        """
        Configure all the services
        """

        for service in sorted(self.repository.services):
            self.repository.services.get(service).configure(self.repository)

    def configure_compose(self) -> None:
        """
        Configure the services docker compose part
        """

        for service in sorted(self.repository.services):
            self.repository.services.get(
                service).configure_compose(self.repository)

    def configure_entrypoint(self) -> None:
        """
        Configure the services entrypoint
        """

        for service in sorted(self.repository.services):
            self.repository.services.get(
                service).configure_entrypoint(self.repository)

    def write_configuration(self) -> None:
        """
        Write the configuration files of each service
        """

        for service in sorted(self.repository.services):
            s = self.repository.services.get(service)
            s.write_configuration(self.repository.output_configuration_folder)

    def write_entrypoint(self) -> None:
        """
        Write entrypoints for each service
        """

        for service in sorted(self.repository.services):
            s: Service = self.repository.services.get(service)
            s.write_entrypoint(self.repository)

    def write_compose(self) -> None:
        """
        Write docker-compose.yaml file
        """

        output = {
            "version": "3.9",
            "services": {},
            "networks": {},
            "volumes": {"dbdata": None}
        }

        for service in sorted(self.repository.services):
            if self.repository.services[service].compose != None:
                output["services"][service] = self.repository.services[service].compose.generate()

        network_index: int = 0
        for network in sorted(self.networker.networks_name):
            output["networks"][network] = {
                "name": network,
                "driver": "bridge",
                "ipam": {
                    "driver": "default",
                    "config": [
                        {
                            "subnet": str(
                                self.networker.networks_name.get(network))
                        }
                    ]
                },
                "driver_opts":
                {
                    "com.docker.network.bridge.name": f"network-{network_index}"
                }
            }
            network_index += 1

        path: str = f"{self.repository.scenario_folder}/{self.name}/docker-compose.yaml"
        yam = yaml.YAML()
        yam.indent(sequence=4, offset=2)
        with codecs.open(path, "w", encoding="utf-8") as compose_file:
            yam.dump(output,  compose_file)

    def run(self, daemon=None) -> None:
        logging.info(f"[{self.name}] run function undefined, I QUIT !")
        sys.exit(1)

    @classmethod
    def sanitize(cls, definition: Dict, name: str, scenario: object) -> Dict:
        """
        Verify if the scenario definition is valid and sanitize accoding to the cerberus schema
        """
        if cls.validation_schema == None:
            definition['name'] = name
            return Scenario(definition)
        validator = Validator(cls.validation_schema)
        if not validator.validate(definition, cls.validation_schema):
            logging.error("Error in the scenario definition")
            logging.error(validator.errors)
            sys.exit(1)
        definition['name'] = name
        return scenario(definition)
