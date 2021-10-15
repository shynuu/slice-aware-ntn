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


import ipaddress
from typing import List
from ruamel import yaml
from . import Service, Repository, CService, CEntrypoint
from ..utils.utils import HexInt, representer, find_network
import pprint
import codecs

APPLICATION_WEB = 0x01
APPLICATION_STREAMING = 0x02
APPLICATION_VOIP = 0x03
MNC = "208"
MCC = "93"


class Theta(object):

    def __init__(self, lamba, delta, mu, beta, sigma):
        self.lamba = lamba
        self.delta = delta
        self.mu = mu
        self.beta = beta
        self.sigma = sigma


class Application(object):

    def __init__(self, name: str):
        self.name = name
        self.qi = None
        self.port = None
        self.ntn_dscp = None
        self.terrestrial_dscp = None
        self.data_rate = None
        self.pdb = None
        self.code = None
        self.results = "results"

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

    def __init__(self, data_rate=128):
        super().__init__("VoIP")
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

    def __init__(self, data_rate=5):
        super().__init__("Streaming")
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

    def __init__(self, data_rate=3):
        super().__init__("Web")
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

    def set_ue_network(self, network):
        self.ue_network = network

    def set_data_network(self, network):
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


class User(object):

    def __init__(self):
        self.applications = []
        self.slices = []

    def attach_application(self, application: Application):
        self.slices.append(application)
        return application


# Services


class SERVER(Service):

    docker_image = "shynuu/sa-ntn:application"

    def __init__(self, name: str, repository: Repository) -> None:
        super().__init__(name, repository)
        self.application: Application = None
        self.index: int = None

    def configure(self, repository: Repository) -> None:
        """Configure the SERVER service"""
        pass

    def configure_application(self, index: int, application: Application):
        """Link the `application` with the `SERVER`"""
        self.application = application
        self.index = index

    def configure_compose(self, repository: Repository) -> None:
        """Add a Compose configuration to the SERVER"""

        compose = CService.New(self.name, self.docker_image)
        compose.tty = True
        compose.entrypoint = f"./entrypoint.sh"
        compose.volumes = [
            f"{repository.containers_folder}/{self.name}.sh:/application/entrypoint.sh",
            f"{repository.results_folder}:/application/results"
        ]
        compose.environment = {"GIN_MODE": "release"}
        compose.networks = self.networks
        compose.cap_add = ["NET_ADMIN"]
        self.compose = compose

    def configure_entrypoint(self, repository: Repository) -> None:
        """Configure the entrypoint for the SERVER"""

        keys = list(self.networks.keys())
        ep = CEntrypoint.New()
        ep.add_line(self.application.generate_server(
            f"{self.networks.get(keys[0])}", self.index, self.name))
        self.entrypoint = ep


class UE(Service):

    configuration_file = "uecfg.yaml"
    docker_image = "shynuu/sa-ntn:ue"

    def __init__(self, name: str, repository: Repository) -> None:
        super().__init__(name, repository)
        self.applications: List[CEntrypoint] = []

    def configure(self, repository: Repository) -> None:
        """Configure the UE service"""

        slices = repository.get_misc("slices")
        radio_link_sim = self.networks.get("ran-link-sim")
        gnb = repository.get_service("gnb")
        index = int(self.name.strip("ue-"))

        self.configuration["supi"] = f"imsi-{MNC}{MCC}{index+1:010d}"
        self.configuration['gnbSearchList'] = [
            str(gnb.networks.get("ran-link-sim"))]
        self.configuration["sessions"] = [
            {
                "type": 'IPv4',
                "apn": s.data_network,
                "slice": {
                        "sst": HexInt(int(s.sst, 16)),
                        "sd": HexInt(int(s.sd, 16)),
                },
                "emergency": False,
            } for s in slices
        ]
        self.configuration["configured-nssai"] = [
            {
                "sst": HexInt(int(s.sst, 16)),
                "sd": HexInt(int(s.sd, 16)),
            }
            for s in slices
        ]

    def configure_compose(self, repository: Repository) -> None:
        """Add a Compose configuration to the UE"""

        slices = repository.get_misc("slices")
        index: int = int(self.name.split("-")[1])

        compose = CService.New(self.name, self.docker_image)

        compose.command = f"--config ue.yaml"
        compose.volumes = [
            f"{repository.output_configuration_folder}/{self.name}.yaml:/ue/ue.yaml",
            f"{repository.results_folder}:/ue/results",
        ]

        i = 0
        for sl in slices:
            for server in sl.servers[index]:
                if f"{repository.containers_folder}/{self.name}-slice-{i}-app.sh:/ue/slice-{i}-app.sh" not in compose.volumes:
                    compose.volumes.append(
                        f"{repository.containers_folder}/{self.name}-slice-{i}-app.sh:/ue/slice-{i}-app.sh")
            i += 1

        compose.cap_add = ["NET_ADMIN"]
        compose.devices = ["/dev/net/tun"]
        compose.networks = self.networks
        depends_on: List[str] = ["gnb"]
        index: int = int(self.name.split("-")[1])
        if index > 0:
            depends_on.extend([f"ue-{i}" for i in range(index)])
        compose.depends_on = depends_on
        self.compose = compose

    def configure_entrypoint(self, repository: Repository) -> None:
        """
        Configure the entrypoints for the UE
        Generates the scripts for running each application
        """

        slices = repository.get_misc("slices")
        index: int = int(self.name.split("-")[1])

        i = 0
        for sl in slices:
            ep = CEntrypoint.New()
            bind = f"BIND_0"
            ep.add_line(f"BIND_0=$1")
            ep.add_line(f"ip route add {sl.network} via $BIND_0")
            for server in sl.servers[index]:
                keys = list(server.networks.keys())
                ep.add_line(server.application.generate_client(
                    f"${bind}", f"{server.networks.get(keys[0])}", self.name, i, sl.end-sl.start))
            self.applications.append(ep)
            i += 1

    def write_entrypoint(self, repository: Repository) -> None:
        """Write entrypoint applications"""
        i = 0
        for app in self.applications:
            app.write(f"{repository.containers_folder}",
                      f"{self.name}-slice-{i}-app")
            i += 1


