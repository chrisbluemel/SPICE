#!/bin/env python

#######################################################################
# Copyright (C) 2023 Christian Bluemel
#
# This file is part of main.
#
#  RemoteEnsembl is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  RemoteEnsembl is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with PathwayTrace.  If not, see <http://www.gnu.org/licenses/>.
#
#######################################################################


from typing import Type
from typing import List

from Classes.API.ensembl_mod.LocalEnsembl import LocalEnsembl


class RemoteEnsembl(LocalEnsembl):

    def __init__(self, raw_species: str, goal_directory: str, release_num: str) -> None:
        super().__init__(raw_species, goal_directory, release_num)


def main():
    remote_ensembl = RemoteEnsembl("human", "C:/Users/chris/Desktop/git/root/", "107")
    print(remote_ensembl.ping)
    remote_ensembl.download()


if __name__ == "__main__":
    main()