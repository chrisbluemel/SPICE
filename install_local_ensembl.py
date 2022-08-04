#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 19 13:05:13 2022

@author: chrisbl
"""

import requests
import os
import sys
import shutil
import gzip
import urllib.request as request
from contextlib import closing
from library_class import Library

def ping_ensembl():
    import requests, sys
    
    
    server = "https://rest.ensembl.org"
    ext = "/info/ping?"
    
    for i in range(3):
        r = requests.get(server+ext, headers={ "Content-Type" : "application/json"})
 
        if r.ok:
            break
        elif i >= 2:
            print("Ensembl is currently down. Can't download sequences. Aborting...")
            r.raise_for_status()
            sys.exit() 
    decoded = r.json()
    return bool(decoded["ping"])

def make_local_ensembl_name(path, release_num, species, suffix, assembly_name, url_species):
        release_num = str(release_num)        
        ensembl_path = path + url_species + "." + assembly_name + "." + release_num + suffix
        return ensembl_path

def get_species_info(species):
    server = "https://rest.ensembl.org"
    ext = "/info/genomes/" + species + "?"
     
    r = requests.get(server+ext, headers={ "Content-Type" : "application/json"})
     
    if not r.ok:
      print("Could not find species!")
      r.raise_for_status()
      sys.exit()
     
    decoded = r.json()
    url_name = decoded["url_name"]
    name = decoded["name"]
    assembly_default = decoded["assembly_default"]
    return name, url_name, assembly_default


def get_release():
        print("Checking release number...")
        server = "https://rest.ensembl.org"
        ext = "/info/data/?"
 
        for x in range(3):
            r = requests.get(server+ext, headers={ "Content-Type" : "application/json"})

            if not r.ok and x < 2:
                continue
            elif x > 2:
                print("Could not current release number...")
                r.raise_for_status()
                sys.exit()
            else:
                release_num = max(r.json()["releases"])
        return str(release_num)

def make_rootpath(library_path, species, assembly_num):
    return library_path + species + "/release-" + str(assembly_num) + "/"

def get_taxon_id(species): 
    server = "https://rest.ensembl.org"
    ext = "/info/genomes/taxonomy/" + species +"?"
 
    r = requests.get(server+ext, headers={ "Content-Type" : "application/json"})
 
    if not r.ok:
        r.raise_for_status()
        sys.exit()
 
    decoded = r.json()
    return decoded[0]["species_taxonomy_id"]

def make_folders_and_files(root_path):
    if not os.path.exists(root_path):
        os.makedirs(root_path)
    
    tsv_buffer_path = root_path + "tsv_buffer/"
    if not os.path.exists(tsv_buffer_path):
        os.makedirs(tsv_buffer_path)
    
    slurm_path = root_path + "SLURM/"
    if not os.path.exists(slurm_path):
        os.makedirs(slurm_path)
    
    fas_buffer_path = root_path + "FAS_buffer/"
    if not os.path.exists(fas_buffer_path):
        os.makedirs(fas_buffer_path)
        
    annotation_path = root_path + "annotation/"
    if not os.path.exists(annotation_path):
        os.makedirs(annotation_path)
    
    isoforms_path = root_path + "isoforms.fasta"
    if not os.path.isfile(isoforms_path):
        with open(isoforms_path, "w") as fp:
            pass
    
    phyloprofile_ids_path = root_path + "phyloprofile_ids.tsv"
    if not os.path.isfile(phyloprofile_ids_path):
        with open(phyloprofile_ids_path, "w") as fp:
            pass
    
    gene_ids_path = root_path + "gene_ids.txt"
    if not os.path.isfile(gene_ids_path):
        with open(gene_ids_path, "w") as fp:
            pass

    return tsv_buffer_path, fas_buffer_path, annotation_path, isoforms_path, phyloprofile_ids_path, gene_ids_path, slurm_path

#def install_local_ensembl(url_infix_species, release_num, library_path, url_species, assembly_name):
def install_local_ensembl(species, output_dir):
        ping_ensembl()
        library_path = output_dir + "/FAS_library/"
        if not os.path.exists(library_path):
            os.makedirs(library_path)
        release_num = get_release()
        species, url_name, assembly_default = get_species_info(species)
        taxon_id = get_taxon_id(species)
        root_path = make_rootpath(library_path, species, release_num)
        
        tsv_buffer_path, fas_buffer_path, annotation_path, isoforms_path, phyloprofile_ids_path, gene_ids_path, slurm_path = make_folders_and_files(root_path)
        pairings_tsv_json_path = root_path + "pairings_tsv.json"
        protein_coding_ids_path = root_path + "pairings_tsv.json"

        ftp_prefix = "http://ftp.ensembl.org/pub/release-"
        ftp_suffix = ".gtf.gz"        
        ftp_infix = "/gtf/" + species + "/"
        
        print("The current release is", release_num + "...")
        
        ### Assemble FTP address according to standard /release-{release_num}/{species}.{assembly_dafault}.{assembly_num}.gtf.gz
        file_name = url_name + "." + assembly_default + "." + release_num + ftp_suffix 
        ftp_address = ftp_prefix + release_num + ftp_infix + file_name 
        local_assembly_path = root_path + file_name
        print("Downloading", ftp_address, "to", local_assembly_path + "...")
        with closing(request.urlopen(ftp_address)) as r:
            with open(local_assembly_path, 'wb') as f:
                shutil.copyfileobj(r, f)
        
        ### Unpacking file
        with gzip.open(local_assembly_path, 'rb') as f_in:
            with open(local_assembly_path[:-3], "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        os.remove(local_assembly_path)
        
        config_path = root_path + "config.tsv"
        
        fas_lib = Library(None, True)
        fas_lib.set_config("species", species)
        fas_lib.set_config("release_num", release_num)
        fas_lib.set_config("url_name", url_name)
        fas_lib.set_config("assembly_default", assembly_default)
        fas_lib.set_config("taxon_id", taxon_id)
        
        fas_lib.set_config("library_path", library_path)
        fas_lib.set_config("root_path", root_path)
        fas_lib.set_config("self_path", config_path)
        fas_lib.set_config("pairings_tsv_json_path", pairings_tsv_json_path)
        fas_lib.set_config("gene_ids_path", gene_ids_path)
        fas_lib.set_config("isoforms_path", isoforms_path)
        fas_lib.set_config("protein_coding_ids_path", protein_coding_ids_path)
        fas_lib.set_config("phyloprofile_ids_path", phyloprofile_ids_path)
        fas_lib.set_config("local_assembly_path", local_assembly_path)
        fas_lib.set_config("slurm_path", slurm_path)
        
        fas_lib.save_config()
        
        print("Library scaffold constructed. Now run main.py using the option -c", config_path)


def main():
    pass
    #install_local_ensembl("mouse", "/share/project/zarnack/chrisbl/FAS/utility/protein_lib/FAS_Pipe/")
    #print(make_local_ensembl_name("/share/project/zarnack/chrisbl/FAS/utility/protein_lib/FAS_library/", 107, "homo_sapiens", ".gtf"))
if __name__ == "__main__":
    main()
        
                
                        
                    