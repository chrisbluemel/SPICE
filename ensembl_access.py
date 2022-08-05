# -*- coding: utf-8 -*-
"""
__author__ = "Christian Bluemel"

"""

import requests
import sys

from all_protein_coding_gene_ID import extract_protein_coding_ids

from install_local_ensembl import install_local_ensembl

from FAS_handler import tsv_collection_maker

from library_class import Library

#Test command line:
# python main.py -s human -o /share/project/zarnack/chrisbl/FAS/utility/protein_lib/ -l

# /share/project/zarnack/chrisbl/FAS/utility/protein_lib


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def make_request_data(id_list):
    id_list = [protein_id for gene_id, protein_id, transcript_id in id_list]
    request_data = '{ "ids" : ['
    for entry in id_list:
        request_data += '"' + entry + '", '
    request_data = request_data[:-2]
    request_data += ' ] }'
    return request_data

def extract_gene_ids(protein_coding_ids):
    gene_ids = sorted(list(set([gene_id for gene_id, protein_id, transcript_id in protein_coding_ids])))
    count = len(gene_ids)
    return count, gene_ids

def save_gene_ids_txt(gene_ids, gene_ids_path):
    gene_id_str = "\n".join(["gene"] + gene_ids)
    with open(gene_ids_path, "w") as f:
        f.write(gene_id_str)

def load_gene_ids_txt(gene_ids_path):
    with open(gene_ids_path, "r") as f:
        gene_ids = f.read()
        gene_ids = gene_ids.split("\n")
        gene_ids = [gene_id for gene_id in gene_ids if len(gene_id) > 0]
    return gene_ids


def load_progress(path):
    tuple_list = tsv_to_tuple_list(path)
    header_list = [ header for header, taxon_id in tuple_list ]
    gene_protein_id_tuple_list = [ tuple(header.split("|")[0:2]) for header in header_list ]
    return gene_protein_id_tuple_list

def assemble_protein_seqs(protein_coding_ids, fas_lib):
    """

    Parameters
    ----------
    list with gene and protein IDs as tuples
        [
            (gene_id_1, protein_id_1, transcript_id_1),
            (gene_id_1, protein_id_2, transcript_id_2),
            (gene_id_2, protein_id_3, transcript_id_3),
            .
            .
            .
            ...etc...
            
            ]
    The Library config class.

    Returns
    -------
    counts on how many request were found, not found and how many genes were assembled.
    """
    
    if fas_lib.get_config("flag_gene_ids_collection") == "False":
        print("Gene IDs not assembled on their own yet.")
        gene_count, gene_ids = extract_gene_ids(protein_coding_ids)
        save_gene_ids_txt(gene_ids, fas_lib.get_config("gene_ids_path"))
        fas_lib.set_config("gene_count", gene_count)
        fas_lib.set_config("flag_gene_ids_collection", "True")
        fas_lib.save_config()
    else:
        gene_count = fas_lib.get_config("gene_count")
        gene_ids = load_gene_ids_txt(fas_lib.get_config("gene_ids_path"))
    
    print("Checking progress of the library.")
    if fas_lib.get_config("flag_sequence_collection") == "False":
        request_chunks = list(chunks(protein_coding_ids, 50))
        
        ensembl_requests = []
        for chunk in request_chunks:
            ensembl_requests.append(make_request_data(chunk))

        server = "https://rest.ensembl.org/sequence/id"
        headers={ "Content-Type" : "application/json", "Accept" : "application/json"}    
                
        for i, request in enumerate(ensembl_requests):
            ids_list = request_chunks[i]
            for x in range(3):
                r = requests.post(server, headers=headers, data=request)
                if r.ok:
                    break
                elif x > 1:
                    r.raise_for_status()
                    sys.exit()
            decoded = r.json()
            id_seq_tuple_list = [(entry["query"], entry["seq"]) for entry in decoded]
            for j, id_seq_tuple in enumerate(id_seq_tuple_list):
                gene_id, protein_id, transcript_id = ids_list[j]
                query_id, seq = id_seq_tuple
                if query_id != protein_id:
                    print("Incorrect pairing. Aborting!", query_id, protein_id)
                header = gene_id + "|" + protein_id + "|" + fas_lib.get_config("taxon_id")
                with open(fas_lib.get_config("phyloprofile_ids_path"), "a") as file:
                    file.write(header + "\t" + fas_lib.get_config("taxon_id") + "\n")
                with open(fas_lib.get_config("isoforms_path"), "a") as fasta:
                    fasta.write(">" + header + "\n" + seq + "\n")
                fas_lib.increment_acquired_seq_count()
                fas_lib.save_config()
                
        #Sequence collection should be done.
        fas_lib.set_config("flag_sequence_collection", "True")
        fas_lib.save_config()
    return fas_lib