class POPULATE(Service):

    configuration_file = "populatecfg.yaml"
    docker_image = "shynuu/sa-ntn:populate"

    def configure(self, repository: Repository) -> None:
        """Configure the POPULATE service"""

        sbi = self.networks.get("sbi")
        slices: List[Slice] = repository.get_misc("slices")
        ues: List[UE] = repository.get_misc("ues")
        mongo = repository.get_service("mongo")

        self.configuration["mongo"]["url"] = f"mongodb://{str(mongo.networks.get('sbi'))}:27017"
        self.configuration["slices"] = [
            {
                "sst": int(s.sst),
                "sd": s.sd,
                "varqi": 9,
                "dnn": s.data_network,
            }
            for s in slices
        ]
        self.configuration["imsi"] = [
            f"imsi-{MNC}{MCC}{index:010d}" for index, ue in enumerate(ues, start=1)]

    def configure_compose(self, repository: Repository) -> None:
        """Add a Compose configuration to the POPULATE"""

        compose = CService.New(self.name, self.docker_image)
        compose.command = f"--config populatecfg.yaml"
        compose.volumes = [
            f"{repository.output_configuration_folder}/{self.name}.yaml:/populate/populatecfg.yaml",
        ]
        compose.environment = {"GIN_MODE": "release"}
        compose.networks = self.networks
        compose.depends_on = ["mongo", "amf", "nrf"]
        self.compose = compose


class UPF(Service):

    configuration_file = "upfcfg.yaml"
    docker_image = "shynuu/sa-ntn:upf"

    def configure(self, repository: Repository) -> None:
        """Configure the UPF service"""

        to_strip = "classifier-cn-dp-"
        for network in self.networks:
            if network.startswith(to_strip):
                gtp = self.networks.get(network)
                i = int(network.strip(to_strip))

        pfcp = self.networks.get("pfcp")
        slices: List[Slice] = repository.get_misc("slices")

        self.configuration['configuration']['pfcp'] = [
            {'addr': str(pfcp)}]
        self.configuration['configuration']['gtpu'] = [
            {'addr': str(gtp)}]
        self.configuration['configuration']['dnn_list'] = [
            {'dnn': slices[i].data_network, 'cidr': str(slices[i].ue_network)}]

    def configure_compose(self, repository: Repository) -> None:
        """Add a Compose configuration to the UPF"""

        compose = CService.New(self.name, self.docker_image)
        compose.entrypoint = "./entrypoint.sh"
        compose.volumes = [
            f"{repository.output_configuration_folder}/{self.name}.yaml:/upf/upfcfg.yaml",
            f"{repository.containers_folder}/{self.name}.sh:/upf/entrypoint.sh",
            f"{repository.results_folder}:/upf/results",
        ]
        compose.networks = self.networks
        compose.ports = ["8805:8805/udp"]
        compose.cap_add = ["NET_ADMIN"]
        self.compose = compose

    def configure_entrypoint(self, repository: Repository) -> None:
        """Configure the entrypoint for the UPF"""

        for network in self.networks:
            if network.startswith("classifier-cn-dp"):
                index = network.replace("classifier-cn-dp-", "")

        classifier_cn = repository.get_service("classifier-cn")
        gnb = repository.get_service("gnb")
        slices = repository.get_misc("slices")

        ingress = [classifier_cn.networks.get(
            f"classifier-cn-dp-{j}") for j in range(len(slices))]
        ingress.append(classifier_cn.networks.get(f"sbi"))

        classifier_ip = find_network(
            self.networks.get(f"classifier-cn-dp-{index}"), ingress)

        ep = CEntrypoint.New()

        ep.add_line(
            f"ETH=$(ip a | grep {self.networks.get(f'data-network-slice-{index}')} | awk \'{{print($7)}}\')")
        ep.add_line("iptables -t nat -A POSTROUTING -o $ETH -j MASQUERADE")
        ran_network = ipaddress.IPv4Interface(
            f"{gnb.networks.get('classifier-ran')}/24").network
        ep.add_line(f"ip route add {ran_network} via {classifier_ip}")
        ep.add_line(f"free5gc-upfd -f upfcfg.yaml")
        self.entrypoint = ep


