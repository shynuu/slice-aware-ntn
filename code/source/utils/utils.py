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
