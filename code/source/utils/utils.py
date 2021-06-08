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
import subprocess
from typing import List
from ruamel import yaml


class HexInt(int):
    pass


def representer(dumper, data):
    return yaml.representer.ScalarNode('tag:yaml.org,2002:int', f"0x{data:02x}")


def find_network(source: ipaddress.IPv4Address,  pool: List[ipaddress.IPv4Address]) -> ipaddress.IPv4Address:
    ip_network = ipaddress.ip_interface(f"{source}/24").network
    for ip in pool:
        if ip in ip_network:
            return ip


def start_pcap_capture(path: str):
    cmd = f"sudo tcpdump --interface any -w {path}"
    subprocess.call(cmd, shell=True)


def stop_pcap_capture():
    cmd = "sudo killall -9 tcpdump"
    subprocess.call(cmd, shell=True)
