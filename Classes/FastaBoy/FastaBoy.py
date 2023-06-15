#!/bin/env python
import json
#######################################################################
# Copyright (C) 2023 Christian Bluemel
#
# This file is part of Spice.
#
#  FastaBoy is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  FastaBoy is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Spice.  If not, see <http://www.gnu.org/licenses/>.
#
#######################################################################

from typing import Dict, List, Tuple, Iterator
import argparse


class FastaBoy:

    def __init__(self, fasta_path: str):
        self.fasta_path = fasta_path
        self.fasta_dict: Dict[str, Dict[str, str]] = dict()
        self.filter_list: List[Tuple[str, str]] = list()

    def get_fasta_dict(self) -> Dict[str, Dict[str, str]]:
        return self.fasta_dict

    def set_filter(self, key: str, value: str):
        self.filter_list.append((key, value))

    def parse_fasta(self):
        gene_id: str = ""
        protein_id: str = ""
        found_flag: bool = False
        for line in self:
            if line.startswith(">"):
                found_flag = False
                fasta_header_dict: Dict[str, str] = FastaBoy.make_fasta_header_dict(line)
                if self.__apply_filter(fasta_header_dict):
                    found_flag = True
                    gene_id: str = fasta_header_dict["gene_id"]
                    protein_id: str = fasta_header_dict["protein_id"]
                    if gene_id not in self.fasta_dict.keys():
                        self.fasta_dict[gene_id] = dict()
                    self.fasta_dict[gene_id][protein_id] = ""
            elif found_flag:
                self.fasta_dict[gene_id][protein_id] += line.strip()

    def __apply_filter(self, fasta_header_dict: Dict[str, str]) -> bool:
        for key, value in self.filter_list:
            if fasta_header_dict[key] != value:
                return False
        return True

    @staticmethod
    def make_fasta_header_dict(fasta_header: str) -> Dict[str, str]:
        entry_list: List[str] = [entry for entry in fasta_header.split(" ") if FastaBoy.discriminate_header(entry)]
        fasta_header_dict: Dict[str, str] = dict()
        for entry in entry_list:
            if entry.startswith(">"):
                fasta_header_dict["protein_id"] = entry[1:].split(".")[0]
            elif entry.startswith("gene:"):
                fasta_header_dict["gene_id"] = entry.split(":")[1].split(".")[0]
            elif entry.startswith("transcript:"):
                fasta_header_dict["transcript_id"] = entry.split(":")[1].split(".")[0]
            elif entry.startswith("gene_biotype:"):
                fasta_header_dict["gene_biotype"] = entry.split(":")[1]
            elif entry.startswith("transcript_biotype:"):
                fasta_header_dict["transcript_biotype"] = entry.split(":")[1]
        return fasta_header_dict

    @staticmethod
    def discriminate_header(entry: str):
        if entry.startswith(">"):
            return True
        elif entry.startswith("gene_biotype"):
            return True
        elif entry.startswith("transcript_biotype"):
            return True
        elif entry.startswith("gene"):
            return True
        elif entry.startswith("transcript"):
            return True
        else:
            return False

    def __iter__(self) -> Iterator[str]:
        with open(self.fasta_path, "r") as f:
            for line in f:
                yield line


def main():
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument("-i",
                        "--input",
                        type=str,
                        action="store",
                        help="Path to a fasta file.")
    parser.add_argument("-o",
                        "--output",
                        type=str,
                        action="store",
                        help="Path to json output file.")

    argument_dict: Dict[str, str] = vars(parser.parse_args())

    fasta_iterator: FastaBoy = FastaBoy(argument_dict["input"])
    fasta_iterator.set_filter("transcript_biotype", "protein_coding")
    fasta_iterator.set_filter("gene_biotype", "protein_coding")

    fasta_iterator.parse_fasta()

    with open(argument_dict["output"], "w") as f:
        json.dump(fasta_iterator.get_fasta_dict(), f, indent=4)


if __name__ == "__main__":
    main()