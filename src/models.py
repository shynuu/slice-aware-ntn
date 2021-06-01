from cerberus import Validator
from typing import List, Dict
from ruamel import yaml
import ipaddress
import codecs
import logging
import os
from .const import APPLICATION_STREAMING, APPLICATION_VOIP, APPLICATION_WEB

NETWORKS = [
    "172.16.10.0/24",
    "172.16.20.0/24",
    "172.16.30.0/24",
    "172.16.40.0/24",
    "172.16.50.0/24",
    "172.16.60.0/24",
    "172.16.70.0/24",
    "172.16.80.0/24",
    "172.16.90.0/24",
    "172.16.100.0/24",
    "172.16.110.0/24",
    "172.16.120.0/24",
    "172.16.130.0/24",
    "172.16.140.0/24",
]

UE_SUBNETS = [
    "60.60.0.0/24",
    "60.60.1.0/24",
    "60.60.2.0/24",
    "60.60.3.0/24",
]

DATA_NETWORK = [
    "10.0.100.0/24",
    "10.0.110.0/24",
    "10.0.120.0/24",
]


NETWORK_INDEX = 0
UE_SUBNETS_INDEX = 0
DATA_NETWORK_INDEX = 0

MNC = "208"
MCC = "93"


class HexInt(int):
    pass


def representer(dumper, data):
    return yaml.representer.ScalarNode('tag:yaml.org,2002:int', f"0x{data:02x}")


def init_index():
    global NETWORK_INDEX
    global UE_SUBNETS_INDEX
    global DATA_NETWORK_INDEX
    NETWORK_INDEX = 0
    UE_SUBNETS_INDEX = 0
    DATA_NETWORK_INDEX = 0


class Model(object):

    configuration = ""
    compose = ""
    out_configuration = ""

    def __init__(self, name):
        self.name = name

    def read_compose(self):
        with codecs.open(self.compose, mode="r", encoding="utf8") as f:
            self.compose = f.read()
        self.compose = self.compose.replace("CONTAINER_NAME", self.name)

    def read_configuration(self):
        with codecs.open(self.configuration, mode="r", encoding="utf8") as f:
            self.configuration = f.read()
        self.configuration = yaml.load(
            self.configuration, Loader=yaml.RoundTripLoader)

    def generate_compose(self, path: str):
        pass

    def generate_configuration(self, path: str):
        path = f"{path}/{self.name}.yaml"
        yam = yaml.YAML()
        yam.indent(sequence=4, offset=2)
        with codecs.open(path, "w", encoding="utf-8") as configuration:
            yam.representer.add_representer(HexInt, representer)
            yam.dump(self.configuration,  configuration)


class Network(Model):

    def __init__(self, name, subnet=False, data=False):
        global NETWORK_INDEX
        global UE_SUBNETS_INDEX
        global DATA_NETWORK_INDEX
        super().__init__(name)
        if subnet:
            network = UE_SUBNETS[UE_SUBNETS_INDEX]
            UE_SUBNETS_INDEX += 1
        elif data:
            network = DATA_NETWORK[DATA_NETWORK_INDEX]
            DATA_NETWORK_INDEX += 1
        else:
            network = NETWORKS[NETWORK_INDEX]
            NETWORK_INDEX += 1
        self.network = ipaddress.IPv4Network(network)
        self.hosts = list(self.network.hosts())[1:]

    def get_address(self):
        return self.hosts.pop(0)

    def get_specific_address(self, index):
        return self.hosts.pop(index)


class Service(Model):

    def __init__(self, name):
        super().__init__(name)
        self.networks = {}

    def attach_network(self, network: Network, index: int = None):
        if index:
            address = network.get_specific_address(index)
        else:
            address = network.get_address()
        self.networks[network.name] = address
        return address

    def configure_sba_ip(self, sba: Network):
        net = self.attach_network(sba)
        self.configuration['configuration']['sbi']['registerIPv4'] = str(net)
        self.configuration['configuration']['sbi']['bindingIPv4'] = str(net)
        return net

    def generate(self, configuration: str, containers: str):
        pass

    def configure(self):
        pass


class Compose(object):

    def __init__(self, name):
        self.name = name
        self.tty: bool = None
        self.container_name: str = None
        self.build_context: str = None
        self.build_args: Dict[str, str] = None
        self.image: str = None
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
        self.configuration = {}

        if self.tty != None:
            self.configuration['tty'] = self.tty

        if self.container_name != None:
            self.configuration['container_name'] = self.container_name

        if self.build_context != None:
            self.configuration['build'] = {'context': self.build_context}

        if self.build_args != None:
            self.configuration['build']['args'] = self.build_args

        if self.image != None:
            self.configuration['image'] = self.image

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
    def New(cls, name):
        container = Compose(name)
        container.container_name = name
        return container

# Objects


class Theta(object):

    def __init__(self, lamba, delta, mu, beta, sigma):
        self.lamba = lamba
        self.delta = delta
        self.mu = mu
        self.beta = beta
        self.sigma = sigma


class Application(object):

    def __init__(self, name: str, aware: bool):
        self.name = name
        self.qi = None
        self.port = None
        self.ntn_dscp = None
        self.terrestrial_dscp = None
        self.data_rate = None
        self.pdb = None
        self.code = None
        if aware:
            self.results = "results-sa"
        else:
            self.results = "results-non-sa"

    def generate_tos(self):
        return hex(self.terrestrial_dscp << 2)

    def generate_server(self, bind, sl, server):
        pass

    def generate_client(self, bind, destination, ue, sl, upf, duration):
        pass

    def get_data_rate(self):
        pass

    def get_log_server(self, server: str, sl: int):
        return f"{self.results}/{server}_{self.name.lower()}_{sl}_probes.txt"

    def get_log_client(self, ue: str, sl: int):
        return f"{self.results}/{ue}_{self.name.lower()}_{sl}_probes.txt"