def check_isoforms(isoforms_path):
    with open(isoforms_path, "r") as f:
        fasta = f.read()
    fasta_lines = fasta.split("\n")
    fasta_lines = fasta_lines[:-1]
    header = fasta_lines[::2]
    gene_ids = [ entry.split("|")[0][1:] for entry in header ]
    protein_ids = [ entry.split("|")[1] for entry in header ]
    
    server = "https://rest.ensembl.org"
    ext = "/lookup/id"
    ext2 = "/lookup/id/"

    headers={ "Content-Type" : "application/json", "Accept" : "application/json"}
    prefix_request = '{ "ids" : ["' 
    infix_request = '", "'
    suffix_request ='" ] }'
    for i, protein_id in enumerate(protein_ids): 
        
        gene_id = gene_ids[i]
        request = prefix_request + protein_id + infix_request + gene_id + suffix_request
        r = requests.post(server+ext, headers=headers, data=request)
        if not r.ok:
            r.raise_for_status()
            sys.exit()
        decoded = r.json()
        gene_r= decoded[gene_id]
        flag_biotype = gene_r["biotype"].startswith("protein_coding")
        
        protein_r = decoded[protein_id]

        transcript_id = protein_r["Parent"]
        r = requests.get(server+ext2+transcript_id+"?", headers={ "Content-Type" : "application/json"})
        
        transcript_r = r.json()
        flag_same_id = transcript_r["Parent"] == gene_id
        flag_biotype2 = transcript_r["biotype"].startswith("protein_coding")
        if not all([flag_same_id, flag_biotype2, flag_biotype]):
            print("Problem found!")
            print(gene_id, transcript_id, protein_id)

def triple_list_to_tsv(triple_list):
    tsv = ""
    for str_x, str_y, str_z in triple_list:
        tsv += str_x + "\t" + str_y + "\t" + str_z + "\n"
    return tsv

def tuple_list_to_tsv(tuple_list):
    tsv = ""
    for str_x, str_y in tuple_list:
        tsv += str_x + "\t" + str_y + "\n"
    return tsv

def tsv_to_tuple_list(path):
    tuple_list = []
    with open(path, "r") as f:
        tsv = f.read()
        tsv = tsv.split("\n")
        tsv = [ entry for entry in tsv if len(entry) > 0 ]
    tuple_list = [ tuple(entry.split("\t")) for entry in tsv ]
    return tuple_list

def make_header_dict(fas_lib):
    header_taxon_tuple_list = tsv_to_tuple_list(fas_lib.get_config("phyloprofile_ids_path"))
    header_list = [ header for header, taxon in header_taxon_tuple_list ]
    
    gene_ids = load_gene_ids_txt(fas_lib.get_config("gene_ids_path"))
    
    header_dict = dict()
    
    for gene_id in gene_ids:
        header_dict[gene_id] = []
    
    for header in header_list:
        gene_id = header.split("|")[0]
        header_dict[gene_id].append(header)
    return header_dict

def ensembl_access(output_dir, species, flag_install_local, config_path):
    """
    Returns
    -------
    fasta called isoform.fasta that contains the the gene_id, protein_id, taxon_id as a header and the
    consensus sequence like this:
        >gene_id1|protein_id1|taxon_id
        consensus_sequence1
        >gene_id1|protein_id2|taxon_id
        consensus_sequence2
        >gene_id2|protein_id3|taxon_id
        consensus_sequence3
        .
        .
        .
        ...etc...
    """

  
    if flag_install_local:
        print("Local ensembl installation commencing...")
        #install_local_ensembl(species, release_num, library_path, url_name, assembly_default)
        install_local_ensembl(species, output_dir)
    else:
        fas_lib = Library(config_path, False)
        print("Library generation commencing.")
        print("Checking config for protein coding ID status.")
        # Collect the protein coding IDs
        if fas_lib.get_config("flag_protein_coding_genes") == "True":
            print("Protein coding genes already collected. Loading list.")
            protein_coding_ids = tsv_to_tuple_list(fas_lib.get_config("protein_coding_ids_path"))
        else:
            print("Protein coding genes not collected yet. Assembling list.")
            protein_coding_ids = extract_protein_coding_ids(fas_lib.get_config("local_assembly_path"))
            fas_lib.set_config("total_seq_count", len(protein_coding_ids))
            with open(fas_lib.get_config("protein_coding_ids_path"), "w") as f:
                f.write(triple_list_to_tsv(protein_coding_ids))
            fas_lib.set_config("flag_protein_coding_genes", "True")
            fas_lib.save_config()
        
        # Remove the IDs that have already been loaded.
        progress_list = load_progress(fas_lib.get_config("phyloprofile_ids_path"))
        protein_coding_ids = [(gene_id,
                               protein_id,
                               transcript_id) for  gene_id,
                                                  protein_id,
                                                  transcript_id in protein_coding_ids if (gene_id, protein_id) not in progress_list]
        
        fas_lib = assemble_protein_seqs(protein_coding_ids, fas_lib)
        
        if fas_lib.get_config("flag_made_pairings") == "False":
            header_dict = make_header_dict(fas_lib)
            tsv_collection_maker(header_dict, fas_lib)
            fas_lib.set_config("flag_made_pairings", True)
            fas_lib.save_config()
        print(fas_lib.get_config("gene_count"), "genes assembled.")
        print("Saved isoforms as fasta in", fas_lib.get_config("isoforms_path"))
        print("Library assembly complete.")
    
def main():
    species = "human"
    # release_num = 107
    # species, url_name, assembly_default = ('homo_sapiens', 'Homo_sapiens', 'GRCh38')
    # library_path = "/share/project/zarnack/chrisbl/FAS/utility/protein_lib/FAS_library/"
    # ensembl_path = make_local_ensembl_name(library_path, release_num, species, ".gtf", assembly_default, url_name)
    
if __name__ == "__main__":
    main()

