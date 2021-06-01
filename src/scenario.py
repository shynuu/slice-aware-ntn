from typing import List, Dict
from cerberus import Validator
import logging
import os
import ipaddress
import schedule
import codecs
import shutil
import time
from ruamel import yaml
from .models import (Service, AMF, AUSF, NRF, UPF, SMF, UDR, UDM, PCF, NSSF, TRUNKS, MONGO, GNB, CLASSIFIER,
                     UE, QOF, NTNQOF, POPULATE, SERVER, Network, Slice, User, Web, VoIP, Streaming, Ntn, Theta, init_index)
from . import runner

SLICES = [('1', "110101"), ("1", "110203"), ("1", "112233")]
DATA_NETWORK = ["internet", "internet2", "internet3"]
APPLICATIONS = [Web(True), Streaming(True), VoIP(True)]


class Verificator(object):
    """
    Verify if the scenario is correctly defined
    """

    schema = {
        'scenario': {'type': 'dict', 'schema':
                     {
                         'name': {'type': 'string', 'required': True},
                         'user': {'type': 'integer', 'required': True, 'min': 1, 'max': 10},
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
                     }
    }

    def __init__(self, configuration):
        self.configuration = {'scenario': configuration}
        self.validation = Validator(self.schema)

    def validate(self):
        """
        Verify if the scenario configuration is valid
        """
        return self.validation.validate(self.configuration, self.schema)

    def get_scenario(self):
        """
        Return the validated scenario
        """
        return self.configuration['scenario']


class Scenario(object):
    """
    Scenario base class. Build the scenario topology and configure the components of the testbed
    """

    def __init__(self, conf):
        self.name = conf['name']
        self.configuration = conf
        self.networks: Dict[str, Network] = {}
        self.services: Dict[str, Service] = {}

        self.users: List[User] = []
        self.slices = []
        self.default_slice = None
        self.default_link = None
        self.links = []
        self.applications = []
        self.ues: List[UE]
        self.servers: Dict[int, List[SERVER]] = {}
        self.slice_aware = False

    def make_folders(self):
        """
        Create the required folders for the scenario
        """

        name = self.name

        if os.path.exists(f"scenarios/{name}"):
            shutil.rmtree(f"scenarios/{name}")

        if not os.path.exists(f"scenarios/{name}/results-sa"):
            logging.info(f"Creating scenarios/{name}/results-sa folder")
            os.makedirs(f"scenarios/{name}/results-sa")

        if not os.path.exists(f"scenarios/{name}/results-non-sa"):
            logging.info(f"Creating scenarios/{name}/results-non-sa folder")
            os.makedirs(f"scenarios/{name}/results-non-sa")

        if not os.path.exists(f"scenarios/{name}/containers"):
            logging.info(f"Creating scenarios/{name}/containers folder")
            os.makedirs(f"scenarios/{name}/containers")

        if not os.path.exists(f"scenarios/{name}/configuration"):
            logging.info(f"Creating scenarios/{name}/configuration folder")
            os.makedirs(f"scenarios/{name}/configuration")

    def prepare_scenario(self, generate, slice_aware: bool):
        """
        Prepare all the requirements prior to the generation of the scenario topology
        """

        if generate:
            logging.info(
                f"Scenario is compose of {len(self.configuration['links'])} NTN links")

        for j in range(self.configuration['user']):
            self.users.append(User())

        i = 0
        j = 0
        default_set = False
        for link in self.configuration['links']:
            ntn = Ntn(link['forward'],
                      link['return'],
                      link['delay'],
                      link['jitter'],
                      link['acm'],
                      link['default']
                      )
            if generate:
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
                if generate:
                    logging.info(f"Slice {j} configuration")
                    logging.info(
                        f"Management Interface configured with Theta (Θ) parameters: lambda {s.Theta.lamba} ms, delta {s.Theta.delta} ms, beta {s.Theta.beta} Mbps, mu {s.Theta.mu} Mbps, beta {s.Theta.sigma}")
                    logging.info(
                        f"Data Network: {s.data_network}, SST: {s.sst}, SD: {s.sd}")

                if not default_set and ntn.default:
                    self.default_link = i
                    self.default_slice = j
                    default_set = True

                add = True
                for user in self.users:
                    for application in sd['applications']:
                        if application["name"] == "web":
                            app = user.attach_application(
                                Web(slice_aware, data_rate=application['data_rate']))
                        elif application["name"] == "streaming":
                            app = user.attach_application(
                                Streaming(slice_aware, data_rate=application['data_rate']))
                        else:
                            app = user.attach_application(
                                VoIP(slice_aware, data_rate=application['data_rate']))
                        if add:
                            self.applications.append(app)
                            s.applications.append(app)
                            if generate:
                                logging.info(
                                    f"Slice {j} embed Application {app.name} with a Data Rate of {app.get_data_rate()}")
                    add = False

                self.slices.append(s)
                ntn.slices.append(s)
                j += 1
            self.links.append(ntn)
            i += 1

    def build_services(self, slice_aware: bool):
        """
        Generate all the components of the scenario
        """

        self.slice_aware = slice_aware

        # Build the 5G Core Network
        mongo = MONGO("mongo")
        mongo_net = mongo.configure(self.networks['core-network-cp'])
        self.services[mongo.name] = mongo

        nrf = NRF("nrf")
        nrf_net = nrf.configure(self.networks['core-network-cp'], mongo_net)
        self.services[nrf.name] = nrf

        ausf = AUSF("ausf")
        ausf.configure(self.networks['core-network-cp'], nrf_net)
        self.services[ausf.name] = ausf

        pcf = PCF("pcf")
        pcf_net = pcf.configure(
            self.networks['core-network-cp'], nrf_net, mongo_net)
        self.services[pcf.name] = pcf

        udm = UDM("udm")
        udm_net = udm.configure(self.networks['core-network-cp'], nrf_net)
        self.services[udm.name] = udm

        udr = UDR("udr")
        udr_net = udr.configure(
            self.networks['core-network-cp'], nrf_net, mongo_net)
        self.services[udr.name] = udr

        amf = AMF("amf")
        amf_net = amf.configure(
            self.networks['core-network-cp'], nrf_net, self.slices)
        self.services[amf.name] = amf

        upfs: List[UPF] = []

        for j in range(len(self.slices)):
            upf = UPF(f"upf-{j}")
            upf.configure(self.networks['pfcp'],
                          self.networks[f'classifier-cn-dp-{j}'], self.slices[j])
            self.services[upf.name] = upf
            upf.associate_slice(self.slices[j])
            upfs.append(upf)

        self.upfs = upfs

        # Build the GNB
        gnb = GNB("gnb")
        gnb.configure(self.networks['classifier-ran'], amf_net,
                      self.networks['ran-link-sim'], self.slices)
        self.services[gnb.name] = gnb

        ues: List[UE] = []

        # Build the UEs
        for j in range(len(self.users)):
            ue = UE(f"ue-{j}")
            ue.set_index(j)
            ue.configure(gnb.radio_link_sim,
                         self.networks['ran-link-sim'], self.slices, j)
            self.services[ue.name] = ue
            ues.append(ue)
            self.servers[j] = []

        self.ues = ues

        nssf = NSSF("nssf")
        nssf.configure(self.networks['core-network-cp'],
                       nrf_net,
                       self.slices)
        self.services[nssf.name] = nssf

        populate = POPULATE("populate")
        populate.configure(self.networks['core-network-cp'],
                           self.slices,
                           self.ues,
                           mongo_net)
        self.services[populate.name] = populate

        classifiers: List[CLASSIFIER] = []
        classifier_name = ["ran", "cn"]

        # Build the Classifiers
        for j in range(len(classifier_name)):
            classifier = CLASSIFIER(f"classifier-{classifier_name[j]}")
            classifier.configure(self.networks['satellite-control'])
            self.services[classifier.name] = classifier
            classifiers.append(classifier)

        self.classifiers = classifiers

        # Attach the networks to the classifiers
        self.services["classifier-ran"].attach_ingress(
            self.networks[f"classifier-ran"])

        for j in range(len(self.links)):
            self.services["classifier-ran"].attach_egress(
                self.networks[f"st-classifier-{j}"])

        self.services["classifier-cn"].attach_ingress(
            self.networks[f"core-network-cp"])

        for j in range(len(self.slices)):
            self.services["classifier-cn"].attach_ingress(
                self.networks[f'classifier-cn-dp-{j}'])
        for j in range(len(self.links)):
            self.services["classifier-cn"].attach_egress(
                self.networks[f"gw-classifier-{j}"])

        trunks: List[TRUNKS] = []

        # Build the NTN Slices
        for j in range(len(self.links)):
            trunk = TRUNKS(f"trunks-{j}")
            trunk.configure(self.networks[f"st-classifier-{j}"],
                            self.networks[f"gw-classifier-{j}"],
                            self.links[j])
            trunk.configure_routes(self.services['classifier-ran'],
                                   self.services['classifier-cn'],
                                   self.upfs,
                                   self.links,
                                   gnb,
                                   amf,
                                   j,
                                   self.default_link)
            self.services[trunk.name] = trunk
            trunks.append(trunk)

        self.trunks = trunks

        self.services["classifier-ran"].configure_routes_ran(
            self.links,
            self.upfs,
            self.trunks,
            amf,
            self.default_link,
        )

        self.services["classifier-cn"].configure_routes_cn(
            self.links,
            self.upfs,
            self.trunks,
            amf,
            gnb,
            self.default_link,
        )

        # Build the NTN QoS Function
        ntn = NTNQOF("ntnqof")
        ntn.configure(self.networks['satellite-control'], nrf_net)
        ntn.configure_awareness(slice_aware)
        ntn.configure_slice(self.links, self.slices, self.trunks,
                            self.classifiers[0], self.classifiers[1])
        ntn.configure_qos(APPLICATIONS)
        ntn.configure_classifier(
            self.services["classifier-ran"], self.services["classifier-cn"])
        self.services[ntn.name] = ntn

        # Build the 5G QOF Function
        qof = QOF("qof")
        qof.configure_network(
            self.networks['satellite-control'], self.networks['core-network-cp'])
        qof_net = qof.configure(
            self.networks['core-network-cp'], nrf_net, ntn.sbi)
        qof.configure_qos(APPLICATIONS)
        qof.configure_slice(gnb, upfs, self.slices, amf,
                            self.default_slice)
        self.services[qof.name] = qof

        smf = SMF("smf")
        smf.configure(self.networks['core-network-cp'],
                      self.networks['pfcp'],
                      self.slices,
                      nrf_net,
                      qof_net)
        smf.configure_ran_upf(gnb, upfs, self.slices)
        self.services[smf.name] = smf

        # Build the application servers
        i = 0
        for sl in self.slices:
            j = 0
            for ue in self.ues:
                if sl.servers.get(j, None) == None:
                    sl.servers[j] = []
                for app in sl.applications:
                    server_name = f"app-server-ue-{j}-{app.name.lower()}-slice-{i}"
                    server = SERVER(server_name)
                    server.configure(
                        self.networks[f"data-network-slice-{i}"], i, app)
                    self.services[server_name] = server
                    self.servers[j].append(server)
                    sl.servers[j].append(server)
                j += 1
            i += 1

        return

    def build_networks(self):
        """
        Generate the networks of the testbed
        """

        init_index()
        networks = []
        networks.append(Network("core-network-cp"))

        for i in range(len(self.slices)):
            networks.append(Network(f"classifier-cn-dp-{i}"))
            ue_network = Network(f"ue-network-slice-{i}", subnet=True)
            data_network = Network(f"data-network-slice-{i}", data=True)
            self.slices[i].set_ue_network(ue_network)
            self.slices[i].set_data_network(data_network)
            networks.append(ue_network)
            networks.append(data_network)

        networks.append(Network("pfcp"))

        # Configure NTN Networks
        for i in range(len(self.links)):
            networks.append(Network(f"st-classifier-{i}"))
            networks.append(Network(f"gw-classifier-{i}"))

        networks.append(Network("satellite-control"))
        networks.append(Network("classifier-ran"))
        networks.append(Network("ran-link-sim"))

        for network in networks:
            self.networks[network.name] = network

        return

    def build_topology(self, slice_aware: bool):
        """
        Generate the scenario topology
        """

        self.build_networks()
        self.build_services(slice_aware)

    def generate(self):
        """
        Generate the configuration files and scripts required by the components of the testbed
        """

        configuration_path = f"scenarios/{self.name}/configuration"
        container_path = f"scenarios/{self.name}/containers"

        for name, service in self.services.items():
            service.generate(configuration_path, container_path)
        return

    def generate_compose(self):
        """
        Generate the docker-compose.yaml corresponding to the scenario topology
        """

        compose = {"version": "3.9", "services": {}}

        # NTN QOF
        compose["services"][self.services['ntnqof'].name] = self.services['ntnqof'].generate_compose(
            depends_on=[classifier.name for classifier in self.classifiers])

        # CORE NETWORK CONTROL PLANE
        compose["services"][self.services['mongo'].name] = self.services['mongo'].generate_compose()
        compose["services"][self.services['nrf'].name] = self.services['nrf'].generate_compose(
            depends_on=["mongo"])
        compose["services"][self.services['ausf'].name] = self.services['ausf'].generate_compose(
            depends_on=["nrf"])
        compose["services"][self.services['pcf'].name] = self.services['pcf'].generate_compose(
            depends_on=["nrf"])
        compose["services"][self.services['smf'].name] = self.services['smf'].generate_compose(
            depends_on=["nrf"])
        compose["services"][self.services['udm'].name] = self.services['udm'].generate_compose(
            depends_on=["nrf"])
        compose["services"][self.services['udr'].name] = self.services['udr'].generate_compose(
            depends_on=["nrf"])
        compose["services"][self.services['nssf'].name] = self.services['nssf'].generate_compose(
            depends_on=["nrf"])
        compose["services"][self.services['qof'].name] = self.services['qof'].generate_compose(
            depends_on=["nrf", "ntnqof"])
        compose["services"][self.services['populate'].name] = self.services['populate'].generate_compose(
            depends_on=["mongo", "amf", "nrf"])

        self.services['amf'].generate_entrypoint(
            self.services['classifier-cn'].ingress, self.services['gnb'])
        self.services['amf'].write_entrypoint(
            f"scenarios/{self.name}/containers")
        compose["services"][self.services['amf'].name] = self.services['amf'].generate_compose(
            depends_on=["nrf"])

        # APPLICATION SERVERS
        for j, s in self.servers.items():
            for server in s:
                server.generate_entrypoint()
                server.write_entrypoint(f"scenarios/{self.name}/containers")
                compose["services"][server.name] = server.generate_compose()

        # CORE NETWORK DATA PLANE
        for upf in self.upfs:
            upf.generate_entrypoint(
                self.services['classifier-cn'].ingress, self.services['gnb'])
            upf.write_entrypoint(
                f"scenarios/{self.name}/containers")
            # upf.generate_applications(self.ues)
            # upf.write_application(f"scenarios/{self.name}/containers")
            compose["services"][upf.name] = upf.generate_compose()

        d = ["nrf", "amf", "smf", "pcf", "ausf", "qof",
             "ntnqof", "classifier-ran", "classifier-cn"]
        d.extend([trunk.name for trunk in self.trunks])

        # RAN
        self.services['gnb'].generate_entrypoint(
            self.services['classifier-ran'].ingress,
            self.services['amf'],
            self.upfs)
        self.services['gnb'].write_entrypoint(
            f"scenarios/{self.name}/containers")
        compose["services"][self.services['gnb'].name] = self.services['gnb'].generate_compose(
            depends_on=d)

        for index, ue in enumerate(self.ues, 0):
            ue.generate_applications(self.slices)
            ue.write_application(
                f"scenarios/{self.name}/containers")
            depends_on = ["gnb"]
            if index > 0:
                depends_on.extend([f"ue-{i}" for i in range(index)])
            compose["services"][ue.name] = ue.generate_compose(
                depends_on=depends_on)

        trunks_sts = []
        trunks_gws = []

        # NTN
        j = 0
        for trunk in self.trunks:
            trunk.generate_entrypoint(self.links[j].acm, self.slice_aware)
            trunk.write_entrypoint(f"scenarios/{self.name}/containers")
            compose["services"][trunk.name] = trunk.generate_compose(
                depends_on=["ntnqof"])
            trunks_sts.append(trunk.st)
            trunks_gws.append(trunk.gw)
        for classifier in self.classifiers:
            compose["services"][classifier.name] = classifier.generate_compose()
            if classifier.name == "classifier-ran":
                classifier.generate_entrypoint(
                    trunks_gws, trunks_sts, self.applications, True)
                classifier.write_entrypoint(
                    f"scenarios/{self.name}/containers")
            else:
                classifier.generate_entrypoint(
                    trunks_sts, trunks_gws, self.applications, False)
                classifier.write_entrypoint(
                    f"scenarios/{self.name}/containers")

        # NETWORKS
        compose["networks"] = {}
        network_index = 0
        for network_name, network in self.networks.items():
            compose["networks"][network.name] = {
                "name": network_name,
                "driver": "bridge",
                "ipam": {
                    "driver": "default",
                    "config": [
                        {"subnet": str(network.network)}
                    ]
                },
                "driver_opts":
                {
                    "com.docker.network.bridge.name": f"network-{network_index}"
                }
            }
            network_index += 1

        compose["volumes"] = {"dbdata": None}
        path = f"scenarios/{self.name}/docker-compose.yaml"
        yam = yaml.YAML()
        yam.indent(sequence=4, offset=2)
        with codecs.open(path, "w", encoding="utf-8") as compose_file:
            yam.dump(compose,  compose_file)

    def generate_all(self):
        self.generate()
        self.generate_compose()

    def get_max_duration(self):
        """
        Get the maximum duration of traffic generation
        """
        m = 0
        for s in self.slices:
            if s.end >= m:
                m = s.end
        return m

    def run(self):
        """
        Run a scenario and collect probes
        """
        logging.info(f"Running {self.name} scenario")

        offset: int = 5 + 0.2 * len(self.users)
        duration = self.get_max_duration()

        logging.info("Starting testbed...")
        runner.start_testbed(self.name)
        logging.info("Waiting for configuration...")
        runner.wait_for_configuration()
        time.sleep(5)

        ue_ips: List[List[str]] = []
        n = len(self.slices)
        n_ue = len(self.users)
        for k in range(n_ue):
            time.sleep(0.2)
            ue_ips.append(runner.gather_ip(f"ue-{k}", n))

        for k in range(n):
            schedule.every(
                offset + self.slices[k].start).seconds.do(runner.run_app, slice_id=k, ue_ips=ue_ips)

        end: int = offset + duration + offset
        start = 0
        while start < end:
            schedule.run_pending()
            time.sleep(1)
            start += 1

        runner.stop_testbed(self.name)
