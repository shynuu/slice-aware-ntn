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

import codecs
from ruamel.yaml import YAML
from typing import List, Dict


class DockerImage(object):
    """Docker Image custom class"""

    def __init__(self, name: str, fulltag: str, requirement: object) -> None:
        self.name = name
        self.fulltag = fulltag
        self.requirement = [requirement] if type(
            requirement) == str else requirement

    def get_repository(self) -> str:
        return self.fulltag.split(":")[0]

    def get_tag(self) -> str:
        return self.fulltag.split(":")[1]


class ImageRepository(object):
    """Docker Image custom repository class"""

    def __init__(self, images: List[DockerImage], required: List[DockerImage]) -> None:
        self.images: Dict[str, DockerImage] = {}
        self.required: Dict[str, DockerImage] = {}
        for image in images:
            self.images[image.name] = image
        for image in required:
            self.required[image.name] = image

    def find_required(self, image: str) -> str:
        """Returns the required images to be built before `image`"""
        return self.images[image].requirement

    def is_present(self, image: str) -> bool:
        """Check if `image` is in the repository"""
        return image in self.images

    @classmethod
    def from_config(cls, path: str):
        """Returns a repository based on the image configuration file"""
        yaml = YAML()
        with codecs.open(path, "r") as f:
            images = yaml.load(f.read())
            repository = ImageRepository([DockerImage(
                im["name"], im["fulltag"], im["required"]) for im in images["images"]],
                [DockerImage(
                    im["name"], im["fulltag"], None) for im in images["required"]],
            )
            return repository