class VoIP(Application):

    def __init__(self, aware: bool, data_rate=128):
        super().__init__("VoIP", aware)
        self.qi = 7
        # EF
        self.ntn_dscp = 0x2c
        # AF
        self.terrestrial_dscp = 0x2e
        self.port = 5060
        self.data_rate = data_rate
        self.pdb = 100
        self.code = APPLICATION_VOIP

    def generate_server(self, bind, sl, server):
        return f"iperf -s -B {bind} -p {self.port} -u -l 1400 -i 1 -f b --tos {self.generate_tos()} > {self.get_log_server(server, sl)}"

    def generate_client(self, bind, destination, ue, sl, duration):
        return f"iperf -c {destination} -B {bind} -p {self.port} --trip-times --tos {self.generate_tos()} -i 1 -u -l 1400 --reverse -t {duration}s -b {self.data_rate}k -f b > {self.get_log_client(ue, sl)} &"

    def get_data_rate(self):
        return f"{self.data_rate} kbit/s"


class Streaming(Application):

    def __init__(self, aware: bool, data_rate=5):
        super().__init__("Streaming", aware)
        self.qi = 6
        # AF12
        self.ntn_dscp = 0x0c
        # AF12
        self.terrestrial_dscp = 0x0c
        self.port = 8085
        self.data_rate = data_rate
        self.pdb = 300
        self.code = APPLICATION_STREAMING

    def generate_server(self, bind, sl, server):
        return f"iperf -s -B {bind} -p {self.port} -u -l 1400 -i 1 -f b --tos {self.generate_tos()} > {self.get_log_server(server, sl)}"

    def generate_client(self, bind, destination, ue, sl, duration):
        return f"iperf -c {destination} -B {bind} -p {self.port} --trip-times --tos {self.generate_tos()} -i 1 -u -l 1400 --reverse -t {duration}s --isochronous=25:{self.data_rate}m,{round(self.data_rate * 0.2)}m -f b > {self.get_log_client(ue, sl)} &"

    def get_data_rate(self):
        return f"{self.data_rate} Mbit/s"


class Web(Application):

    def __init__(self, aware: bool, data_rate=3):
        super().__init__("Web", aware)
        self.qi = 9
        # AF11
        self.ntn_dscp = 0x0a
        # AF11
        self.terrestrial_dscp = 0x0a
        self.port = 8080
        self.data_rate = data_rate
        self.pdb = 300
        self.code = APPLICATION_WEB

    def generate_server(self, bind, sl, server):
        return f"iperf -s -B {bind} -p {self.port} -b {self.data_rate}M -u -l 1400 -i 1 -f b --tos {self.generate_tos()} > {self.get_log_server(server, sl)}"

    def generate_client(self, bind, destination, ue, sl, duration):
        return f"iperf -c {destination} -B {bind} -p {self.port} --trip-times --tos {self.generate_tos()} -i 1 -u -l 1400 --reverse -t {duration}s -b {self.data_rate}M -f b > {self.get_log_client(ue, sl)} &"

    def get_data_rate(self):
        return f"{self.data_rate} Mbit/s"


class Slice(object):

    def __init__(self, sst: str, sd: str, data_network: str, start: int, end: int):
        self.start = start
        self.end = end
        self.sst = sst
        self.sd = sd
        self.data_network = data_network
        self.applications: List[Application] = []
        self.servers = {}

    def ntn(self, ntn):
        self.Ntn = ntn

    def theta(self, theta):
        self.Theta = theta

    def set_ue_network(self, network: Network):
        self.ue_network = network

    def set_data_network(self, network: Network):
        self.network = network

    def add_server(self, server):
        self.servers.append(server)

    def generate_conf(self):
        sst = f'{int(self.sst):02d}'
        sd = f'{int(self.sd):06d}'
        return {'sst': int(sst), 'sd': int(sd)}

    def __str__(self):
        return f"{self.sst}, {self.sd}"


class Ntn(object):

    def __init__(self, forward: int, retur: int, delay: int, jitter: int, acm: bool, default: bool):
        self.forward = forward
        self.retur = retur
        self.delay = delay
        self.jitter = jitter
        self.acm = acm
        self.default = default
        self.slices: Slice = []


class User(Model):

    def __init__(self):
        self.applications = []
        self.slices = []

    def attach_application(self, application: Application):
        self.slices.append(application)
        return application


# 5G COMPONENTS


class SERVER(Service):

    def __init__(self, name):
        super().__init__(name)

    def configure(self, network: Network, sl: int, application: Application):
        self.ip = self.attach_network(network)
        self.application = application
        self.sl_i = sl

    def generate_entrypoint(self):
        s = ["#!/bin/bash"]
        s.append(self.application.generate_server(
            f"{self.ip}", self.sl_i, self.name))
        self.entrypoint = "\n".join(s)

    def write_entrypoint(self, path):
        pth = f"{path}/{self.name}.sh"
        with codecs.open(pth, "w", encoding="utf8") as entrypoint:
            entrypoint.write(self.entrypoint)
        os.chmod(pth, 0o777)

    def generate_compose(self, depends_on=None):
        compose = Compose.New(self.name)
        compose.image = "shynuu/sa-ntn:application"
        compose.container_name = self.name
        compose.tty = True
        compose.entrypoint = f"./entrypoint.sh"
        compose.volumes = [
            f"./containers/{self.name}.sh:/application/entrypoint.sh",
            f"./results-sa:/application/results-sa",
            f"./results-non-sa:/application/results-non-sa",
        ]
        compose.cap_add = ["NET_ADMIN"]
        compose.networks = self.networks
        if depends_on != None:
            compose.depends_on = depends_on
        return compose.generate()


