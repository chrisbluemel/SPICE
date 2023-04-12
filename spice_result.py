#!/bin/env python

#######################################################################
# Copyright (C) 2023 Christian Bluemel
#
# This file is part of Spice.
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
#  along with Spice.  If not, see <http://www.gnu.org/licenses/>.
#
#######################################################################

from typing import Dict, Any, List

from Classes.ReduxArgParse.ReduxArgParse import ReduxArgParse
from Classes.ResultBuddy.ResultBuddy import ResultBuddy


def setup(library_path: str, outdir: str):
    ResultBuddy(library_path, outdir, True)


def expression(library_path: str,
               outdir: str,
               gtf_path: str,
               expression_name: str,
               normalization: str,
               normalization_threshold: float = 1.0):
    result: ResultBuddy = ResultBuddy(library_path, outdir)
    result.import_expression_gtf(gtf_path, expression_name, normalization, normalization_threshold)
    result.generate_ewfd_file(expression_name)


def condition(library_path: str, outdir: str, replicate_name_list: List[str], condition_name: str):
    result: ResultBuddy = ResultBuddy(library_path, outdir)
    result.build_condition(condition_name, replicate_name_list)
    result.generate_ewfd_file(condition_name, True)


def compare():
    pass


def main():
    ####################################################################
    # SETUP ARGS PARSER

    argument_parser: ReduxArgParse = ReduxArgParse(["--mode", "--library", "--outdir", "--gtf",
                                                    "--name", "--replicates", "--compared", "--Normalization",
                                                    "--threshold"],
                                                   [str, str, str, str,
                                                    str, str, str, str,
                                                    float],
                                                   ["store", "store", "store", "store",
                                                    "store", "store", "store", "store",
                                                    "store"],
                                                   [1, 1, 1, "?",
                                                    "?", "*", "*", "?",
                                                    "?"],
                                                   ["""Mode: Either 'setup', 'expression', 'condition' or 'compare'.
                                                   'setup' creates the result directory system.
                                                   'expression' loads a gtf expression file into results as replicate.
                                                   'condition' combines replicates and calculates the new conditions
                                                   EWFD.
                                                   'compare' generates a comparison between two conditions EWFDs.
                                                   """,
                                                    "Path to the library. Required for all modes.",
                                                    "Parent directory of the result output. Required for all modes.",
                                                    """Path to gtf expression file to be imported.
                                                    Required for 'expression'""",
                                                    """Name of replicate or condition that will be generated. 
                                                    Required for 'expression' and 'condition' modes.""",
                                                    """Names of replicates to be joined into condition.
                                                    Required for 'condition' mode. Must be more than one.""",
                                                    """Names of conditions that shall be compared.
                                                     Required for 'compare' mode.""",
                                                    """Normalization method referencing expression entry in gtf file.
                                                    Usually TPM or FPKM. Required for 'expression' mode.""",
                                                    """Any expression entry below this threshold will be set to 0.0.
                                                    Optional for 'expression' mode. 1.0 by default."""
                                                    ])
    argument_parser.generate_parser()
    argument_parser.execute()
    argument_dict: Dict[str, Any] = argument_parser.get_args()

    ####################################################################
    # CHECK THE COMMANDLINE ARGUMENTS FOR THE INTEGRITY.
    if argument_dict["mode"][0] == "setup":

        if any(argument_dict[key] is None for key in ["library", "outdir"]):
            print("'setup' mode failed. Either 'library' or 'outdir' missing from commandline arguments.\nAborting.")
        else:
            setup(argument_dict["library"][0], argument_dict["outdir"][0])

    elif argument_dict["mode"][0] == "expression":

        if any(argument_dict[key] is None for key in ["outdir", "gtf", "name", "Normalization", "library"]):
            print("""'expression' mode failed. 
            Either 'library', 'outdir', 'gtf', 'Normalization' or 'name' missing from commandline arguments.
            Aborting.""")
        else:
            if argument_dict["threshold"] is None:
                argument_dict["threshold"] = 1.0
            expression(argument_dict["library"][0],
                       argument_dict["outdir"][0],
                       argument_dict["gtf"],
                       argument_dict["name"],
                       argument_dict["Normalization"],
                       argument_dict["threshold"])

    elif argument_dict["mode"][0] == "condition":

        if any(argument_dict[key] is None for key in ["library", "outdir", "name", "replicates"]):
            print("""'condition' mode failed. 
            Either 'library', 'outdir', 'replicates' or 'name' missing from commandline arguments.\nAborting.""")
        elif len(argument_dict["replicates"]) < 2:
            print("""'condition' mode failed. 
            A condition requires more than one replicate.
            All replicates automatically get their EWFD calculated.\nAborting.""")
        else:
            condition(argument_dict["library"][0],
                      argument_dict["outdir"][0],
                      argument_dict["replicates"],
                      argument_dict["name"])

    elif argument_dict["mode"][0] == "compare":
        print("'compare' mode not yet implemented in this version of spice.")
    else:
        print("Mode not recognized:\n", argument_dict["mode"][0], "\nAborting.")


if __name__ == "__main__":
    main()