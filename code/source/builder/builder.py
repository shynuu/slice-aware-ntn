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

import docker
import logging
import sys
from . import ImageRepository


class Builder(object):
    """Builder class builds docker images"""

    def __init__(self, path: str) -> None:
        self.repository = ImageRepository.from_config(f"{path}/images.yaml")
        self.main = f"{path}/main"
        self.required = f"{path}/required"
        self.client = docker.from_env()

    def get_required(self, name: str):
        return self.repository.find_required(name)

    def push_all(self):
        """Push all images to docker hub"""

        for image, value in self.repository.images.items():
            try:
                logging.info(f"Pushing {image} docker image...")
                self.client.images.push(
                    value.get_repository(), tag=value.get_tag())
            except Exception as e:
                logging.error(
                    f"Impossible to push {value.fulltag} docker image")
                logging.error(e)
                sys.exit(1)

    def pull_all(self):
        """Pull all images from docker hub"""

        for image, value in self.repository.images.items():
            try:
                logging.info(f"Pulling {image} docker image...")
                self.client.images.pull(
                    value.get_repository(), tag=value.get_tag())
            except Exception as e:
                logging.error(
                    f"Impossible to pull {value.fulltag} docker image")
                logging.error(e)
            sys.exit(1)

    def build_main(self, name: str, nocache: bool):
        """Build main docker images"""

        image = self.repository.images[name]
        logging.info(
            f"Building {image.fulltag} docker image")
        pth = f"{self.main}/{image.name}/."
        try:
            self.client.images.build(path=pth, rm=True, forcerm=True,
                                     tag=image.fulltag, quiet=False, nocache=nocache)
        except Exception as e:
            logging.error(
                f"Impossible to build {image.fulltag} docker image")
            logging.error(e)
            sys.exit(1)

    def build_required(self, name: str, nocache: bool):
        """Build required docker images"""

        image = self.repository.required[name]
        logging.info(f"Building required {image.fulltag} docker image")
        pth = f"{self.required}/{image.name}/."
        try:
            self.client.images.build(path=pth, rm=True, forcerm=True,
                                     tag=image.fulltag, quiet=False, nocache=nocache)
        except Exception as e:
            logging.error(
                f"Impossible to build required {image.fulltag} docker image")
            logging.error(e)
            sys.exit(1)

    def build(self, target: str, pre_cache: bool, main_cache: bool):
        """Build all docker images"""

        if target != "all":
            required = self.get_required(target)
            if required:
                for element in required:
                    self.build_required(element, pre_cache)
            self.build_main(target, main_cache)
        else:
            logging.info(
                "Building all docker images, this may take some time...")

            required = set([])
            images = set([])
            for image, value in self.repository.images.items():
                images.add(value.name)
                if value.requirement:
                    for r in value.requirement:
                        required.add(r)

            for r in sorted(required):
                self.build_required(r, pre_cache)

            for i in sorted(images):
                self.build_main(i, main_cache)
