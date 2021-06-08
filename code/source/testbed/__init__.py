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

from typing import Dict
from ..scenario import Scenario
from ..scenario.non_slice_aware_ntn import NonSliceAwareNTN
from ..scenario.slice_aware_ntn import SliceAwareNTN


class Selector(object):
    """Scenario selector class"""

    scenarios = [SliceAwareNTN, NonSliceAwareNTN]

    @classmethod
    def get_scenario(cls, definition: Dict, name: str) -> Scenario:
        for s in cls.scenarios:
            if definition['type'] == s.scenario_type:
                return s.sanitize(definition, name, s)