class AMF(Service):

    configuration_file = "amfcfg.yaml"
    docker_image = "shynuu/sa-ntn:amf"

    def configure(self, repository: Repository) -> None:
        """Configure the AMF service"""

        sbi = self.networks.get("sbi")
        nrf = repository.get_service("nrf").networks.get("sbi")
        slices: List[Slice] = repository.get_misc("slices")

        self.configuration['configuration']['amfName'] = self.name.upper()
        self.configuration['configuration']['nrfUri'] = f"http://{nrf}:8000"
        self.configuration['configuration']['sbi']['registerIPv4'] = str(sbi)
        self.configuration['configuration']['sbi']['bindingIPv4'] = str(sbi)
        self.configuration['configuration']['ngapIpList'] = [str(sbi)]
        self.configuration['configuration']['plmnSupportList'][0]['snssaiList'] = [
            s.generate_conf() for s in slices]
        self.configuration['configuration']['supportDnnList'] = [
            s.data_network for s in slices]

    def configure_compose(self, repository: Repository) -> None:
        """Add a Compose configuration to the AMF"""

        compose = CService.New(self.name, self.docker_image)
        compose.entrypoint = f"./entrypoint.sh"
        compose.volumes = [
            f"{repository.output_configuration_folder}/{self.name}.yaml:/amf/amfcfg.yaml",
            f"{repository.containers_folder}/{self.name}.sh:/amf/entrypoint.sh"
        ]
        compose.environment = {"GIN_MODE": "release"}
        compose.networks = self.networks
        compose.cap_add = ["NET_ADMIN"]
        compose.depends_on = ["nrf"]
        compose.ports = ["38412:38412/sctp"]
        self.compose = compose

    def configure_entrypoint(self, repository: Repository) -> None:
        """Configure the entrypoint for the AMF"""

        slices = repository.get_misc("slices")
        classifier_cn = repository.get_service("classifier-cn")
        gnb = repository.get_service("gnb")

        ccn_ingress = [classifier_cn.networks.get(
            f"classifier-cn-dp-{j}") for j in range(len(slices))]
        ccn_ingress.append(classifier_cn.networks.get(f"sbi"))

        classifier_ip = find_network(self.networks.get("sbi"), ccn_ingress)

        ep = CEntrypoint.New()
        ran_network = ipaddress.IPv4Interface(
            f"{gnb.networks.get('classifier-ran')}/24").network
        ep.add_line(f"ip route add {ran_network} via {classifier_ip}")
        ep.add_line(f"amf --amfcfg amfcfg.yaml")
        self.entrypoint = ep


class NSSF(Service):

    configuration_file = "nssfcfg.yaml"
    docker_image = "shynuu/sa-ntn:nssf"

    def configure(self, repository: Repository) -> None:
        """Configure the NSSF service"""

        sbi = self.networks.get("sbi")
        nrf = repository.get_service("nrf").networks.get("sbi")
        slices: List[Slice] = repository.get_misc("slices")

        self.configuration['configuration']['nssfName'] = self.name.upper()
        self.configuration['configuration']['nrfUri'] = f"http://{nrf}:8000"
        self.configuration['configuration']['sbi']['registerIPv4'] = str(sbi)
        self.configuration['configuration']['sbi']['bindingIPv4'] = str(sbi)
        self.configuration['configuration']['supportedNssaiInPlmnList'][0]['supportedSnssaiList'] = [
            s.generate_conf() for s in slices]
        self.configuration['configuration']['nsiList'] = [
            {
                'snssai': s.generate_conf(),
                'nsiInformationList':
                [{
                    'nrfId': f"http://{nrf}:8000/nnrf-nfm/v1/nf-instances",
                    'nsiId': (lambda index: 10 + index)(i),
                }]
            }
            for i, s in enumerate(slices, start=1)
        ]

        self.configuration['configuration']['amfSetList'][0][
            'nrfAmfSet'] = f"http://{nrf}:8000/nnrf-nfm/v1/nf-instances"
        self.configuration['configuration']['amfSetList'][0]["supportedNssaiAvailabilityData"][0]['supportedSnssaiList'] = [
            s.generate_conf() for s in slices
        ]
        self.configuration['configuration']['taList'][0]['supportedSnssaiList'] = [
            s.generate_conf() for s in slices
        ]

    def configure_compose(self, repository: Repository) -> None:
        """Add a Compose configuration to the NSSF"""

        compose = CService.New(self.name, self.docker_image)
        compose.command = f"--nssfcfg nssfcfg.yaml"
        compose.volumes = [
            f"{repository.output_configuration_folder}/{self.name}.yaml:/nssf/nssfcfg.yaml",
        ]
        compose.environment = {"GIN_MODE": "release"}
        compose.networks = self.networks
        compose.depends_on = ["nrf"]
        self.compose = compose


