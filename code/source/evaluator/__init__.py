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

from ..testbed.testbed import Testbed


class Evaluator(object):
    """Generic Evaluator Class"""

    def __init__(self, t1: Testbed, t2: Testbed) -> None:
        self.t1 = t1
        self.t2 = t2
        self.output_path = None

    def evaluate(self, contribution: bool, plot: bool) -> None:
        """generic evaluate function"""
        pass
