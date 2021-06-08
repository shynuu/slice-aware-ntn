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

import os
import shutil
import logging
import codecs
import sys
import _thread
from ruamel import yaml
from ..utils.utils import start_pcap_capture, stop_pcap_capture
from ..scenario import Scenario


class Testbed(object):
    """Generic Testbed"""

    def __init__(self, scenario: Scenario) -> None:
        self.scenario = scenario
        self.receipes = None
        self.results = None

    def generate(self):
        """Generate the testbed corresponding to the embedded scenario"""
        self.scenario.prepare_scenario()
        self.scenario.generate_networks()
        self.scenario.generate_topology()
        self.scenario.configure_services()
        self.scenario.write_configuration()
        self.scenario.configure_compose()
        self.scenario.configure_entrypoint()
        self.scenario.write_entrypoint()
        self.scenario.write_compose()

    def run(self, iteration: int, pcap: bool):
        """Run the embedded scenario on the testbed"""
        logging.info(
            f"Scenario {self.scenario.name} runs for {iteration} iterations")
        i: int = 0
        while i < iteration:
            if pcap:
                pth = f"{self.results}/capture.pcap"
                _thread.start_new_thread(start_pcap_capture, (pth,))
            logging.info(
                f"Running iteration {i} of scenario {self.scenario.name}")
            result = self.scenario.run()
            if result:
                shutil.copytree(
                    self.results, f"{self.receipes}/iteration-{i}", dirs_exist_ok=True)
                logging.info(f"End of iteration {i}")
                i += 1
            else:
                stop_pcap_capture()

    def make_receipes_folders(self, receipes_folder: str, iterations: int) -> None:
        """
        Create the receipes folders
        """

        receipes_path = f"{receipes_folder}/{self.scenario.name}"

        if os.path.exists(receipes_path):
            shutil.rmtree(receipes_path)
        os.makedirs(receipes_path)

        yam = yaml.YAML()
        yam.indent(sequence=4, offset=2)
        with codecs.open(f"{receipes_path}/iterations.yaml", "w", encoding="utf-8") as iteration_file:
            yam.dump({"iterations": iterations},  iteration_file)
        self.receipes = receipes_path

        return receipes_path

    def make_scenario_folders(self, name: str, scenario_folder: str) -> None:
        """
        Create the scenario folders
        """

        if os.path.exists(f"{scenario_folder}/{name}"):
            shutil.rmtree(f"{scenario_folder}/{name}")
        os.makedirs(f"{scenario_folder}/{name}")

        results_folder = f"{scenario_folder}/{name}/results"
        containers_folder = f"{scenario_folder}/{name}/containers"
        configurations_folder = f"{scenario_folder}/{name}/configurations"

        logging.info(f"Creating {results_folder} folder")
        os.makedirs(results_folder)

        logging.info(f"Creating {containers_folder} folder")
        os.makedirs(containers_folder)

        logging.info(f"Creating {configurations_folder} folder")
        os.makedirs(configurations_folder)

        self.results = results_folder

        return results_folder, containers_folder, configurations_folder

    def read_iterations(self, receipes_folder: str) -> int:
        """
        Read the iteration configuration file
        """

        receipes_path = f"{receipes_folder}/{self.scenario.name}"
        self.receipes = receipes_path
        if not os.path.exists(receipes_path):
            logging.error(
                f"No results for scenario {self.scenario.name} found, run the scenario first with: python3.8 run --scenario {self.scenario.name} --iterations <number of iterations>")
            sys.exit(1)

        iteration_configuration = {}
        yam = yaml.YAML()
        yam.indent(sequence=4, offset=2)

        with codecs.open(f"{receipes_path}/iterations.yaml", "r", encoding="utf-8") as iteration_file:
            iteration_configuration = yam.load(iteration_file)

        self.iterations = iteration_configuration['iterations']
        return self.iterations