class GNB(Service):

    configuration_file = "gnbcfg.yaml"
    docker_image = "shynuu/sa-ntn:gnb"

    def configure(self, repository: Repository) -> None:
        """Configure the GNB service"""

        ran_ip = self.networks.get("classifier-ran")
        radio_link_sim = self.networks.get("ran-link-sim")

        amf = repository.get_service("amf").networks.get("sbi")
        slices: List[Slice] = repository.get_misc("slices")

        self.configuration["linkIp"] = str(radio_link_sim)
        self.configuration["ngapIp"] = str(ran_ip)
        self.configuration["gtpIp"] = str(ran_ip)
        self.configuration['amfConfigs'] = [
            {"address": str(amf), "port": 38412}]

        self.configuration["slices"] = [
            {"sst": HexInt(int(s.sst, 16)), "sd": HexInt(int(s.sd, 16))} for s in slices]

    def configure_compose(self, repository: Repository) -> None:
        """Add a Compose configuration to the GNB"""

        trunks = repository.get_misc("trunks")

        compose = CService.New(self.name, self.docker_image)
        compose.entrypoint = f"./entrypoint.sh"
        compose.volumes = [
            f"{repository.output_configuration_folder}/{self.name}.yaml:/ueransim/gnb.yaml",
            f"{repository.containers_folder}/{self.name}.sh:/ueransim/entrypoint.sh"
        ]
        compose.networks = self.networks
        compose.cap_add = ["NET_ADMIN"]
        d = ["nrf", "amf", "smf", "pcf", "ausf", "qof",
             "ntnqof", "classifier-ran", "classifier-cn"]
        d.extend([trunk.name for trunk in trunks])
        compose.depends_on = d
        self.compose = compose

    def configure_entrypoint(self, repository: Repository) -> None:
        """Configure the entrypoint for the CLASSIFIER"""

        amf = repository.get_service("amf")
        upfs = repository.get_misc("upfs")
        classifier_ip = find_network(self.networks.get(
            "classifier-ran"), [repository.get_service("classifier-ran").networks.get("classifier-ran")])

        ep = CEntrypoint.New()

        ep.add_line(
            f"gtp-dscp --ipv4 {self.networks.get('classifier-ran')} --offset 16")
        sbi_network = ipaddress.IPv4Interface(
            f"{amf.networks.get('sbi')}/24").network
        ep.add_line(f"ip route add {sbi_network} via {classifier_ip}")
        for index, upf in enumerate(upfs, start=0):
            upf_network = ipaddress.IPv4Interface(
                f"{upf.networks.get(f'classifier-cn-dp-{index}')}/24").network
            ep.add_line(f"ip route add {upf_network} via {classifier_ip}")
        ep.add_line("sleep 6")
        ep.add_line(f"nr-gnb --config gnb.yaml")
        self.entrypoint = ep


class SMF(Service):

    configuration_file = "smfcfg.yaml"
    uerouting = "uerouting.yaml"
    docker_image = "shynuu/sa-ntn:smf"

    def __init__(self, name: str, repository: Repository) -> None:
        super().__init__(name, repository)
        path = f"{repository.configurations_folder}/{self.uerouting}"
        with codecs.open(path, mode="r", encoding="utf8") as f:
            self.uerouting = yaml.load(
                f.read(), Loader=yaml.RoundTripLoader)

    def configure(self, repository: Repository) -> None:
        """Configure the SMF service"""

        sbi = self.networks.get("sbi")
        pfcp = self.networks.get("pfcp")

        nrf = repository.get_service("nrf").networks.get("sbi")
        qof = repository.get_service("qof").networks.get("sbi")

        gnb = repository.get_service("gnb")
        upfs = repository.get_misc("upfs")

        slices: List[Slice] = repository.get_misc("slices")

        self.configuration['configuration']['smfName'] = self.name.upper()
        self.configuration['configuration']['sbi']['registerIPv4'] = str(sbi)
        self.configuration['configuration']['sbi']['bindingIPv4'] = str(sbi)
        self.configuration['configuration']['nrfUri'] = f"http://{nrf}:8000"
        self.configuration["configuration"]["qofUri"] = f"http://{qof}:8090"
        self.configuration["configuration"]["pfcp"]["addr"] = str(pfcp)

        self.configuration["configuration"]["snssaiInfos"] = [
            {
                "sNssai": s.generate_conf(),
                "dnnInfos": [
                    {
                        "dnn": s.data_network,
                        "dns":
                        {
                            "ipv4": "8.8.8.8",
                        },
                        # "ueSubnet": str(s.ue_network)
                    }
                ]
            }
            for s in slices
        ]

        self.configuration["configuration"]["userplane_information"]["up_nodes"] = {
        }
        self.configuration["configuration"]["userplane_information"]["up_nodes"][gnb.name] = {
            "type": "AN",
            "an_ip": str(gnb.networks.get("classifier-ran"))
        }

        for j in range(len(upfs)):
            self.configuration["configuration"]["userplane_information"]["up_nodes"][upfs[j].name] = {
                "type": "UPF",
                "node_id": str(upfs[j].networks.get("pfcp")),
                "sNssaiUpfInfos":
                [
                    {
                        "sNssai": slices[j].generate_conf(),
                        "dnnUpfInfoList": [
                            {
                                "dnn": slices[j].data_network,
                                # Should be here if new version of free5gc
                                "pools": [
                                    {"cidr": str(slices[j].ue_network)}
                                ]
                            }
                        ]
                    }
                ],
                "interfaces":
                [
                    {
                        "interfaceType": "N3",
                        "endpoints": [
                            str(upfs[j].networks.get(f"classifier-cn-dp-{j}"))
                        ],
                        "networkInstance": slices[j].data_network,
                    }
                ]
            }

        self.configuration["configuration"]["userplane_information"]["links"] = [
            {"A": gnb.name, "B": upf.name} for upf in upfs
        ]

    def write_configuration(self, folder_path: str) -> None:
        super().write_configuration(folder_path)
        path = f"{folder_path}/uerouting.yaml"
        yam = yaml.YAML()
        yam.indent(sequence=4, offset=2)
        with codecs.open(path, "w", encoding="utf-8") as uerouting:
            yam.representer.add_representer(HexInt, representer)
            yam.dump(self.uerouting,  uerouting)

    def configure_compose(self, repository: Repository) -> None:
        """Add a Compose configuration to the SMF"""

        compose = CService.New(self.name, self.docker_image)
        compose.command = f"--smfcfg smfcfg.yaml --uerouting uerouting.yaml"
        compose.volumes = [
            f"{repository.output_configuration_folder}/{self.name}.yaml:/smf/smfcfg.yaml",
            f"{repository.output_configuration_folder}/uerouting.yaml:/smf/uerouting.yaml",
        ]
        compose.networks = self.networks
        compose.cap_add = ["NET_ADMIN"]
        compose.ports = ["8805:8805/udp"]
        compose.depends_on = ["nrf"]
        self.compose = compose


