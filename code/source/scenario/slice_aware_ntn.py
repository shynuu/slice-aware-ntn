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
import docker
import subprocess
import time
import schedule
import re
import ipaddress
import _thread
from typing import Dict, List
from . import Scenario
from ..model.slice_aware_ntn import User, Ntn, Slice, Theta, Web, Streaming, VoIP
from ..model.slice_aware_ntn import MONGO, SERVER, NRF, PCF, AUSF, AMF, SMF, UPF, NSSF, UDR, UDM, GNB, UE, QOF, POPULATE, CLASSIFIER, TRUNKS, NTNQOF

SLICES = [('1', "110101"), ("1", "110203"), ("1", "112233")]
DATA_NETWORK = ["internet", "internet2", "internet3"]
APPLICATIONS = [Web(), Streaming(), VoIP()]


class SliceAwareNTN(Scenario):
    """Slice Aware Non Terrestrial Networks Scenario"""

    scenario_type = "slice-aware"
    validation_schema = {
        'type': {'type': 'string', 'required': True},
        'duration': {'type': 'integer', 'required': True},
        'user': {'type': 'integer', 'required': True, 'min': 1, 'max': 30},
        'links': {'type': 'list', 'required': True, 'minlength': 1, 'maxlength': 2, 'schema': {
            'type': 'dict', 'schema': {
                'default': {'type': 'boolean', 'required': True, 'default': False},
                'forward': {'type': 'integer', 'required': True, 'min': 2, 'max': 1000},
                'return': {'type': 'integer', 'required': True, 'min': 2, 'max': 1000},
                'delay': {'type': 'integer', 'required': True, 'min': 20, 'max': 1000},
                'jitter': {'type': 'integer', 'required': True, 'min': 0, 'max': 100},
                'acm': {'type': 'boolean', 'required': True, 'default': True},
                'slices': {'type': 'list', 'required': True, 'minlength': 1, 'maxlength': 2, 'schema': {
                    'type': 'dict', 'schema': {
                        'start': {'type': 'integer', 'required': True},
                        'end': {'type': 'integer', 'required': True},
                        'theta': {'type': 'dict', 'required': True, 'schema': {
                            'lambda': {'type': 'integer', 'required': True, 'min': 20, 'max': 1000},
                            'delta': {'type': 'integer', 'required': True, 'min': 0, 'max': 100},
                            'mu': {'type': 'integer', 'required': True, 'min': 2, 'max': 1000},
                            'beta': {'type': 'integer', 'required': True, 'min': 0, 'max': 1000},
                            'sigma': {'type': 'boolean', 'required': True, 'default': False},
                        },
                        },
                        'applications': {'type': 'list', 'required': True, 'minlength': 1, 'maxlength': 3, 'schema': {
                            'type': 'dict', 'schema': {
                                                 'name': {'type': 'string', 'required': True, 'allowed': ['voip', 'web', 'streaming']},
                                                 'data_rate': {'type': 'integer', 'required': True, 'min': 1, 'max': 1000},
                            }
                        },
                        },
                    },
                },
                },
            }
        },
        },
    }

    def prepare_scenario(self) -> None:

        users_misc = self.repository.add_misc("users", [])
        slices_misc = self.repository.add_misc("slices", [])
        links_misc = self.repository.add_misc("links", [])
        applications_misc = self.repository.add_misc("applications", [])

        logging.info(
            f"Scenario is composed of {len(self.definition['links'])} NTN links")

        for j in range(self.definition['user']):
            users_misc.append(User())

        i = 0
        j = 0
        default_set = False
        for link in self.definition['links']:
            ntn = Ntn(link['forward'],
                      link['return'],
                      link['delay'],
                      link['jitter'],
                      link['acm'],
                      link['default']
                      )
            logging.info(
                f"NTN link {i} configuration forward link: {ntn.forward} Mbps, {ntn.retur} Mbps, {ntn.delay} ms, {ntn.jitter} ms, ACM {ntn.acm}")
            logging.info(
                f"NTN link {i} support {len(link['slices'])} slices")

            for sd in link['slices']:
                s = Slice(SLICES[j][0], SLICES[j][1],
                          DATA_NETWORK[j], sd['start'], sd['end'])
                s.theta(Theta(sd['theta']['lambda'],
                              sd['theta']['delta'],
                              sd['theta']['mu'],
                              sd['theta']['beta'],
                              sd['theta']['sigma']))

                logging.info(f"Slice {j} configuration")
                logging.info(
                    f"Management Interface configured with Theta (Θ) parameters: lambda {s.Theta.lamba} ms, delta {s.Theta.delta} ms, beta {s.Theta.beta} Mbps, mu {s.Theta.mu} Mbps, beta {s.Theta.sigma}")
                logging.info(
                    f"Data Network: {s.data_network}, SST: {s.sst}, SD: {s.sd}")

                if not default_set and ntn.default:
                    self.repository.add_misc("default_link", i)
                    self.repository.add_misc("default_slice", i)
                    default_set = True

                add = True
                for user in users_misc:
                    for application in sd['applications']:
                        if application["name"] == "web":
                            app = user.attach_application(
                                Web(data_rate=application['data_rate']))
                        elif application["name"] == "streaming":
                            app = user.attach_application(
                                Streaming(data_rate=application['data_rate']))
                        else:
                            app = user.attach_application(
                                VoIP(data_rate=application['data_rate']))
                        if add:
                            applications_misc.append(app)
                            s.applications.append(app)
                            logging.info(
                                f"Slice {j} embed Application {app.name} with a Data Rate of {app.get_data_rate()}")
                    add = False

                slices_misc.append(s)
                ntn.slices.append(s)
                j += 1
            links_misc.append(ntn)
            i += 1

        return

    def generate_networks(self) -> None:

        slices = self.repository.get_misc("slices")
        links = self.repository.get_misc("links")

        self.networker.new_network(name="sbi", pool=1)
        for i in range(len(slices)):
            self.networker.new_network(name=f"classifier-cn-dp-{i}", pool=1)
            ue_network = self.networker.new_network(
                name=f"ue-network-slice-{i}", pool=1)
            data_network = self.networker.new_network(
                name=f"data-network-slice-{i}", pool=1)
            slices[i].set_ue_network(ue_network)
            slices[i].set_data_network(data_network)

        self.networker.new_network(name="pfcp", pool=1)

        for i in range(len(links)):
            self.networker.new_network(name=f"st-classifier-{i}", pool=1)
            self.networker.new_network(name=f"gw-classifier-{i}", pool=1)

        self.networker.new_network(name="satellite-control", pool=1)
        self.networker.new_network(name="classifier-ran", pool=1)
        self.networker.new_network(name="ran-link-sim", pool=1)

    def generate_topology(self) -> None:

        slices: List[Slice] = self.repository.get_misc("slices")
        links: List[Slice] = self.repository.get_misc("links")
        users: List[User] = self.repository.get_misc("users")

        upfs_misc: List[UPF] = self.repository.add_misc("upfs", [])
        ues_misc: List[UE] = self.repository.add_misc("ues", [])
        servers_misc: Dict[int, List[SERVER]
                           ] = self.repository.add_misc("servers", {})
        classifiers_misc: List[CLASSIFIER] = self.repository.add_misc(
            "classifiers", [])
        trunks_misc: List[TRUNKS] = self.repository.add_misc(
            "trunks", [])

        mongo = self.repository.new_service("mongo", MONGO)
        mongo.attach_network("sbi", self.networker.get_address("sbi"))

        nrf = self.repository.new_service("nrf", NRF)
        nrf.attach_network("sbi", self.networker.get_address("sbi"))

        ausf = self.repository.new_service("ausf", AUSF)
        ausf.attach_network("sbi", self.networker.get_address("sbi"))

        pcf = self.repository.new_service("pcf", PCF)
        pcf.attach_network("sbi", self.networker.get_address("sbi"))

        udm = self.repository.new_service("udm", UDM)
        udm.attach_network("sbi", self.networker.get_address("sbi"))

        udr = self.repository.new_service("udr", UDR)
        udr.attach_network("sbi", self.networker.get_address("sbi"))

        smf = self.repository.new_service("smf", SMF)
        smf.attach_network("sbi", self.networker.get_address("sbi"))
        smf.attach_network("pfcp", self.networker.get_address("pfcp"))

        nssf = self.repository.new_service("nssf", NSSF)
        nssf.attach_network("sbi", self.networker.get_address("sbi"))

        amf = self.repository.new_service("amf", AMF)
        amf.attach_network("sbi", self.networker.get_address("sbi"))

        qof = self.repository.new_service("qof", QOF)
        qof.attach_network("sbi", self.networker.get_address("sbi"))

        populate = self.repository.new_service("populate", POPULATE)
        populate.attach_network("sbi", self.networker.get_address("sbi"))

        for j in range(len(slices)):
            upf = self.repository.new_service(f"upf-{j}", UPF)
            upf.attach_network("pfcp", self.networker.get_address("pfcp"))
            upf.attach_network(
                f"classifier-cn-dp-{j}", self.networker.get_address(f"classifier-cn-dp-{j}"))
            upf.attach_network(
                f"data-network-slice-{j}", self.networker.get_address(f"data-network-slice-{j}"))
            upf.attach_network(
                f"ue-network-slice-{j}", self.networker.get_address(f"ue-network-slice-{j}", 100))
            upfs_misc.append(upf)

        gnb = self.repository.new_service("gnb", GNB)
        gnb.attach_network(
            "ran-link-sim", self.networker.get_address("ran-link-sim"))
        gnb.attach_network(
            "classifier-ran", self.networker.get_address("classifier-ran"))

        for j in range(len(users)):
            ue = self.repository.new_service(f"ue-{j}", UE)
            ue.attach_network(
                "ran-link-sim", self.networker.get_address("ran-link-sim"))
            ues_misc.append(ue)
            servers_misc[j] = []

        classifier_name = ["ran", "cn"]
        for j in range(len(classifier_name)):
            classifier = self.repository.new_service(
                f"classifier-{classifier_name[j]}", CLASSIFIER)
            classifier.attach_network(
                "satellite-control", self.networker.get_address("satellite-control"))

            if classifier_name[j] == "ran":
                classifier.attach_network(
                    "classifier-ran", self.networker.get_address("classifier-ran"))
                for j in range(len(links)):
                    classifier.attach_network(
                        f"st-classifier-{j}", self.networker.get_address(f"st-classifier-{j}"))
            else:
                classifier.attach_network(
                    "sbi", self.networker.get_address("sbi"))
                for j in range(len(slices)):
                    classifier.attach_network(
                        f"classifier-cn-dp-{j}", self.networker.get_address(f"classifier-cn-dp-{j}"))
                for j in range(len(links)):
                    classifier.attach_network(
                        f"gw-classifier-{j}", self.networker.get_address(f"gw-classifier-{j}"))
            classifiers_misc.append(classifier)

        for j in range(len(links)):
            trunks = self.repository.new_service(f"trunks-{j}", TRUNKS)
            trunks.attach_network(
                f"st-classifier-{j}", self.networker.get_address(f"st-classifier-{j}"))
            trunks.attach_network(
                f"gw-classifier-{j}", self.networker.get_address(f"gw-classifier-{j}"))
            trunks_misc.append(trunks)

        ntnqof = self.repository.new_service("ntnqof", NTNQOF)
        ntnqof.attach_network(
            "satellite-control", self.networker.get_address("satellite-control"))
        ntnqof.attach_network(
            "sbi", self.networker.get_address("sbi"))

        i = 0
        for sl in slices:
            j = 0
            for ue in ues_misc:
                if sl.servers.get(j) == None:
                    sl.servers[j] = []
                for app in sl.applications:
                    server_name = f"app-server-ue-{j}-{app.name.lower()}-slice-{i}"
                    server = self.repository.new_service(server_name, SERVER)
                    server.configure_application(i, app)
                    server.attach_network(
                        f"data-network-slice-{i}", self.networker.get_address(f"data-network-slice-{i}"))
                    servers_misc[j].append(server)
                    sl.servers[j].append(server)
                j += 1
            i += 1

        return

    def get_max_duration(self, slices: List):
        m = 0
        for s in slices:
            if s.end >= m:
                m = s.end
        return m

    def run(self) -> bool:

        def start_testbed(path: str) -> None:
            cmd = f"docker-compose -f {path} up -d"
            subprocess.call(cmd, shell=True)

        def stop_testbed(path: str) -> None:
            cmd = f"docker-compose -f {path} down -v"
            subprocess.call(cmd, shell=True)

        def wait_for_configuration(client, n) -> None:
            started = False
            configured = False
            while not started:
                try:
                    for i in range(n):
                        client.containers.get(f"ue-{i}")
                    started = True
                except:
                    time.sleep(1)
            ue = client.containers.get("ue-0")
            (c, r) = ue.exec_run("ip a")
            result = r.decode('utf-8').split("\n")
            l = len(result)
            while not configured:
                (c, r) = ue.exec_run("ip a")
                result = r.decode('utf-8').split("\n")
                if len(result) > l:
                    configured = True
                time.sleep(1)

        def gather_ip(client, name: str, n: int) -> List:
            ips = []
            regex = r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}"
            ue = client.containers.get(name)
            (c, r) = ue.exec_run("ip a")
            result = r.decode('utf-8')
            matches = re.finditer(regex, result, re.MULTILINE)
            for matchNum, match in enumerate(matches, start=1):
                if matchNum > 1 and matchNum <= 1+n:
                    logging.info(f"Gathering IP for {name} {match.group()}")
                    ips.append(match.group())
            return ips

        def generate_traffic(client, k: int, slice_id: int, ue_ips: List[List[str]]) -> None:
            ue = client.containers.get(f"ue-{k}")
            e = f"bash slice-{slice_id}-app.sh {ue_ips[k][slice_id]}"
            (c, r) = ue.exec_run(e)
            result = r.decode('utf-8')
            logging.info(f"UE {k} PDU generates traffic on slice {slice_id}")

        def run_app(client, slice_id: int, ue_ips: List[List[str]]) -> None:
            logging.info(f"Generating traffic on slice {slice_id}")
            for k in range(len(ue_ips)):
                time.sleep(0.1)
                _thread.start_new_thread(
                    generate_traffic, (client, k, slice_id, ue_ips,))
            return schedule.CancelJob

        client = docker.from_env()

        slices: List[Slice] = self.repository.get_misc("slices")
        users: List[User] = self.repository.get_misc("users")

        offset: int = 5 + 0.2 * len(users)
        duration: int = self.get_max_duration(slices)

        compose_path = f"{self.repository.scenario_folder}/{self.name}/docker-compose.yaml"

        logging.info("Starting testbed...")
        start_testbed(compose_path)
        logging.info("Waiting for UE configuration...")
        wait_for_configuration(client, len(users))
        time.sleep(15)

        ue_ips: List[List[str]] = []
        n = len(slices)
        n_ue = len(users)
        for k in range(n_ue):
            time.sleep(0.2)
            ips = gather_ip(client, f"ue-{k}", n)
            if len(ips) != n:
                logging.warning(
                    f"PDU Session Establishment failed for ue-{k}, retrying scenario...")
                stop_testbed(compose_path)
                return False
            for i in range(len(ips)):
                ip_networks = self.networker.networks_name.get(
                    f"ue-network-slice-{i}")
                if ipaddress.IPv4Address(ips[i]) not in ip_networks:
                    logging.warning(
                        f"PDU Session Establishment failed for ue-{k}, retrying scenario...")
                    stop_testbed(compose_path)
                    return False
            ue_ips.append(ips)

        for k in range(n):
            schedule.every(
                offset + slices[k].start).seconds.do(run_app, client=client, slice_id=k, ue_ips=ue_ips)

        end: int = offset + duration + offset
        start = 0
        while start < end:
            schedule.run_pending()
            time.sleep(1)
            start += 1

        stop_testbed(compose_path)

        return True
