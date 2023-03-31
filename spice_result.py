#!/bin/env python

#######################################################################
# Copyright (C) 2023 Christian Bluemel
#
# This file is part of main.
#
#  spice_result is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  spice_result is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with PathwayTrace.  If not, see <http://www.gnu.org/licenses/>.
#
#######################################################################

from typing import Dict, Any, List

from Classes.ReduxArgParse.ReduxArgParse import ReduxArgParse
from Classes.ResultBuddy.ResultBuddy import ResultBuddy


def setup(library_path: str, outdir: str):
    ResultBuddy(library_path, outdir, )


def expression(library_path: str, outdir: str, gtf_path: str, expression_name: str):
    pass


def condition(result_dir: str, replicate_name_list: List[str], condition_name: str):
    pass


def compare():
    pass


def main():
    ####################################################################
    # SETUP ARGS PARSER

    argument_parser: ReduxArgParse = ReduxArgParse(["--mode", "--library", "--outdir",
                                                    "--gtf", "--name", "--replicates", "--compared"],
                                                   [str, str, str,
                                                    str, str, str, str],
                                                   ["store", "store", "store",
                                                    "store", "store", "store", "store"],
                                                   [1, 1, 1,
                                                    "?", "?", "*", "*"],
                                                   ["""Mode: Either 'setup', 'expression', 'condition' or 'compare'.
                                                   'setup' creates the result directory system.
                                                   'expression' loads a gtf expression file into results as replicate.
                                                   'condition' combines replicates and calculates the new conditions
                                                   movement.
                                                   'compare' generates a comparison between two conditions movements.
                                                   """,
                                                    "Path to the library. Required for all modes.",
                                                    "Parent directory of the result output. Required for all modes.",
                                                    """Path to gtf expression file to be imported.
                                                    Required for 'expression'""",
                                                    """Name of replicate or condition that will be generated. 
                                                    Required for 'expression' and 'condition' modes.""",
                                                    """Names of replicates to be joined into condition.
                                                    Required for 'condition' mode. Can be just one.""",
                                                    """Names of conditions that shall be compared.
                                                     Required for 'compare' mode."""
                                                    ])
    argument_parser.generate_parser()
    argument_parser.execute()
    argument_dict: Dict[str, Any] = argument_parser.get_args()

    ####################################################################
    # CHECK THE COMMANDLINE ARGUMENTS FOR THE INTEGRITY.
    if argument_dict["mode"][0] == "setup":

        if any(argument_dict[key] is None for key in ["library", "outdir"]):
            print("'setup' mode failed. Either 'library' or 'outdir' missing from commandline arguments.\nAborting.")
        elif any(isinstance(argument_dict[key], list) for key in ["library", "outdir"]):
            print("""'setup' mode failed.
            Multiple arguments given for either 'library' or 'outdir' commandline arguments.\nAborting.""")
        else:
            setup(argument_dict["library"][0], argument_dict["outdir"][0])

    elif argument_dict["mode"] == "expression":

        if any(argument_dict[key] is None for key in ["result_dir", "gtf", "name"]):
            print("""'expression' mode failed. 
            Either 'result_dir', 'gtf' or 'name' missing from commandline arguments.\nAborting.""")
        elif any(isinstance(argument_dict[key], list) for key in ["result_dir", "gtf", "name"]):
            print("""'expression' mode failed.
            Multiple arguments given for either 'result_dir', 'gtf' or 'name' commandline arguments.\nAborting.""")
        else:
            expression(argument_dict["library"][0],
                       argument_dict["outdir"][0],
                       argument_dict["gtf"],
                       argument_dict["name"])

    elif argument_dict["mode"] == "condition":

        if any(argument_dict[key] is None for key in ["result_dir", "name", "replicates"]):
            print("""'condition' mode failed. 
            Either 'result_dir', 'replicates' or 'name' missing from commandline arguments.\nAborting.""")
        elif any(isinstance(argument_dict[key], list) for key in ["result_dir", "name"]):
            print("""'condition' mode failed.
            Multiple arguments given for either 'result_dir' or 'name' commandline arguments.\nAborting.""")
        else:
            condition(argument_dict["result_dir"], argument_dict["replicates"], argument_dict["name"])

    elif argument_dict["mode"] == "compare":
        print("'compare' mode not yet implemented in this version of spice.")
    else:
        print("Mode not recognized:\n", argument_dict["mode"], "\nAborting.")


if __name__ == "__main__":
    main()