class AUSF(Service):

    configuration_file = "ausfcfg.yaml"
    docker_image = "shynuu/sa-ntn:ausf"

    def configure(self, repository: Repository) -> None:
        """Configure the AUSF service"""

        sbi = self.networks.get("sbi")
        nrf = repository.get_service("nrf").networks.get("sbi")

        self.configuration['configuration']['sbi']['registerIPv4'] = str(sbi)
        self.configuration['configuration']['sbi']['bindingIPv4'] = str(sbi)
        self.configuration['configuration']['nrfUri'] = f"http://{nrf}:8000"

    def configure_compose(self, repository: Repository) -> None:
        """Add a Compose configuration to the AUSF"""

        compose = CService.New(self.name, self.docker_image)
        compose.command = f"--ausfcfg ausfcfg.yaml"
        compose.volumes = [
            f"{repository.output_configuration_folder}/{self.name}.yaml:/ausf/ausfcfg.yaml",
        ]
        compose.environment = {"GIN_MODE": "release"}
        compose.networks = self.networks
        compose.depends_on = ["nrf"]
        self.compose = compose


class NRF(Service):

    configuration_file = "nrfcfg.yaml"
    docker_image = "shynuu/sa-ntn:nrf"

    def configure(self, repository: Repository) -> None:
        """Configure the NRF service"""

        mongo = repository.get_service("mongo").networks.get("sbi")
        sbi = self.networks.get("sbi")

        self.configuration['configuration']['sbi']['registerIPv4'] = str(sbi)
        self.configuration['configuration']['sbi']['bindingIPv4'] = str(sbi)
        self.configuration['configuration']['MongoDBUrl'] = f"mongodb://{mongo}:27017"

    def configure_compose(self, repository: Repository) -> None:
        """Add a Compose configuration to the NRF"""

        compose = CService.New(self.name, self.docker_image)
        compose.command = f"--nrfcfg nrfcfg.yaml"
        compose.volumes = [
            f"{repository.output_configuration_folder}/{self.name}.yaml:/nrf/nrfcfg.yaml",
        ]
        compose.environment = {"GIN_MODE": "release"}
        compose.networks = self.networks
        compose.depends_on = ["mongo"]
        self.compose = compose


class PCF(Service):

    configuration_file = "pcfcfg.yaml"
    docker_image = "shynuu/sa-ntn:pcf"

    def configure(self, repository: Repository) -> None:
        """Configure the AUSF service"""

        sbi = self.networks.get("sbi")
        nrf = repository.get_service("nrf").networks.get("sbi")
        mongo = repository.get_service("mongo").networks.get("sbi")

        self.configuration['configuration']['pcfName'] = self.name.upper()
        self.configuration['configuration']['sbi']['registerIPv4'] = str(sbi)
        self.configuration['configuration']['sbi']['bindingIPv4'] = str(sbi)
        self.configuration['configuration']['mongodb'][
            'url'] = f"mongodb://{mongo}:27017"
        self.configuration['configuration']['nrfUri'] = f"http://{nrf}:8000"

    def configure_compose(self, repository: Repository) -> None:
        """Add a Compose configuration to the PCF"""

        compose = CService.New(self.name, self.docker_image)
        compose.command = f"--pcfcfg pcfcfg.yaml"
        compose.volumes = [
            f"{repository.output_configuration_folder}/{self.name}.yaml:/pcf/pcfcfg.yaml",
        ]
        compose.environment = {"GIN_MODE": "release"}
        compose.networks = self.networks
        compose.cap_add = ["NET_ADMIN"]
        compose.depends_on = ["nrf"]
        self.compose = compose


class UDM(Service):

    configuration_file = "udmcfg.yaml"
    docker_image = "shynuu/sa-ntn:udm"

    def configure(self, repository: Repository) -> None:
        """Configure the UDM service"""

        sbi = self.networks.get("sbi")
        nrf = repository.get_service("nrf").networks.get("sbi")

        self.configuration['configuration']['sbi']['registerIPv4'] = str(sbi)
        self.configuration['configuration']['sbi']['bindingIPv4'] = str(sbi)
        self.configuration['configuration']['nrfUri'] = f"http://{nrf}:8000"

    def configure_compose(self, repository: Repository) -> None:
        """Add a Compose configuration to the UDM"""

        compose = CService.New(self.name, self.docker_image)
        compose.command = f"--udmcfg udmcfg.yaml"
        compose.volumes = [
            f"{repository.output_configuration_folder}/{self.name}.yaml:/udm/udmcfg.yaml",
        ]
        compose.environment = {"GIN_MODE": "release"}
        compose.networks = self.networks
        compose.depends_on = ["nrf"]
        self.compose = compose