class UE(Service):

    configuration = "config/components/uecfg.yaml"
    compose = "config/containers/ue.yaml"

    def __init__(self, name):
        super().__init__(name)
        self.read_configuration()
        self.applications = []

    def set_index(self, index: int):
        self.index = index

    def configure(self, ran_sim: ipaddress.IPv4Address, ran: Network, slices: List[Slice], index: int):
        self.attach_network(ran)
        self.imsi = f"imsi-{MNC}{MCC}{index+1:010d}"
        self.configuration["supi"] = self.imsi
        self.configuration['gnbSearchList'] = [str(ran_sim)]
        self.configuration["sessions"] = [
            {
                "type": 'IPv4',
                "apn": sl.data_network,
                "emergency": False,
                "slice": {
                        "sst": HexInt(int(sl.sst, 16)),
                        "sd": HexInt(int(sl.sd, 16)),
                }
            } for sl in slices
        ]
        self.configuration["configured-nssai"] = [
            {
                "sst": HexInt(int(sl.sst, 16)),
                "sd": HexInt(int(sl.sd, 16)),
            }
            for sl in slices
        ]

    def generate(self, configuration: str, containers: str):
        self.generate_configuration(configuration)

    def generate_applications(self, slices: List[Slice]):
        i = 0
        for sl in slices:
            s = ["#!/bin/bash"]
            bind = f"BIND_0"
            s.append(f"BIND_0=$1")
            s.append(f"ip route add {sl.network.network} via $BIND_0")
            for server in sl.servers[self.index]:
                s.append(server.application.generate_client(
                    f"${bind}", f"{server.ip}", self.name, i, sl.end))
            self.applications.append("\n".join(s))
            i += 1

    def write_application(self, path):
        i = 0
        for app in self.applications:
            pth = f"{path}/{self.name}-slice-{i}-app.sh"
            with codecs.open(pth, "w", encoding="utf8") as application:
                application.write(app)
            os.chmod(pth, 0o777)
            i += 1

    def generate_compose(self, depends_on=None):
        compose = Compose.New(self.name)
        compose.image = "shynuu/sa-ntn:ue"
        compose.container_name = self.name
        compose.command = f"--config ue.yaml"
        compose.volumes = [
            f"./configuration/{self.name}.yaml:/ue/ue.yaml",
            f"./results-sa:/ue/results-sa",
            f"./results-non-sa:/ue/results-non-sa",
        ]
        for i in range(len(self.applications)):
            compose.volumes.append(
                f"./containers/{self.name}-slice-{i}-app.sh:/ue/slice-{i}-app.sh",)
        compose.cap_add = ["NET_ADMIN"]
        compose.devices = ["/dev/net/tun"]
        compose.networks = self.networks
        if depends_on != None:
            compose.depends_on = depends_on
        return compose.generate()


class POPULATE(Service):

    configuration = "config/components/populatecfg.yaml"
    compose = "config/containers/ue.yaml"

    def __init__(self, name):
        super().__init__(name)
        self.read_configuration()

    def configure(self, sba: Network, slices: List[Slice], ues: List[UE], mongo: ipaddress.IPv4Address):
        self.attach_network(sba)
        self.configuration["mongo"]["url"] = f"mongodb://{str(mongo)}:27017"
        self.configuration["slices"] = [
            {
                "sst": int(sl.sst),
                "sd": sl.sd,
                "varqi": 9,
                "dnn": sl.data_network,
            }
            for sl in slices
        ]
        self.configuration["imsi"] = [ue.imsi for ue in ues]

    def generate(self, configuration: str, containers: str):
        self.generate_configuration(configuration)

    def generate_compose(self, depends_on=None):
        compose = Compose.New(self.name)
        compose.image = "shynuu/sa-ntn:populate"
        compose.container_name = self.name
        compose.command = f"--config populatecfg.yaml"
        compose.volumes = [
            f"./configuration/{self.name}.yaml:/populate/populatecfg.yaml",
        ]
        compose.networks = self.networks
        if depends_on != None:
            compose.depends_on = depends_on
        return compose.generate()


class UPF(Service):

    configuration = "config/components/upfcfg.yaml"
    compose = "config/containers/upf.yaml"

    def __init__(self, name):
        super().__init__(name)
        self.read_configuration()
        self.applications = None
        self.sl = None

    def configure(self, pfcp_network: Network, gtp_network: Network, slisse: Slice):
        self.ip = self.attach_network(slisse.ue_network, index=99)
        self.dn = self.attach_network(slisse.network)
        self.pfcp = self.attach_network(pfcp_network)
        self.gtp = self.attach_network(gtp_network)
        self.slisse = slisse

        self.configuration['configuration']['pfcp'] = [
            {'addr': str(self.pfcp)}]
        self.configuration['configuration']['gtpu'] = [
            {'addr': str(self.gtp)}]

        self.configuration['configuration']['dnn_list'] = [
            {'dnn': slisse.data_network, 'cidr': str(slisse.ue_network.network)}]

    def generate(self, configuration: str, containers: str):
        self.generate_configuration(configuration)

    def associate_slice(self, sl):
        self.sl = sl

    def find_network(self, classifier_ips: List[ipaddress.IPv4Address]):
        ip_network = ipaddress.ip_interface(f"{self.gtp}/24").network
        for ip in classifier_ips:
            if ip in ip_network:
                return ip

    def generate_entrypoint(self, classifier_ips: List[ipaddress.IPv4Address], gnb):
        classifier_ip = self.find_network(classifier_ips)
        s = ["#!/bin/bash"]
        s.append(f"ETH=$(ip a | grep {self.dn} | awk \'{{print($7)}}\')")
        s.append("iptables -t nat -A POSTROUTING -o $ETH -j MASQUERADE")
        ran_network = ipaddress.IPv4Interface(f"{gnb.ran_net}/24").network
        s.append(f"ip route add {ran_network} via {classifier_ip}")
        s.append(f"free5gc-upfd -f {self.name}.yaml")
        self.entrypoint = "\n".join(s)

    def write_entrypoint(self, path):
        pth = f"{path}/{self.name}.sh"
        with codecs.open(pth, "w", encoding="utf8") as entrypoint:
            entrypoint.write(self.entrypoint)
        os.chmod(pth, 0o777)

    def generate_compose(self, depends_on=None):
        compose = Compose.New(self.name)
        compose.image = "shynuu/sa-ntn:upf"
        compose.entrypoint = "./entrypoint.sh"
        compose.volumes = [
            f"./configuration/{self.name}.yaml:/upf/{self.name}.yaml",
            f"./containers/{self.name}.sh:/upf/entrypoint.sh",
            f"./containers/{self.name}-app.sh:/upf/{self.name}-app.sh",
            f"./results-sa:/upf/results-sa",
            f"./results-non-sa:/upf/results-non-sa",
        ]
        compose.networks = self.networks
        compose.cap_add = ["NET_ADMIN"]
        if depends_on != None:
            compose.depends_on = depends_on
        return compose.generate()


