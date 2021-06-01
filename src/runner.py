from typing import List, Dict
from cerberus import Validator
import logging
import docker
import subprocess
import os
import ipaddress
import schedule
import time
import re
import _thread
from .models import Slice

client = docker.from_env()


def start_testbed(name: str):
    cmd = f"docker-compose -f scenarios/{name}/docker-compose.yaml up -d"
    subprocess.call(cmd, shell=True)


def stop_testbed(name: str):
    cmd = f"docker-compose -f scenarios/{name}/docker-compose.yaml down -v"
    subprocess.call(cmd, shell=True)


def wait_for_configuration():
    started = False
    configured = False
    while not started:
        try:
            ue = client.containers.get("ue-0")
            started = True
        except:
            time.sleep(1)
    (c, r) = ue.exec_run("ip a")
    result = r.decode('utf-8').split("\n")
    l = len(result)
    while not configured:
        (c, r) = ue.exec_run("ip a")
        result = r.decode('utf-8').split("\n")
        if len(result) > l:
            configured = True
        time.sleep(1)


def gather_ip(name: str, n: int):
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


def generate_traffic(k: int, slice_id: int, ue_ips: List[List[str]]):
    ue = client.containers.get(f"ue-{k}")
    e = f"bash slice-{slice_id}-app.sh {ue_ips[k][slice_id]}"
    (c, r) = ue.exec_run(e)
    result = r.decode('utf-8')
    logging.info(f"UE {k} PDU generates traffic on slice {slice_id}")


def run_app(slice_id: int, ue_ips: List[List[str]]):
    logging.info(f"Generating traffic on slice {slice_id}")
    for k in range(len(ue_ips)):
        time.sleep(0.1)
        _thread.start_new_thread(generate_traffic, (k, slice_id, ue_ips,))
    return schedule.CancelJob