class UDR(Service):

    configuration_file = "udrcfg.yaml"
    docker_image = "shynuu/sa-ntn:udr"

    def configure(self, repository: Repository) -> None:
        """Configure the UDR service"""

        mongo = repository.get_service("mongo").networks.get("sbi")
        nrf = repository.get_service("nrf").networks.get("sbi")
        sbi = self.networks.get("sbi")

        self.configuration['configuration']['nrfUri'] = f"http://{nrf}:8000"
        self.configuration['configuration']['sbi']['registerIPv4'] = str(sbi)
        self.configuration['configuration']['sbi']['bindingIPv4'] = str(sbi)
        self.configuration['configuration']['mongodb'][
            'url'] = f"mongodb://{mongo}:27017"

    def configure_compose(self, repository: Repository) -> None:
        """Add a Compose configuration to the UDR"""

        compose = CService.New(self.name, self.docker_image)
        compose.command = f"--udrcfg udrcfg.yaml"
        compose.volumes = [
            f"{repository.output_configuration_folder}/{self.name}.yaml:/udr/udrcfg.yaml",
        ]
        compose.environment = {"GIN_MODE": "release"}
        compose.networks = self.networks
        compose.depends_on = ["nrf"]
        self.compose = compose

# NTN COMPONENTS


class TRUNKS(Service):

    configuration_file = "trunks.yaml"
    docker_image = "shynuu/sa-ntn:trunks"

    def configure(self, repository: Repository) -> None:
        """Configure the TRUNKS service"""

        index = int(self.name.strip("trunks-"))
        link = repository.get_misc("links")[index]

        to_strip_st = "st-classifier-"
        to_strip_gw = "gw-classifier-"
        for network in self.networks:
            if network.startswith(to_strip_st):
                st = self.networks.get(network)
            if network.startswith(to_strip_gw):
                gw = self.networks.get(network)

        self.configuration["nic"] = {
            "st": str(st),
            "gw": str(gw)
        }
        self.configuration["bandwidth"] = {
            "forward": link.forward,
            "return": link.retur
        }
        self.configuration["delay"] = {
            "value": link.delay,
            "offset": link.jitter
        }

    def configure_compose(self, repository: Repository) -> None:
        """Add a Compose configuration to the TRUNKS"""

        compose = CService.New(self.name, self.docker_image)
        compose.entrypoint = "./entrypoint.sh"
        compose.volumes = [
            f"{repository.output_configuration_folder}/{self.name}.yaml:/trunks/trunks.yaml",
            f"{repository.containers_folder}/{self.name}.sh:/trunks/entrypoint.sh",
        ]
        compose.environment = {"GIN_MODE": "release"}
        compose.networks = self.networks
        compose.cap_add = ["NET_ADMIN"]
        compose.depends_on = ["ntnqof"]
        self.compose = compose

    def configure_entrypoint(self, repository: Repository) -> None:
        """Configure the entrypoint for TRUNKS service"""

        amf = repository.get_service("amf")
        gnb = repository.get_service("gnb")
        classifier_cn = repository.get_service("classifier-cn")
        classifier_ran = repository.get_service("classifier-ran")

        slices = repository.get_misc("slices")
        links = repository.get_misc("links")
        upfs = repository.get_misc("upfs")
        default_slice = repository.get_misc("default_slice")
        index = int(self.name.replace("trunks-", ""))

        cran_ingress = [classifier_ran.networks.get("classifier-ran")]
        cran_egress = [classifier_ran.networks.get(
            f"st-classifier-{j}") for j in range(len(links))]
        ccn_ingress = [classifier_cn.networks.get(
            f"classifier-cn-dp-{j}") for j in range(len(slices))]
        ccn_ingress.append(classifier_cn.networks.get(f"sbi"))
        ccn_egress = [classifier_cn.networks.get(
            f"gw-classifier-{j}") for j in range(len(links))]

        routes = []

        if index == default_slice:
            ip_network = ipaddress.ip_interface(
                f"{amf.networks.get('sbi')}/24").network
            gateway = find_network(self.networks.get(
                f'gw-classifier-{index}'), ccn_egress)
            routes.append((gateway, ip_network))
        k = 0
        if index > 0:
            for i in range(index):
                k += len(links[i].slices)
        for s in links[index].slices:
            # Find IP NETWORK of UPF and add Route to IP Network using the classifier CN interface
            ip_network = ipaddress.ip_interface(
                f"{upfs[k].networks.get(f'classifier-cn-dp-{k}')}/24").network
            gateway = find_network(self.networks.get(
                f'gw-classifier-{index}'), ccn_egress)
            if (gateway, ip_network) not in routes:
                routes.append((gateway, ip_network))
            k += 1

        ip_network = ipaddress.ip_interface(
            f"{gnb.networks.get('classifier-ran')}/24").network
        gateway = find_network(self.networks.get(
            f'st-classifier-{index}'), cran_egress)
        routes.append((gateway, ip_network))

        ep = CEntrypoint.New()
        for route in routes:
            ep.add_line(f"ip route add {route[1]} via {route[0]}")
        ep.add_line(f"trunks --config trunks.yaml")
        self.entrypoint = ep


