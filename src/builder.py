import docker
import os
import logging
import sys
from typing import List

IMAGES = [
    "amf",
    "smf",
    "ausf",
    "nrf",
    "pcf",
    "smf",
    "udm",
    "udr",
    "upf",
    "qof",
    "ntnqof",
    "nssf",
    "gnb",
    "ue",
    "trunks",
    "populate",
    "classifier",
]

client = docker.from_env()


def get_required(name: str):
    if name in ["amf", "smf", "ausf", "nrf", "pcf", "smf", "udm", "udr", "upf", "qof", "ntnqof", "nssf"]:
        return ["base"]
    elif name in ["gnb", "ue"]:
        return ["cmake", "ueransim"]
    else:
        return None


def push_all():
    for image in IMAGES:
        try:
            logging.info(f"Pushing {image} docker image...")
            client.images.push("shynuu/sa-ntn", tag=image)
        except Exception as e:
            logging.error(
                f"Impossible to push sa-ntn/{image} docker image")
            logging.error(e)
            sys.exit(1)

def pull_all():
    pull()
    for image in IMAGES:
        try:
            logging.info(f"Pulling {image} docker image...")
            client.images.pull("shynuu/sa-ntn", tag=image)
        except Exception as e:
            logging.error(
                f"Impossible to pull sa-ntn/{image} docker image")
            logging.error(e)
            sys.exit(1)


def pull():
    images: List[str] = ["mongo"]
    for image in images:
        logging.info(
            f"Pulling {image} docker image...")
        img = client.images.pull(image)
        return img


def build_main(main: str, folder: str, nocache: bool):
    logging.info(
        f"Building shynuu/sa-ntn:{folder} docker image")
    pth = f"{main}/{folder}/."
    try:
        client.images.build(path=pth, rm=True, forcerm=True,
                            tag=f"shynuu/sa-ntn:{folder}", quiet=False, nocache=nocache)
    except Exception as e:
        logging.error(
            f"Impossible to build sa-ntn/{folder} docker image")
        logging.error(e)
        sys.exit(1)


def build_pre(pre: str, folder: str, nocache: bool):
    logging.info(f"Building required shynuu/sa-ntn:{folder} docker image")
    pth = f"{pre}/{folder}/."
    try:
        client.images.build(path=pth, rm=True, forcerm=True,
                            tag=f"shynuu/sa-ntn:{folder}", quiet=False, nocache=nocache)
    except Exception as e:
        logging.error(
            f"Impossible to build required sa-ntn/{folder} docker image")
        logging.error(e)
        sys.exit(1)


def build(path: str, target: str, pre_cache: bool, main_cache: bool,):

    pre = f"{path}/pre"
    main = f"{path}/main"

    if target in ["amf", "smf", "ausf", "gnb", "nrf", "pcf", "smf", "trunks", "udm", "udr", "ue", "upf", "classifier", "qof", "ntnqof", "populate", "nssf", "application"]:
        required = get_required(target)
        if required:
            for element in required:
                build_pre(pre, element, pre_cache)
        build_main(main, target, main_cache)
    else:

        logging.info("Building all docker images, this may take some time...")

        pull()
        pre_folders = [d for d in os.listdir(
            pre) if os.path.isdir(os.path.join(pre, d))]
        pre_folders.sort()

        main_folders = [d for d in os.listdir(
            main) if os.path.isdir(os.path.join(main, d))]
        main_folders.sort()
        for folder in pre_folders:
            build_pre(pre, folder, pre_cache)
        for folder in main_folders:
            build_main(main, folder, main_cache)

    post_build()


def post_build():
    pass
