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

import logging
import argparse
import configparser
import os
import sys
import codecs
from ruamel.yaml import YAML
from source.builder.builder import Builder
from source.testbed import Selector
from source.testbed.testbed import Testbed
from source.evaluator.saw_suaw_evaluator import SSEvaluator

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s-%(name)s] - [%(levelname)s] - %(message)s')


if __name__ == "__main__":

    # Read the configuration file
    config = configparser.ConfigParser()
    config.read(os.path.abspath("configuration.conf"))

    # Define global parser and parse arguments
    parser = argparse.ArgumentParser(description="Network Testbed Launcher")
    subparsers = parser.add_subparsers(
        dest="subparser_name")

    # Configure the docker image management commands
    image_parser = subparsers.add_parser("images", help="manage docker images")
    action_options = image_parser.add_mutually_exclusive_group(required=True)
    action_options.add_argument("--pull", action="store_true",
                                default=False, help="pull the container images from docker HUB")
    action_options.add_argument("--push", action="store_true",
                                default=False, help="push the container images to docker HUB (authenticated account only)")
    action_options.add_argument("--build", type=str, default=None,
                                help="build the container images using local Dockerfile", metavar=('<image name>'))
    build_options = image_parser.add_argument_group()
    build_options.add_argument("--pre-cache", action="store_true", default=False,
                               help="add --no-cache option to docker build for required containers")
    build_options.add_argument("--main-cache", action="store_true",
                               default=False, help="add --no-cache option to docker build for mainstream containers")

    # Generate the testbed
    generate_parser = subparsers.add_parser(
        "generate", help="generate the testbed corresponding to a scenario")
    generate_parser.add_argument(
        "-s", "--scenario", nargs="*", help="Specify scenarios for the testbed generation", metavar=('<scenarios name>'), required=True)

    # Run a specific scenario
    run_parser = subparsers.add_parser(
        "run", help="generate the testbed corresponding to a scenario, run the testbed and extract probes for further evaluation")
    run_parser.add_argument("-s", "--scenario", help="Specify the scenario to run", nargs="*",
                            type=str, default=None, metavar=('<scenario name>'), required=True)
    run_parser.add_argument("-i", "--iterations", help="Run the scenario multiple times",
                            type=int, default=1, metavar=('<iteration number>'), required=False)
    run_parser.add_argument("--pcap", help="Generate a .pcap file for the testbed", action="store_true",
                            default=False, required=False)

    # Evaluate a specific scenario
    evaluate_parser = subparsers.add_parser(
        "evaluate", help="evalute the performances of two scenarios and plot results")
    evaluate_parser.add_argument("-s1", "--scenario-1", help="Specify the first scenario",
                                 type=str, default=None, metavar=('<scenario name>'), required=True)
    evaluate_parser.add_argument("-s2", "--scenario-2", help="Specify the second scenario",
                                 type=str, default=None, metavar=('<scenario name>'), required=True)
    evaluate_parser.add_argument(
        "--contribution", help="generate figure tikz code for a contribution (use tikzplotlib)", action="store_true", default=False)
    evaluate_parser.add_argument(
        "--plot", help="plot figures", action="store_true", default=False)

    args = parser.parse_args()

    if args.subparser_name == "images":
        path = os.path.abspath(config.get("images", "dockerfile"))
        b = Builder(path)

        if args.push:
            b.push_all()
            logging.info(f"All containers pushed")
            sys.exit(0)
        elif args.pull:
            b.pull_all()
            logging.info(f"All containers pulled")
            sys.exit(0)
        elif args.build:
            ok = b.repository.is_present(args.build) or args.build == "all"
            if not ok:
                logging.error(
                    f"Image {args.build} not in the repository ! I QUIT !")
                sys.exit(1)
            b.build(args.build, args.pre_cache, args.main_cache)
            sys.exit(0)

    elif args.subparser_name == "generate":

        template_folder = os.path.abspath(config.get("scenario", "template"))
        template_file = f"{template_folder}/scenario.yaml"
        scenario_folder = os.path.abspath(config.get("scenario", "scenario"))
        configuration_folder = os.path.abspath(
            config.get("services", "configuration"))
        yaml = YAML()
        if not os.path.isfile(template_file):
            logging.error(f"No file {template_file} found, exiting...")
            sys.exit(1)

        with codecs.open(template_file) as file:
            scenarios = yaml.load(file.read())

        for s in args.scenario:
            scenario_conf = scenarios.get(s, None)
            if scenario_conf != None:
                scenario = Selector.get_scenario(scenario_conf, s)
                testbed = Testbed(scenario)
                r, cont, conf = testbed.make_scenario_folders(
                    s, scenario_folder)
                scenario.set_path(
                    r, cont, configuration_folder, conf, scenario_folder)
                testbed.generate()
            else:
                logging.error(
                    f"No scenario corresponding to {s} in the template file, moving to next scenario")

        sys.exit(0)

    elif args.subparser_name == "run":

        template_folder = os.path.abspath(config.get("scenario", "template"))
        template_file = f"{template_folder}/scenario.yaml"
        scenario_folder = os.path.abspath(config.get("scenario", "scenario"))
        configuration_folder = os.path.abspath(
            config.get("services", "configuration"))
        receipes_folder = os.path.abspath(config.get("scenario", "receipes"))
        yaml = YAML()
        if not os.path.isfile(template_file):
            logging.error(f"No file {template_file} found, exiting...")
            sys.exit(1)

        with codecs.open(template_file) as file:
            scenarios = yaml.load(file.read())

        for s in args.scenario:
            scenario_conf = scenarios.get(s, None)
            if scenario_conf != None:
                scenario = Selector.get_scenario(scenario_conf, s)
                testbed = Testbed(scenario)
                r, cont, conf = testbed.make_scenario_folders(
                    s, scenario_folder)
                scenario.set_path(
                    r, cont, configuration_folder, conf, scenario_folder)
                testbed.generate()
                testbed.make_receipes_folders(receipes_folder, args.iterations)
                testbed.run(args.iterations, args.pcap)
            else:
                logging.error(
                    f"No scenario corresponding to {s} in the template file, moving to next scenario")

        sys.exit(0)

    elif args.subparser_name == "evaluate":

        template_folder = os.path.abspath(config.get("scenario", "template"))
        template_file = f"{template_folder}/scenario.yaml"
        scenario_folder = os.path.abspath(config.get("scenario", "scenario"))
        configuration_folder = os.path.abspath(
            config.get("services", "configuration"))
        receipes_folder = os.path.abspath(config.get("scenario", "receipes"))
        yaml = YAML()
        if not os.path.isfile(template_file):
            logging.error(f"No file {template_file} found, exiting...")
            sys.exit(1)

        with codecs.open(template_file) as file:
            scenarios = yaml.load(file.read())

        scenarios_to_evaluate = [args.scenario_1, args.scenario_2]
        testbeds = []

        for s in scenarios_to_evaluate:
            scenario_conf = scenarios.get(s, None)
            if scenario_conf != None:
                scenario = Selector.get_scenario(scenario_conf, s)
                testbed = Testbed(scenario)
                r, cont, conf = testbed.make_scenario_folders(
                    s, scenario_folder)
                scenario.set_path(
                    r, cont, configuration_folder, conf, scenario_folder)
                testbed.generate()
                testbed.read_iterations(receipes_folder)
                testbeds.append(testbed)
            else:
                logging.error(
                    f"No scenario corresponding to {s} in the template file, moving to next scenario")
                sys.exit(1)

        evaluator = SSEvaluator(testbeds[0], testbeds[1])
        evaluator.init_folder(receipes_folder)
        evaluator.evaluate(args.contribution, args.plot)

        sys.exit(0)

    logging.info("Nothing to do, I QUIT !")
    sys.exit(0)
