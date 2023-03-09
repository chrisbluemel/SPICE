#!/bin/env python
from typing import Any

#######################################################################
# Copyright (C) 2023 Christian Bluemel
#
# This file is part of main.
#
#  LibraryInfo is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  LibraryInfo is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with PathwayTrace.  If not, see <http://www.gnu.org/licenses/>.
#
#######################################################################

import yaml


class LibraryInfo:

    def __init__(self, info_path: str) -> None:
        self.path: str = info_path
        with open(info_path, "r") as f:
            self.info_dict = yaml.safe_load(f)
        if self.info_dict is None:
            self.info_dict = dict()

    def __getitem__(self, key: str) -> Any:
        return self.info_dict[key]

    def __setitem__(self, key: str, item: Any) -> None:
        self.info_dict[key] = item

    def save(self):
        with open(self.path, "w") as f:
            yaml.dump(self.info_dict ,f)