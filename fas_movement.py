#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 18 11:30:47 2022

@author: chrisbl
"""

import argparse

import library_class
import expression_extraction as ee


def parser_setup():
    """
    

    Returns
    -------
    Get species, output direcotry and installation settings for run.

    """  
    
    #Setting up parser:
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--config", type=str,
                        help="Path to a config file of a library. Is required for library creation.")
                        
    parser.add_argument("-n", "--namepath", type=str,
                        help="""Path to a textfile that contains the names of the expression filepath given in the argument --expressionpath.
                        One name per row.""")

    parser.add_argument("-e", "--expressionpath", type=str,
                        help="""Path to a textfile that contains the path to the expression gtf files for which the movement shall be calculated. 
                        One sample per row, though several paths can be written into one row seperated by a semicolon. Paths in the same row will be
                        concatenated and considered as several replicates of one sample.""")
    
    parser.add_argument("-t", "--tmhmm", action="store_true",
                        help="""Only do the FAS runs using TMHMM and SignalP domains.""")

    parser.add_argument("-l", "--lcr", action="store_true",
                        help="""Only do the FAS runs using flPS and SEG domains.""")

                        
    args = parser.parse_args()
    config_path = args.config
    name_path = args.namepath
    expression_path = args.expressionpath
    flag_lcr = args.lcr
    flag_tmhmm = args.tmhmm

    return config_path, name_path, expression_path, flag_lcr, flag_tmhmm

def main():
    """
    Returns
    -------
    """
    config_path, name_path, expression_path, flag_lcr, flag_tmhmm = parser_setup()

    fas_lib = library_class.Library(config_path, False)
    print("Movement calculation commencing...")
    ee.generate_FAS_polygon(fas_lib, expression_path, name_path, flag_lcr, flag_tmhmm)
    
if __name__ == "__main__":
    main()
   