class AMF(Service):

    configuration = "config/components/amfcfg.yaml"
    compose = "config/containers/amf.yaml"

    def __init__(self, name):
        super().__init__(name)
        self.read_configuration()

    def configure(self, sba: Network, nrf: Network, slices: List[Slice]):
        net = self.configure_sba_ip(sba)
        self.n2 = net
        self.configuration['configuration']['amfName'] = self.name.upper()
        self.configuration['configuration']['ngapIpList'] = [str(net)]
        self.configuration['configuration']['plmnSupportList'][0]['snssaiList'] = [
            sl.generate_conf() for sl in slices]
        self.configuration['configuration']['supportDnnList'] = [
            sl.data_network for sl in slices]

        self.configuration['configuration']['nrfUri'] = f"http://{nrf}:8000"
        # logging.info(self.configuration)
        return net

    def generate(self, configuration: str, containers: str):
        self.generate_configuration(configuration)

    def find_network(self, classifier_ips: List[ipaddress.IPv4Address]):
        ip_network = ipaddress.ip_interface(f"{self.n2}/24").network
        for ip in classifier_ips:
            if ip in ip_network:
                return ip

    def generate_entrypoint(self, classifier_ips: List[ipaddress.IPv4Address], gnb):
        classifier_ip = self.find_network(classifier_ips)
        s = ["#!/bin/bash"]
        ran_network = ipaddress.IPv4Interface(f"{gnb.ran_net}/24").network
        s.append(f"ip route add {ran_network} via {classifier_ip}")
        s.append(f"amf --amfcfg {self.name}.yaml")
        self.entrypoint = "\n".join(s)

    def write_entrypoint(self, path):
        pth = f"{path}/{self.name}.sh"
        with codecs.open(pth, "w", encoding="utf8") as entrypoint:
            entrypoint.write(self.entrypoint)
        os.chmod(pth, 0o777)

    def generate_compose(self, depends_on=None):
        compose = Compose.New(self.name)
        compose.image = "shynuu/sa-ntn:amf"
        compose.entrypoint = f"./entrypoint.sh"
        compose.volumes = [
            f"./configuration/{self.name}.yaml:/amf/{self.name}.yaml",
            f"./containers/{self.name}.sh:/amf/entrypoint.sh"
        ]
        compose.environment = {"GIN_MODE": "release"}
        compose.networks = self.networks
        compose.cap_add = ["NET_ADMIN"]
        if depends_on != None:
            compose.depends_on = depends_on
        return compose.generate()


class NSSF(Service):

    configuration = "config/components/nssfcfg.yaml"
    compose = "config/containers/nssf.yaml"

    def __init__(self, name):
        super().__init__(name)
        self.nsiId = 10
        self.read_configuration()

    def get_nsiId(self):
        self.nsiId += 1
        return self.nsiId

    def configure(self, sba: Network, nrf: ipaddress.IPv4Address, slices: List[Slice]):
        net = self.configure_sba_ip(sba)
        self.configuration['configuration']['nrfUri'] = f"http://{nrf}:8000"
        self.configuration['configuration']['supportedNssaiInPlmnList'][0]['supportedSnssaiList'] = [
            sl.generate_conf() for sl in slices]
        self.configuration['configuration']['nsiList'] = [
            {
                'snssai': sl.generate_conf(),
                'nsiInformationList':
                [{
                    'nrfId': f"http://{nrf}:8000/nnrf-nfm/v1/nf-instances",
                    'nsiId': self.get_nsiId(),
                }]
            }
            for sl in slices
        ]
        self.configuration['configuration']['amfSetList'][0][
            'nrfAmfSet'] = f"http://{nrf}:8000/nnrf-nfm/v1/nf-instances"
        self.configuration['configuration']['amfSetList'][0]["supportedNssaiAvailabilityData"][0]['supportedSnssaiList'] = [
            sl.generate_conf() for sl in slices
        ]
        self.configuration['configuration']['taList'][0]['supportedSnssaiList'] = [
            sl.generate_conf() for sl in slices
        ]
        return net

    def generate(self, configuration: str, containers: str):
        self.generate_configuration(configuration)

    def generate_compose(self, depends_on=None):
        compose = Compose.New(self.name)
        compose.image = "shynuu/sa-ntn:nssf"
        compose.container_name = self.name
        compose.command = f"--nssfcfg {self.name}.yaml"
        compose.volumes = [
            f"./configuration/{self.name}.yaml:/nssf/{self.name}.yaml",
        ]
        compose.environment = {"GIN_MODE": "release"}
        compose.networks = self.networks
        if depends_on != None:
            compose.depends_on = depends_on
        return compose.generate()


class GNB(Service):

    configuration = "config/components/gnbcfg.yaml"
    compose = "config/containers/gnb.yaml"

    def __init__(self, name):
        super().__init__(name)
        self.read_configuration()

    def configure(self, ran: Network, amf_net: ipaddress.IPv4Address, ran_sim: Network, slices: List[Slice]):
        self.ran_net = self.attach_network(ran)
        self.radio_link_sim = self.attach_network(ran_sim)

        self.configuration["linkIp"] = str(self.radio_link_sim)
        self.configuration["ngapIp"] = str(self.ran_net)
        self.configuration["gtpIp"] = str(self.ran_net)
        self.configuration['amfConfigs'] = [
            {"address": str(amf_net), "port": 38412}]

        self.configuration["slices"] = [
            {"sst": HexInt(int(sl.sst, 16)), "sd": HexInt(int(sl.sd, 16))} for sl in slices]
        return

    def generate(self, configuration: str, containers: str):
        self.generate_configuration(configuration)

    def find_network(self, classifier_ips: List[ipaddress.IPv4Address]):
        ip_network = ipaddress.ip_interface(f"{self.ran_net}/24").network
        for ip in classifier_ips:
            if ip in ip_network:
                return ip

    def generate_entrypoint(self, classifier_ips: List[ipaddress.IPv4Address], amf: AMF, upfs: List[UPF]):
        classifier_ip = self.find_network(classifier_ips)
        s = ["#!/bin/bash"]
        s.append(f"gtp-dscp --ipv4 {self.ran_net} --offset 16")
        sbi_network = ipaddress.IPv4Interface(f"{amf.n2}/24").network
        s.append(f"ip route add {sbi_network} via {classifier_ip}")
        for upf in upfs:
            upf_network = ipaddress.IPv4Interface(f"{upf.gtp}/24").network
            s.append(f"ip route add {upf_network} via {classifier_ip}")
        s.append("sleep 6")
        s.append(f"nr-gnb --config {self.name}.yaml")
        self.entrypoint = "\n".join(s)

    def write_entrypoint(self, path):
        pth = f"{path}/{self.name}.sh"
        with codecs.open(pth, "w", encoding="utf8") as entrypoint:
            entrypoint.write(self.entrypoint)
        os.chmod(pth, 0o777)

    def generate_compose(self, depends_on=None):
        compose = Compose.New(self.name)
        compose.image = "shynuu/sa-ntn:gnb"
        compose.volumes = [
            f"./configuration/{self.name}.yaml:/ueransim/{self.name}.yaml",
            f"./containers/{self.name}.sh:/ueransim/entrypoint.sh"
        ]
        compose.environment = {"GIN_MODE": "release"}
        compose.entrypoint = "./entrypoint.sh"
        compose.cap_add = ["NET_ADMIN"]
        compose.networks = self.networks
        if depends_on != None:
            compose.depends_on = depends_on
        return compose.generate()