class CLASSIFIER(Service):

    configuration_file = "classifier.yaml"
    docker_image = "shynuu/sa-ntn:classifier"

    def configure(self, repository: Repository) -> None:
        """Configure the CLASSIFIER service"""
        sbi = self.networks.get("satellite-control")

        self.configuration['ClassifierName'] = self.name.upper()
        self.configuration['sbi']['registerIPv4'] = str(sbi)
        self.configuration['sbi']['bindingIPv4'] = str(sbi)

    def configure_compose(self, repository: Repository) -> None:
        """Add a Compose configuration to the CLASSIFIER"""

        compose = CService.New(self.name, self.docker_image)
        compose.entrypoint = "./entrypoint.sh"
        compose.volumes = [
            f"{repository.output_configuration_folder}/{self.name}.yaml:/classifier/classifier.yaml",
            f"{repository.containers_folder}/{self.name}.sh:/classifier/entrypoint.sh",
        ]
        compose.environment = {"GIN_MODE": "release"}
        compose.networks = self.networks
        compose.cap_add = ["NET_ADMIN"]
        self.compose = compose

    def configure_entrypoint(self, repository: Repository) -> None:
        """Configure the entrypoint for the CLASSIFIER"""

        default_slice = repository.get_misc("default_slice")
        default_link = repository.get_misc("default_link")
        slices = repository.get_misc("slices")
        links = repository.get_misc("links")
        upfs = repository.get_misc("upfs")
        trunks = repository.get_misc("trunks")
        applications = repository.get_misc("applications")

        amf = repository.get_service("amf")
        gnb = repository.get_service("gnb")

        ran_routes = []
        cn_routes = []

        ingress = []
        egress = []

        t = self.name.replace("classifier-", "")

        if t == "ran":
            ingress = [self.networks.get("classifier-ran")]
            egress = [self.networks.get(
                f"st-classifier-{j}") for j in range(len(links))]
        else:
            ingress = [self.networks.get(
                f"classifier-cn-dp-{j}") for j in range(len(slices))]
            ingress.append(self.networks.get(f"sbi"))
            egress = [self.networks.get(
                f"gw-classifier-{j}") for j in range(len(links))]

        if t == "ran":
            i = 0
            j = 0
            for l in links:
                if i == default_slice:
                    ip_network = ipaddress.ip_interface(
                        f"{amf.networks.get('sbi')}/24").network
                    ran_routes.append((trunks[i].networks.get(
                        f"st-classifier-{i}"), ip_network))
                for s in l.slices:
                    ip_network = ipaddress.ip_interface(
                        f"{upfs[j].networks.get(f'classifier-cn-dp-{j}')}/24").network
                    ran_routes.append((trunks[i].networks.get(
                        f"st-classifier-{i}"), ip_network))
                    j += 1
                i += 1
        else:
            i = 0
            j = 0
            value = 10
            for l in links:
                link = (value, f"link_{i}", trunks[i].networks.get(
                    f"gw-classifier-{i}"), [])
                if i == default_slice:
                    link[3].append(amf.networks.get('sbi'))
                for s in l.slices:
                    link[3].append(upfs[j].networks.get(
                        f'classifier-cn-dp-{j}'))
                    j += 1
                cn_routes.append(link)
                value += 10
                i += 1

        ep = CEntrypoint.New()
        if t == "ran":
            for r in ran_routes:
                ep.add_line(f"ip route add {r[1]} via {r[0]}")
        else:
            i = 0
            for r in cn_routes:
                ep.add_line(f"echo {r[0]} link_{i} >> /etc/iproute2/rt_tables")
                for d in r[3]:
                    ep.add_line(f"ip rule add from {d} lookup link_{i}")
                ep.add_line(f"ip route add default via {r[2]} table link_{i}")
                i += 1

        for interface in ingress:
            q = []
            ep.add_line(
                f"ETH=$(ip a | grep {interface} | awk '{{print ($7)}}')")
            for app in applications:
                if (app.terrestrial_dscp, app.ntn_dscp) not in q:
                    ep.add_line(
                        f"iptables -t mangle -A POSTROUTING -o $ETH -p udp --dport 2152 --sport 2152 -m dscp --dscp {hex(app.terrestrial_dscp)} -j DSCP --set-dscp {hex(app.ntn_dscp)}")
                    q.append((app.terrestrial_dscp, app.ntn_dscp))

        for interface in egress:
            q = []
            ep.add_line(
                f"ETH=$(ip a | grep {interface} | awk '{{print ($7)}}')")
            for app in applications:
                if (app.terrestrial_dscp, app.ntn_dscp) not in q:
                    ep.add_line(
                        f"iptables -t mangle -A POSTROUTING -o $ETH -p udp --dport 2152 --sport 2152 -m dscp --dscp {hex(app.ntn_dscp)} -j DSCP --set-dscp {hex(app.terrestrial_dscp)}")
                    q.append((app.terrestrial_dscp, app.ntn_dscp))

        k = 0
        for interface in ingress:
            ep.add_line(
                f"ETH=$(ip a | grep {interface} | awk \'{{print($7)}}\')")
            ep.add_line(f"ip link add ifb{k} type ifb")
            ep.add_line(f"ip link set dev ifb{k} up")
            ep.add_line(f"tc qdisc add dev ifb{k} root sfq perturb 10")
            ep.add_line("tc qdisc add dev $ETH handle ffff: ingress")
            ep.add_line(
                f"tc filter add dev $ETH parent ffff: u32 match u32 0 0 action mirred egress redirect dev ifb{k}")
            k += 1
        ep.add_line(f"classifier-runtime --config classifier.yaml")

        self.entrypoint = ep


