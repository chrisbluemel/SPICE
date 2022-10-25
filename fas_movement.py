#!/usr/bin/env python3
# -*- coding: utf-8 -*-


#######################################################################
# Copyright (C) 2022 Christian, Blümel, Julian Dosch
#
# This file is part of grand-trumpet.
#
#  grand-trumpet is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  grand-trumpet is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with grand-trumpet.  If not, see <http://www.gnu.org/licenses/>.
#
#######################################################################
"""
Created on Thu Aug 18 11:30:47 2022

@author: chrisbl
"""

import argparse

import valves.library_class as library_class
import valves.expression_extraction as ee


def parser_setup():
    """
    

    Returns
    -------
    Get paths and flags required to run.

    """  
    
    #Setting up parser:
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--config", type=str,
                        help="Path to a config file of a library. Is required for library creation.")
                        
    parser.add_argument("-n", "--namepath", type=str,
                        help="""Path to a textfile that contains the names of the conditions already present in the results/expression directory
                        of the library. Movement files will be calculated for these conditions.""")
    
    parser.add_argument("-t", "--tmhmm", action="store_true",
                        help="""Only do the FAS runs using TMHMM and SignalP domains.""")

    parser.add_argument("-l", "--lcr", action="store_true",
                        help="""Only do the FAS runs using flPS and SEG domains.""")

                        
    args = parser.parse_args()
    config_path = args.config
    name_path = args.namepath
    flag_lcr = args.lcr
    flag_tmhmm = args.tmhmm

    return config_path, name_path, flag_lcr, flag_tmhmm

def main():
    """
    Returns
    -------
    """
    config_path, name_path, flag_lcr, flag_tmhmm = parser_setup()

    fas_lib = library_class.Library(config_path, False)
    print("Movement calculation commencing...")
    ee.generate_movement_file(fas_lib, name_path, flag_lcr, flag_tmhmm)
    
if __name__ == "__main__":
    main()
   