class SMF(Service):

    configuration = "config/components/smfcfg.yaml"
    compose = "config/containers/smf.yaml"
    uerouting = "config/components/uerouting.yaml"

    def __init__(self, name):
        super().__init__(name)
        self.read_configuration()
        self.read_uerouting()

    def read_uerouting(self):
        with codecs.open(self.uerouting, mode="r", encoding="utf8") as f:
            self.uerouting = f.read()
        self.uerouting = yaml.load(
            self.uerouting, Loader=yaml.RoundTripLoader)

    def configure(self, sba: Network, pfcp: Network, slices: List[Slice], nrf_net: ipaddress.IPv4Address, qof_net: ipaddress.IPv4Address):
        net = self.configure_sba_ip(sba)
        self.configuration["configuration"]["snssaiInfos"] = [
            {
                "sNssai": sl.generate_conf(),
                "dnnInfos": [
                    {
                        "dnn": sl.data_network,
                        "dns":
                        {
                            "ipv4": "8.8.8.8",
                            "ipv6": "2001:4860:4860::8888"
                        },
                        "ueSubnet": str(sl.ue_network.network)
                    }
                ]
            }
            for sl in slices
        ]
        self.configuration["configuration"]["pfcp"]["addr"] = str(
            self.attach_network(pfcp))
        self.configuration["configuration"]["nrfUri"] = f"http://{nrf_net}:8000"
        self.configuration["configuration"]["qofUri"] = f"http://{qof_net}:8090"

        return net

    def configure_ran_upf(self, gnb: GNB, upfs: List[UPF], slices: List[Slice]):
        self.configuration["configuration"]["userplane_information"]["up_nodes"] = {
        }
        self.configuration["configuration"]["userplane_information"]["up_nodes"][gnb.name] = {
            "type": "AN",
            "an_ip": str(gnb.ran_net)
        }
        for j in range(len(upfs)):
            self.configuration["configuration"]["userplane_information"]["up_nodes"][upfs[j].name] = {
                "type": "UPF",
                "node_id": str(upfs[j].pfcp),
                "sNssaiUpfInfos":
                [
                    {
                        "sNssai": slices[j].generate_conf(),
                        "dnnUpfInfoList": [
                            {
                                "dnn": slices[j].data_network,
                                # Should be here if new version of free5gc
                                # "pools": [
                                #     {"cidr": str(slices[j].network.network)}
                                # ]
                            }
                        ]
                    }
                ],
                "interfaces":
                [
                    {
                        "interfaceType": "N3",
                        "endpoints": [
                            str(upfs[j].gtp)
                        ],
                        "networkInstance": slices[j].data_network,
                    }
                ]
            }

        self.configuration["configuration"]["userplane_information"]["links"] = [
            {"A": gnb.name, "B": upf.name} for upf in upfs
        ]

    def generate_uerouting(self, path: str):
        path = f"{path}/uerouting.yaml"
        yam = yaml.YAML()
        yam.indent(sequence=4, offset=2)
        with codecs.open(path, "w", encoding="utf-8") as uerouting:
            yam.representer.add_representer(HexInt, representer)
            yam.dump(self.uerouting,  uerouting)

    def generate(self, configuration: str, containers: str):
        self.generate_configuration(configuration)
        self.generate_uerouting(configuration)

    def generate_compose(self, depends_on=None):
        compose = Compose.New(self.name)
        compose.image = "shynuu/sa-ntn:smf"
        compose.container_name = self.name
        compose.command = f"--smfcfg {self.name}.yaml --uerouting uerouting.yaml"
        compose.volumes = [
            f"./configuration/{self.name}.yaml:/smf/{self.name}.yaml",
            f"./configuration/uerouting.yaml:/smf/uerouting.yaml",
        ]
        compose.environment = {"GIN_MODE": "release"}
        compose.networks = self.networks
        if depends_on != None:
            compose.depends_on = depends_on
        return compose.generate()


class AUSF(Service):

    configuration = "config/components/ausfcfg.yaml"
    compose = "config/containers/ausf.yaml"

    def __init__(self, name):
        super().__init__(name)
        self.read_configuration()

    def configure(self, sba: Network, nrf: Network):
        net = self.configure_sba_ip(sba)
        self.configuration['configuration']['nrfUri'] = f"http://{nrf}:8000"

        return net

    def generate(self, configuration: str, containers: str):
        self.generate_configuration(configuration)

    def generate_compose(self, depends_on=None):
        compose = Compose.New(self.name)
        compose.image = "shynuu/sa-ntn:ausf"
        compose.container_name = self.name
        compose.command = f"--ausfcfg {self.name}.yaml"
        compose.volumes = [
            f"./configuration/{self.name}.yaml:/ausf/{self.name}.yaml",
        ]
        compose.environment = {"GIN_MODE": "release"}
        compose.networks = self.networks
        if depends_on != None:
            compose.depends_on = depends_on
        return compose.generate()


