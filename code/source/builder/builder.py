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