class NTNQOF(Service):

    configuration_file = "ntncfg.yaml"
    docker_image = "shynuu/sa-ntn:ntnqof"

    def configure(self, repository: Repository) -> None:

        classifier_ran: CLASSIFIER = repository.get_service("classifier-ran")
        classifier_cn: CLASSIFIER = repository.get_service("classifier-cn")
        nrf = repository.get_service("nrf").networks.get("sbi")
        sbi = self.networks.get("sbi")
        applications: List[Application] = repository.get_misc("applications")

        links = repository.get_misc("links")
        trunks = repository.get_misc("trunks")
        slices = repository.get_misc("slices")

        self.configuration['configuration']['sbi']['registerIPv4'] = str(sbi)
        self.configuration['configuration']['sbi']['bindingIPv4'] = str(sbi)
        self.configuration['configuration']['NtnName'] = self.name.upper()
        self.configuration['configuration']['nrfUri'] = f"http://{nrf}:8000"
        self.configuration['configuration']['slice_aware'] = True

        self.configuration['configuration']['qos'] = {}
        for app in applications:
            self.configuration['configuration']['qos'][HexInt(
                app.terrestrial_dscp)] = HexInt(app.ntn_dscp)

        cran_ingress = [classifier_ran.networks.get("classifier-ran")]
        cran_egress = [classifier_ran.networks.get(
            f"st-classifier-{j}") for j in range(len(links))]
        ccn_ingress = [classifier_cn.networks.get(
            f"classifier-cn-dp-{j}") for j in range(len(slices))]
        ccn_ingress.append(classifier_cn.networks.get(f"sbi"))
        ccn_egress = [classifier_cn.networks.get(
            f"gw-classifier-{j}") for j in range(len(links))]

        sl = []
        j = 0
        k = 0
        for l in links:
            for s in links[j].slices:
                ran_endpoint = find_network(
                    trunks[j].networks.get(f"st-classifier-{j}"), cran_egress)
                cn_endpoint = find_network(
                    trunks[j].networks.get(f"gw-classifier-{j}"), ccn_egress)
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

        self.configuration['configuration']['classifiers'] = {}
        self.configuration['configuration']['classifiers'] = {
            'ran':
            {'registerIPv4': str(classifier_ran.networks.get("satellite-control")),
             'port': 9090,
             'ingress': [
                str(add) for add in cran_ingress],
             'egress': [
                str(add) for add in cran_egress],
             },
            'cn':
            {'registerIPv4': str(classifier_cn.networks.get("satellite-control")),
             'port': 9090,
             'ingress': [
                str(add) for add in ccn_ingress],
             'egress': [
                str(add) for add in ccn_egress],
             },
        }

    def configure_compose(self, repository: Repository) -> None:
        """Add a Compose configuration to the NTNQOF"""

        classifiers = repository.get_misc("classifiers")

        compose = CService.New(self.name, self.docker_image)
        compose.command = "--ntncfg ntnqof.yaml"
        compose.volumes = [
            f"{repository.output_configuration_folder}/{self.name}.yaml:/ntnqof/ntnqof.yaml",
        ]
        compose.environment = {"GIN_MODE": "release"}
        compose.networks = self.networks
        compose.cap_add = ["NET_ADMIN"]
        compose.depends_on = [classifier.name for classifier in classifiers]
        self.compose = compose


class QOF(Service):

    configuration_file = "qofcfg.yaml"
    docker_image = "shynuu/sa-ntn:qof"

    def configure(self, repository: Repository) -> None:
        """Configure the QOF service"""

        sbi = self.networks.get("sbi")
        nrf = repository.get_service("nrf").networks.get("sbi")
        ntnqof = repository.get_service("ntnqof").networks.get("sbi")
        gnb = repository.get_service("gnb")
        amf = repository.get_service("amf")

        slices = repository.get_misc("slices")
        default_slice = repository.get_misc("default_slice")
        upfs = repository.get_misc("upfs")
        applications = [Web(), Streaming(), VoIP()]

        self.configuration['configuration']['sbi']['registerIPv4'] = str(sbi)
        self.configuration['configuration']['sbi']['bindingIPv4'] = str(sbi)
        self.configuration['configuration']['qofName'] = self.name.upper()
        self.configuration['configuration']['nrfUri'] = f"http://{nrf}:8000"
        self.configuration['configuration']['ntnUri'] = f"http://{ntnqof}:8000"

        self.configuration['configuration']['slice'] = [
            {
                "sNssai": slices[j].generate_conf(),
                "ran": str(gnb.networks.get("classifier-ran")),
                "cn": str(upfs[j].networks.get(f"classifier-cn-dp-{j}")),
                "id": j,
                "default": True if j == default_slice else False,
                "amf": str(amf.networks.get("sbi")) if j == default_slice else "0.0.0.0",
            }
            for j in range(len(slices))
        ]

        self.configuration['configuration']['qos'] = {}
        for app in applications:
            self.configuration['configuration']['qos'][app.qi] = HexInt(
                app.terrestrial_dscp)

    def configure_compose(self, repository: Repository) -> None:
        """Add a Compose configuration to the QOF"""

        compose = CService.New(self.name, self.docker_image)
        compose.command = "--qofcfg qofcfg.yaml"
        compose.volumes = [
            f"{repository.output_configuration_folder}/{self.name}.yaml:/qof/qofcfg.yaml",
        ]
        compose.environment = {"GIN_MODE": "release"}
        compose.networks = self.networks
        compose.depends_on = ["nrf", "ntnqof"]
        self.compose = compose


class MONGO(Service):

    docker_image = "mongo"

    def configure(self, repository: Repository) -> None:
        """Configure the MONGO service"""
        pass

    def configure_compose(self, repository: Repository) -> None:
        """Add a Compose configuration to the MONGO"""

        compose = CService.New(self.name, self.docker_image)
        compose.command = "mongod --port 27017"
        compose.expose = ["27017"]
        compose.volumes = ["dbdata:/data/db"]
        compose.networks = self.networks
        self.compose = compose