class NRF(Service):

    configuration = "config/components/nrfcfg.yaml"
    compose = "config/containers/nrf.yaml"
    out_configuration = "nrfcfg.yaml"

    def __init__(self, name):
        super().__init__(name)
        self.read_configuration()

    def configure(self, sba: Network, mongo: Network):
        self.configuration['configuration']['nrfName'] = self.name.upper()
        net = self.configure_sba_ip(sba)

        mongoUri = f"mongodb://{mongo}:27017"
        self.configuration['configuration']['MongoDBUrl'] = mongoUri
        return net

    def generate(self, configuration: str, containers: str):
        self.generate_configuration(configuration)

    def generate_compose(self, depends_on=None):
        compose = Compose.New(self.name)
        compose.image = "shynuu/sa-ntn:nrf"
        compose.container_name = self.name
        compose.command = f"--nrfcfg {self.name}.yaml"
        compose.volumes = [
            f"./configuration/{self.name}.yaml:/nrf/{self.name}.yaml",
        ]
        compose.environment = {"GIN_MODE": "release"}
        compose.networks = self.networks
        if depends_on != None:
            compose.depends_on = depends_on
        return compose.generate()


class PCF(Service):

    configuration = "config/components/pcfcfg.yaml"
    compose = "config/containers/pcf.yaml"

    def __init__(self, name):
        super().__init__(name)
        self.read_configuration()

    def configure(self, sba: Network, nrf: Network, mongo: Network):
        self.configuration['configuration']['pcfName'] = self.name.upper()
        net = self.configure_sba_ip(sba)

        mongoUri = f"mongodb://{mongo}:27017"
        self.configuration['configuration']['mongodb']['url'] = mongoUri
        self.configuration['configuration']['nrfUri'] = f"http://{nrf}:8000"
        return net

    def generate(self, configuration: str, containers: str):
        self.generate_configuration(configuration)

    def generate_compose(self, depends_on=None):
        compose = Compose.New(self.name)
        compose.image = "shynuu/sa-ntn:pcf"
        compose.container_name = self.name
        compose.command = f"--pcfcfg {self.name}.yaml"
        compose.volumes = [
            f"./configuration/{self.name}.yaml:/pcf/{self.name}.yaml",
        ]
        compose.environment = {"GIN_MODE": "release"}
        compose.networks = self.networks
        if depends_on != None:
            compose.depends_on = depends_on
        return compose.generate()


class UDM(Service):

    configuration = "config/components/udmcfg.yaml"
    compose = "config/containers/udm.yaml"

    def __init__(self, name):
        super().__init__(name)
        self.read_configuration()

    def configure(self, sba: Network, nrf: Network):
        net = self.configure_sba_ip(sba)
        self.configuration['configuration']['nrfUri'] = f"http://{nrf}:8000"
        return net

    def generate(self, configuration: str, containers: str):
        self.generate_configuration(configuration)

    def generate_compose(self, depends_on=None):
        compose = Compose.New(self.name)
        compose.image = "shynuu/sa-ntn:udm"
        compose.container_name = self.name
        compose.command = f"--udmcfg {self.name}.yaml"
        compose.volumes = [
            f"./configuration/{self.name}.yaml:/udm/{self.name}.yaml",
        ]
        compose.environment = {"GIN_MODE": "release"}
        compose.networks = self.networks
        if depends_on != None:
            compose.depends_on = depends_on
        return compose.generate()


class UDR(Service):

    configuration = "config/components/udrcfg.yaml"
    compose = "config/containers/udr.yaml"

    def __init__(self, name):
        super().__init__(name)
        self.read_configuration()

    def configure(self, sba: Network, nrf: ipaddress.IPv4Address, mongo: ipaddress.IPv4Address):
        net = self.configure_sba_ip(sba)

        mongoUri = f"mongodb://{mongo}:27017"
        self.configuration['configuration']['mongodb']['url'] = mongoUri
        self.configuration['configuration']['nrfUri'] = f"http://{nrf}:8000"
        return net

    def generate(self, configuration: str, containers: str):
        self.generate_configuration(configuration)

    def generate_compose(self, depends_on=None):
        compose = Compose.New(self.name)
        compose.image = "shynuu/sa-ntn:udr"
        compose.container_name = self.name
        compose.command = f"--udrcfg {self.name}.yaml"
        compose.volumes = [
            f"./configuration/{self.name}.yaml:/udr/{self.name}.yaml",
        ]
        compose.environment = {"GIN_MODE": "release"}
        compose.networks = self.networks
        if depends_on != None:
            compose.depends_on = depends_on
        return compose.generate()


# NTN COMPONENTS


class TRUNKS(Service):

    configuration = "config/components/trunks.yaml"
    compose = "config/containers/trunks.yaml"

    def __init__(self, name):
        super().__init__(name)
        self.read_configuration()
        self.routes = []

    def configure(self, st_network: Network, gw_network: Network, link: Ntn):
        self.st = self.attach_network(st_network)
        self.gw = self.attach_network(gw_network)

        self.configuration["nic"] = {
            "st": str(self.st),
            "gw": str(self.gw)
        }

        self.configuration["bandwidth"] = {
            "forward": link.forward,
            "return": link.retur
        }

        self.configuration["delay"] = {
            "value": link.delay,
            "offset": link.jitter
        }

        return

    def find_network(self, ip_v: ipaddress.IPv4Address, classifier_ips: List[ipaddress.IPv4Address]):
        ip_network = ipaddress.ip_interface(f"{ip_v}/24").network
        for ip in classifier_ips:
            if ip in ip_network:
                return ip

    def configure_routes(self, classifier_ran, classifier_cn, upfs: List[UPF], links: List[Ntn], gnb: GNB, amf: AMF, index: int, default_slice: int):
        if index == default_slice:
            ip_network = ipaddress.ip_interface(f"{amf.n2}/24").network
            gateway = self.find_network(self.gw, classifier_cn.egress)
            self.routes.append((gateway, ip_network))
        k = 0
        if index > 0:
            for i in range(index):
                k += len(links[i].slices)
        for s in links[index].slices:
            # Find IP NETWORK of UPF and add Route to IP Network using the classifier CN interface
            ip_network = ipaddress.ip_interface(f"{upfs[k].gtp}/24").network
            gateway = self.find_network(self.gw, classifier_cn.egress)
            if (gateway, ip_network) not in self.routes:
                self.routes.append((gateway, ip_network))
            k += 1

        ip_network = ipaddress.ip_interface(f"{gnb.ran_net}/24").network
        gateway = self.find_network(self.st, classifier_ran.egress)
        self.routes.append((gateway, ip_network))

    def generate(self, configuration: str, containers: str):
        self.generate_configuration(configuration)

    def generate_entrypoint(self, acm: bool, slice_aware: bool):
        s = ["#!/bin/bash"]
        for route in self.routes:
            s.append(f"ip route add {route[1]} via {route[0]}")
        a = "--acm" if acm else ""
        aw = "--qos" if slice_aware else ""
        s.append(f"trunks --config trunks.yaml {aw} {a}")
        self.entrypoint = "\n".join(s)

    def write_entrypoint(self, path):
        pth = f"{path}/{self.name}.sh"
        with codecs.open(pth, "w", encoding="utf8") as entrypoint:
            entrypoint.write(self.entrypoint)
        os.chmod(pth, 0o777)

    def generate_compose(self, depends_on=None):
        compose = Compose.New(self.name)
        compose.image = "shynuu/sa-ntn:trunks"
        compose.container_name = self.name
        compose.entrypoint = "./entrypoint.sh"
        compose.volumes = [
            f"./configuration/{self.name}.yaml:/trunks/trunks.yaml",
            f"./containers/{self.name}.sh:/trunks/entrypoint.sh",
        ]
        compose.networks = self.networks
        compose.cap_add = ["NET_ADMIN"]
        if depends_on != None:
            compose.depends_on = depends_on
        return compose.generate()


