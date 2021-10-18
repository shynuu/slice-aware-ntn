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
