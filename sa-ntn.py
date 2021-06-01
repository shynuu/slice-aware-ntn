# -*- coding: UTF-8 -*-

import argparse
import yaml
import os
import sys
import logging
import time
import numpy as np
import src.scenario as sc
import src.analyzer as analyzer
import src.builder as bld
import src.packet_analyzer as pa


logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s-%(name)s] - [%(levelname)s] - %(message)s')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Slice Aware Non Terrestrial Networks Testbed")
    main = parser.add_mutually_exclusive_group(required=True)
    main.add_argument("-g", "--generate", type=str,
                      default=None, help="Generate the named scenario", metavar=('<scenario>'))
    main.add_argument("-r", "--run", type=str,
                      default=None, help="Run the named scenario", metavar=('<scenario>'))
    main.add_argument("-a", "--analyze", type=str,
                      default=None, help="Analyze the traffic results of the named scenario", metavar=('<scenario>'))
    main.add_argument("-p", "--pull", action="store_true",
                      default=False, help="Pull the container images from docker HUB")
    main.add_argument("-u", "--push", action="store_true",
                      default=False, help="Push the container images to docker HUB (authenticated account only)")
    main.add_argument("-b", "--build", type=str, choices=["all", "amf", "smf", "ausf", "gnb", "nrf", "pcf", "smf", "trunks", "udm", "udr", "qof", "ntnqof", "ue", "upf", "classifier", "populate", "nssf", "application"],
                      default=None, help="Build the container images using local Dockerfile")

    if "-g" in [s for s in sys.argv] or "--generate" in [s for s in sys.argv]:
        parser.add_argument("--slice-aware", action="store_true", default=False,
                            help="Generate a Slice Aware Non Terrestrial Network scenario")

    if "-b" in [s for s in sys.argv] or "--build" in [s for s in sys.argv]:
        parser.add_argument("--pre-cache", action="store_true", default=False,
                            help="Don't use container cache for required containers")
        parser.add_argument("--main-cache", action="store_true",
                            default=False, help="Don't use container cache for containers")

    if "-a" in [s for s in sys.argv] or "--analyze" in [s for s in sys.argv]:
        parser.add_argument("-f", "--folder", type=str,
                            default=None, help="Specify the folder of results to parse")
        tex_options = parser.add_mutually_exclusive_group()
        tex_options.add_argument("--tikz", action="store_true",
                                 default=False, help="Output the results into a .tex file")
        tex_options.add_argument("--tex", action="store_true",
                                 default=False, help="Specify the folder of results to parse")

    args = parser.parse_args()

    if args.build != None:
        bld.build(f"{os.path.abspath(os.curdir)}/config/containers",
                  args.build, args.pre_cache, args.main_cache)
        sys.exit(0)

    if args.pull:
        bld.pull_all()
        sys.exit(0)

    if args.push:
        bld.push_all()
        sys.exit(0)

    if args.generate != None:
        path = os.path.abspath("template/scenario.yaml")
        if not os.path.isfile(path):
            logging.error(f"No file {path} found, exiting...")
            sys.exit(1)

        with open(path) as file:
            config_file = yaml.load(file, Loader=yaml.FullLoader)

        scenario = config_file.get(args.generate, None)
        if scenario == None:
            logging.error(
                f"No scenario corresponding to {scenario} found in {path}, exiting...")
            sys.exit(1)

        verificator = sc.Verificator(scenario)
        if not verificator.validate():
            logging.error("Error in the scenario configuration")
            logging.error(verificator.validation.errors)
            sys.exit(1)

        scenario = sc.Scenario(verificator.get_scenario())
        scenario.make_folders()
        scenario.prepare_scenario(True, args.slice_aware)
        scenario.build_topology(args.slice_aware)
        scenario.generate_all()
        logging.info(
            f"Scenario {scenario.name} generated. Run it using \"python3.8 sa-ntn.py -r {scenario.name}\"")

        sys.exit(0)

    if args.run != None:
        path = os.path.abspath("template/scenario.yaml")
        if not os.path.isfile(path):
            logging.error(f"No file {path} found, exiting...")
            sys.exit(1)

        with open(path) as file:
            config_file = yaml.load(file, Loader=yaml.FullLoader)

        scenario = config_file.get(args.run, None)
        if scenario == None:
            logging.error(
                f"No scenario corresponding to {scenario} found in {path}, exiting...")
            sys.exit(1)

        verificator = sc.Verificator(scenario)
        if not verificator.validate():
            logging.error("Error in the scenario configuration")
            logging.error(verificator.validation.errors)
            sys.exit(1)

        scenario = sc.Scenario(verificator.get_scenario())
        scenario.make_folders()
        scenario.prepare_scenario(True, False)
        scenario.build_topology(False)
        scenario.generate_all()

        logging.info(f"Running {scenario.name} non-slice aware scenario")
        scenario.run()

        time.sleep(5)

        scenario = sc.Scenario(verificator.get_scenario())
        scenario.prepare_scenario(True, True)
        scenario.build_topology(True)
        scenario.generate_all()

        logging.info(f"Running {scenario.name} slice aware scenario")
        scenario.run()

        sys.exit(0)

    if args.analyze != None:
        path = os.path.abspath("template/scenario.yaml")
        if not os.path.isfile(path):
            logging.error(f"No file {path} found, exiting...")
            sys.exit(1)

        with open(path) as file:
            config_file = yaml.load(file, Loader=yaml.FullLoader)

        scenario = config_file.get(args.analyze, None)
        if scenario == None:
            logging.error(
                f"No scenario corresponding to {scenario} found in {path}, exiting...")
            sys.exit(1)

        verificator = sc.Verificator(scenario)
        if not verificator.validate():
            logging.error("Error in the scenario configuration")
            logging.error(verificator.validation.errors)
            sys.exit(1)

        scenario = sc.Scenario(verificator.get_scenario())
        scenario.make_folders()
        scenario.prepare_scenario(False, False)
        analyzer.plot(scenario, args.folder, args.tikz, args.tex)
        sys.exit(0)

    # path = os.path.abspath(args.config)
    # if not os.path.isfile(path):
    #     logging.error(f"No file {path} found, exiting...")
    #     sys.exit(1)

    # with open(path) as file:
    #     config_file = yaml.load(file, Loader=yaml.FullLoader)

    # scenario = config_file.get(args.scenario, None)
    # if scenario == None:
    #     logging.error(
    #         f"No scenario corresponding to {scenario} found in {path}, exiting...")
    #     sys.exit(1)

    # verificator = sc.Verificator(scenario)
    # if not verificator.validate():
    #     logging.error("Error in the scenario configuration")
    #     logging.error(verificator.validation.errors)

    # scenario = sc.Scenario.from_conf(
    #     verificator.get_scenario(), args.interactive, args.time)
    # scenario.run()

    # an.analyse()
    # pa.read_file(os.path.abspath("http.cap"))