class CLASSIFIER(Service):

    configuration = "config/components/classifier.yaml"
    compose = "config/containers/classifier.yaml"

    def __init__(self, name):
        super().__init__(name)
        self.ingress = []
        self.egress = []
        self.ran_routes = []
        self.cn_routes = []
        self.read_configuration()

    def configure(self, satellite_network: Network):
        self.configuration['ClassifierName'] = self.name.upper()
        self.sbi = self.attach_network(satellite_network)
        self.configuration['sbi']['registerIPv4'] = str(self.sbi)
        self.configuration['sbi']['bindingIPv4'] = str(self.sbi)
        return self.sbi

    def configure_networks(self, left_network: Network, right_network: Network):
        self.attach_network(left_network)
        self.attach_network(right_network)

    def attach_ingress(self, ingr: Network):
        self.ingress.append(self.attach_network(ingr))

    def attach_egress(self, egr: Network):
        self.egress.append(self.attach_network(egr))

    def find_network(self, ip_v: ipaddress.IPv4Address,  classifier_ips: List[ipaddress.IPv4Address]):
        ip_network = ipaddress.ip_interface(f"{ip_v}/24").network
        for ip in classifier_ips:
            if ip in ip_network:
                return ip

    def configure_routes_ran(self, links: List[Ntn], upfs: List[UPF], trunks: List[TRUNKS], amf: AMF, default_slice: int):
        i = 0
        j = 0
        for l in links:
            if i == default_slice:
                ip_network = ipaddress.ip_interface(f"{amf.n2}/24").network
                self.ran_routes.append((trunks[i].st, ip_network))
            for s in l.slices:
                ip_network = ipaddress.ip_interface(
                    f"{upfs[j].gtp}/24").network
                self.ran_routes.append((trunks[i].st, ip_network))
                j += 1
            i += 1

    def configure_routes_cn(self, links: List[Ntn], upfs: List[UPF], trunks: List[TRUNKS], amf: AMF, gnb: GNB, default_slice: int):
        i = 0
        j = 0
        value = 10
        for l in links:
            link = (value, f"link_{i}", trunks[i].gw, [])
            if i == default_slice:
                link[3].append(amf.n2)
            for s in l.slices:
                link[3].append(upfs[j].gtp)
                j += 1
            self.cn_routes.append(link)
            value += 10
            i += 1

    def generate(self, configuration: str, containers: str):
        self.generate_configuration(configuration)

    def generate_compose(self, depends_on=None):
        compose = Compose.New(self.name)
        compose.image = "shynuu/sa-ntn:classifier"
        compose.container_name = self.name
        compose.entrypoint = "./entrypoint.sh"
        compose.volumes = [
            f"./configuration/{self.name}.yaml:/classifier/classifier.yaml",
            f"./containers/{self.name}.sh:/classifier/entrypoint.sh",
        ]
        compose.environment = {"GIN_MODE": "release"}
        compose.cap_add = ["NET_ADMIN"]
        compose.networks = self.networks
        if depends_on != None:
            compose.depends_on = depends_on
        return compose.generate()

    def generate_entrypoint(self, same: List[ipaddress.IPv4Address], sym: List[ipaddress.IPv4Address], apps: List[Application], ran: bool):
        s = ["#!/bin/bash"]
        if ran:
            for r in self.ran_routes:
                s.append(f"ip route add {r[1]} via {r[0]}")
        else:
            i = 0
            for r in self.cn_routes:
                s.append(f"echo {r[0]} link_{i} >> /etc/iproute2/rt_tables")
                for d in r[3]:
                    s.append(f"ip rule add from {d} lookup link_{i}")
                s.append(f"ip route add default via {r[2]} table link_{i}")
                i += 1

        for interface in self.ingress:
            q = []
            s.append(f"ETH=$(ip a | grep {interface} | awk '{{print ($7)}}')")
            for app in apps:
                if (app.terrestrial_dscp, app.ntn_dscp) not in q:
                    s.append(
                        f"iptables -t mangle -A POSTROUTING -o $ETH -p udp --dport 2152 --sport 2152 -m dscp --dscp {hex(app.terrestrial_dscp)} -j DSCP --set-dscp {hex(app.ntn_dscp)}")
                    q.append((app.terrestrial_dscp, app.ntn_dscp))
        for interface in self.egress:
            q = []
            s.append(f"ETH=$(ip a | grep {interface} | awk '{{print ($7)}}')")
            for app in apps:
                if (app.terrestrial_dscp, app.ntn_dscp) not in q:
                    s.append(
                        f"iptables -t mangle -A POSTROUTING -o $ETH -p udp --dport 2152 --sport 2152 -m dscp --dscp {hex(app.ntn_dscp)} -j DSCP --set-dscp {hex(app.terrestrial_dscp)}")
                    q.append((app.terrestrial_dscp, app.ntn_dscp))
        # k = 0
        # for interface in self.ingress:
        #     s.append(f"ETH=$(ip a | grep {interface} | awk \'{{print($7)}}\')")
        #     s.append(f"ip link add ifb{k} type ifb")
        #     s.append(f"ip link set dev ifb{k} up")
        #     s.append(f"tc qdisc add dev ifb{k} root sfq perturb 10")
        #     s.append("tc qdisc add dev $ETH handle ffff: ingress")
        #     s.append(
        #         f"tc filter add dev $ETH parent ffff: u32 match u32 0 0 action mirred egress redirect dev ifb{k}")
        #     k += 1
        s.append(f"classifier-runtime --config classifier.yaml")
        self.entrypoint = "\n".join(s)

    def write_entrypoint(self, path):
        pth = f"{path}/{self.name}.sh"
        with codecs.open(pth, "w", encoding="utf8") as entrypoint:
            entrypoint.write(self.entrypoint)
        os.chmod(pth, 0o777)


