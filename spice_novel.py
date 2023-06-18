#!/bin/env python

#######################################################################
# Copyright (C) 2023 Christian Bluemel
#
# This file is part of Spice.
#
#  spice_novel is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  spice_novel is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Spice.  If not, see <http://www.gnu.org/licenses/>.
#
#######################################################################

from Classes.ReduxArgParse.ReduxArgParse import ReduxArgParse
from Classes.GTFBoy.AnnotationParser import AnnotationParser
from typing import Dict, Any, List


def main():
    argument_parser: ReduxArgParse = ReduxArgParse(["--input", "--out_path", "--expression", "--threshold", "--mode",
                                                    "--name", "--json"],
                                                   [str, str, str, float, str, str, str],
                                                   ["store", "store", "store", "store", "store", "store", "store"],
                                                   [1, 1, None, "?", 1, 1, "?"],
                                                   ["""Path to the input file. Depends on the mode. 
                                                    'merge': .txt-file containing the paths to all annotation-gtfs
                                                     that shall be merged. One path per line.
                                                    'transD': longest_orfs.pep-file containing predicted translated
                                                    ORFs of the transcripts.
                                                    'dmnd': path to diamond output.""",
                                                    """Path to the output directory for <name>.gtf,
                                                     <name>.json, <name>.fasta, <name>_idMap.json etc.""",
                                                    """Only used in 'merge'-mode. Path to a text file containing 
                                                    the paths to gtf files including transcript abundances. Only 
                                                    transcripts will be kept which exceed the float given in 
                                                    the --threshold parameter.""",
                                                    "Expression threshold, which will be used for transcript curation.",
                                                    """Either 1:'merge', 2:'transD' or 3:'diamond' depending on the
                                                    stage of the workflow.""",
                                                    "Name for the output file.",
                                                    """Path to the <name>_idMap.json file that was output during merge
                                                    mode. This argument is only required for
                                                    'transD' and 'dmnd' mode."""
                                                    ])
    argument_parser.generate_parser()
    argument_parser.execute()
    argument_dict: Dict[str, Any] = argument_parser.get_args()

    argument_dict["mode"] = argument_dict["mode"][0]
    argument_dict["out_path"] = argument_dict["out_path"][0]
    argument_dict["input"] = argument_dict["input"][0]
    argument_dict["name"] = argument_dict["name"][0]

    if argument_dict["mode"] == "merge":
        with open(argument_dict["input"], "r") as f:
            anno_list: List[str] = f.read().split("\n")

        if argument_dict["expression"] is None:
            expression_list: List[str] = list()
        else:
            with open(argument_dict["expression"], "r") as f:
                expression_list: List[str] = f.read().split("\n")

        annotation_parser: AnnotationParser = AnnotationParser(anno_list,
                                                               expression_list,
                                                               argument_dict["threshold"],
                                                               argument_dict["name"])
        annotation_parser.parse_annotations()
        annotation_parser.save(argument_dict["out_path"])
        annotation_parser.save_json(argument_dict["out_path"])

    elif argument_dict["mode"] == "transD":
        pass
    elif argument_dict["mode"] == "dmnd":
        pass


if __name__ == "__main__":
    main()