class NTNQOF(Service):

    configuration = "config/components/ntncfg.yaml"
    compose = "config/containers/ntn.yaml"

    def __init__(self, name):
        super().__init__(name)
        self.read_configuration()

    def configure(self, satellite_network: Network, nrf: ipaddress.IPv4Address):
        self.configuration['configuration']['NtnName'] = self.name.upper()
        self.sbi = self.configure_sba_ip(satellite_network)

        self.configuration['configuration']['nrfUri'] = f"http://{nrf}:8000"
        return self.sbi

    def configure_qos(self, applications: List[Application]):
        self.configuration['configuration']['qos'] = {}
        for app in applications:
            self.configuration['configuration']['qos'][HexInt(
                app.terrestrial_dscp)] = HexInt(app.ntn_dscp)

    def find_network(self, ip_v: ipaddress.IPv4Address,  classifier_ips: List[ipaddress.IPv4Address]):
        ip_network = ipaddress.ip_interface(f"{ip_v}/24").network
        for ip in classifier_ips:
            if ip in ip_network:
                return ip

    def configure_awareness(self, slice_aware: bool):
        self.configuration['configuration']['slice_aware'] = slice_aware

    def configure_slice(self, links: List[Ntn], slices: List[Slice], trunks: List[TRUNKS], classifier_ran: CLASSIFIER, classifier_cn: CLASSIFIER):
        sl = []
        j = 0
        k = 0
        for l in links:
            for s in links[j].slices:
                ran_endpoint = self.find_network(
                    trunks[j].st, classifier_ran.egress)
                cn_endpoint = self.find_network(
                    trunks[j].gw, classifier_cn.egress)
                sl.append(
                    {
                        "id": k,
                        "classifier-ran-endpoint": str(ran_endpoint),
                        "classifier-cn-endpoint": str(cn_endpoint),
                        "forward": s.Theta.beta,
                        "return": s.Theta.mu,
                    }
                )
                k += 1
            j += 1
        self.configuration['configuration']['slice'] = sl

    def configure_classifier(self, ran: CLASSIFIER, cn: CLASSIFIER):
        self.configuration['configuration']['classifiers'] = {}
        self.configuration['configuration']['classifiers'] = {
            'ran':
            {'registerIPv4': str(ran.sbi),
             'port': 9090,
             'ingress': [
                str(add) for add in ran.ingress],
             'egress': [
                str(add) for add in ran.egress],
             },
            'cn':
            {'registerIPv4': str(cn.sbi),
             'port': 9090,
             'ingress': [
                str(add) for add in cn.ingress],
             'egress': [
                str(add) for add in cn.egress],
             },
        }

    def generate(self, configuration: str, containers: str):
        self.generate_configuration(configuration)

    def generate_compose(self, depends_on=None):
        compose = Compose.New(self.name)
        compose.image = "shynuu/sa-ntn:ntnqof"
        compose.container_name = self.name
        compose.command = f"--ntncfg {self.name}.yaml"
        compose.volumes = [
            f"./configuration/{self.name}.yaml:/ntnqof/{self.name}.yaml",
        ]
        compose.environment = {"GIN_MODE": "release"}
        compose.networks = self.networks
        if depends_on != None:
            compose.depends_on = depends_on
        return compose.generate()


class QOF(Service):

    configuration = "config/components/qofcfg.yaml"
    compose = "config/containers/qof.yaml"

    def __init__(self, name):
        super().__init__(name)
        self.read_configuration()

    def configure(self, sba: Network, nrf: ipaddress.IPv4Address, ntn: ipaddress.IPv4Address):
        self.configuration['configuration']['qofName'] = self.name.upper()
        net = self.configure_sba_ip(sba)

        self.configuration['configuration']['nrfUri'] = f"http://{nrf}:8000"
        self.configuration['configuration']['ntnUri'] = f"http://{ntn}:8000"
        return net

    def configure_network(self, ntn: Network, sbi: Network):
        self.attach_network(ntn)

    def configure_qos(self, applications: List[Application]):
        self.configuration['configuration']['qos'] = {}
        for app in applications:
            self.configuration['configuration']['qos'][app.qi] = HexInt(
                app.terrestrial_dscp)

    def configure_slice(self, gnb: GNB, upfs: List[UPF], slices: List[Slice], amf: AMF, default_slice: int):
        self.configuration['configuration']['slice'] = [
            {
                "sNssai": slices[j].generate_conf(),
                "ran": str(gnb.ran_net),
                "cn": str(upfs[j].gtp),
                "id": j,
                "default": True if j == default_slice else False,
                "amf": str(amf.n2) if j == default_slice else "0.0.0.0",
            }
            for j in range(len(slices))
        ]

    def generate(self, configuration: str, containers: str):
        self.generate_configuration(configuration)

    def generate_compose(self, depends_on=None):
        compose = Compose.New(self.name)
        compose.image = "shynuu/sa-ntn:qof"
        compose.container_name = self.name
        # compose.command = f"--qofcfg {self.name}.yaml"
        compose.volumes = [
            f"./configuration/{self.name}.yaml:/qof/{self.name}.yaml",
        ]
        compose.environment = {"GIN_MODE": "release"}
        compose.networks = self.networks
        if depends_on != None:
            compose.depends_on = depends_on
        return compose.generate()


class MONGO(Service):

    def __init__(self, name):
        super().__init__(name)

    def configure(self, sba: Network):
        return self.attach_network(sba)

    def generate_compose(self):
        compose = Compose.New(self.name)
        compose.image = "mongo"
        compose.container_name = "mongo"
        compose.command = "mongod --port 27017"
        compose.expose = ["27017"]
        compose.volumes = ["dbdata:/data/db"]
        compose.networks = self.networks
        return compose.generate()
