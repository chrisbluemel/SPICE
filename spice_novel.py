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
from Classes.FastaBoy.FastaBoy import TransDecoderFastaBoy, SpiceFastaBoy
from Classes.SequenceHandling.GeneAssembler import GeneAssembler
from Classes.SequenceHandling.LibraryInfo import LibraryInfo
from Classes.SequenceHandling.Transcript import Transcript
from Classes.TSVBoy.TSVBoy import DiamondTSVBoy
from Classes.PassPath.PassPath import PassPath
from typing import Dict, Any, List
import json
import os
import shutil
from datetime import date


def merge_mode(argument_dict: Dict[str, Any]):
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


def prep_mode(argument_dict: Dict[str, Any]):
    no_complete_orf_count: int = 0
    no_diamond_match_count: int = 0
    seq_identified_count: int = 0

    print("Parsing TransDecoder input.", flush=True)
    fasta_iterator: TransDecoderFastaBoy = TransDecoderFastaBoy(argument_dict["input"])
    fasta_iterator.parse_fasta()
    transdecoder_dict: Dict[str, List[Dict, str]] = fasta_iterator.get_fasta_dict()

    print("Parsing Spice merge input.", flush=True)
    with open(argument_dict["json"], "r") as f:
        novel_transcript_map: Dict[str, Dict[str, Any]] = json.load(f)

    print("Parsing Diamond input.", flush=True)
    tsv_iterator: DiamondTSVBoy = DiamondTSVBoy(argument_dict["diamond"])
    tsv_iterator.parse_tsv()
    diamond_dict: Dict[str, Dict[str, List[Dict[str, Any]]]] = tsv_iterator.get_dict()

    print("Assigning sequences.", flush=True)
    for transcript_id in novel_transcript_map.keys():
        if transcript_id not in transdecoder_dict.keys():
            no_complete_orf_count += 1
            # print(transcript_id, "not found in TransDecoder peptides. Determining as non_coding.")
            novel_transcript_map[transcript_id]["biotype"] = "non_coding"
            novel_transcript_map[transcript_id]["tag"] = " ".join(["no_ORF",
                                                                   "NOVEL",
                                                                   "biotype:non_coding"])
        else:
            real_strand: str = novel_transcript_map[transcript_id]["strand"]
            keep_list: List[int] = list()
            for i, peptide_dict in enumerate(transdecoder_dict[transcript_id]):
                if peptide_dict["strand"] == real_strand:
                    keep_list.append(i)

            peptide_list: List[Dict[str, Any]] = [transdecoder_dict[transcript_id][i] for i in keep_list]

            if len(peptide_list) == 0:
                no_complete_orf_count += 1
                novel_transcript_map[transcript_id]["biotype"] = "non_coding"
                novel_transcript_map[transcript_id]["tag"] = " ".join(["no_ORF",
                                                                       "NOVEL",
                                                                       "biotype:non_coding"])
            else:
                best_hit_dict: Dict[str, str] = dict()
                best_hit_score: float = float("-inf")
                found_flag: bool = False

                for peptide_dict in transdecoder_dict[transcript_id]:
                    if peptide_dict["strand"] == novel_transcript_map[transcript_id]["strand"]:
                        if transcript_id in diamond_dict.keys():  # Was any alignment for the transcript found?
                            diamond_trans_dict: Dict[str, List[Dict[str, Any]]] = diamond_dict[transcript_id]
                            if peptide_dict["transcript_tag"] in diamond_trans_dict.keys():  # Was this seq aligned?
                                bit_score: float = diamond_trans_dict[peptide_dict["transcript_tag"]][0]["bit_score"]
                                e_value: float = diamond_trans_dict[peptide_dict["transcript_tag"]][0]["e-value"]
                                if found_flag:
                                    if bit_score > best_hit_score:
                                        best_hit_score = bit_score
                                        best_hit_dict = peptide_dict
                                        best_hit_dict["bit_score"] = str(bit_score)
                                        best_hit_dict["e-value"] = str(e_value)
                                else:
                                    found_flag = True
                                    best_hit_score = bit_score
                                    best_hit_dict = peptide_dict
                                    best_hit_dict["bit_score"] = str(bit_score)
                                    best_hit_dict["e-value"] = str(e_value)
                if not found_flag:
                    no_diamond_match_count += 1
                    # print("No coding sequence identified for", transcript_id + ". Determining as non-coding.")
                    novel_transcript_map[transcript_id]["biotype"] = "non_coding"
                    novel_transcript_map[transcript_id]["tag"] = " ".join(["no_diamond_hit",
                                                                           "NOVEL",
                                                                           "biotype:non_coding"])
                else:
                    seq_identified_count += 1
                    novel_transcript_map[transcript_id]["biotype"] = "protein_coding"
                    novel_transcript_map[transcript_id]["peptide"] = best_hit_dict["sequence"]
                    novel_transcript_map[transcript_id]["start_orf"] = best_hit_dict["start_orf"]
                    novel_transcript_map[transcript_id]["end_orf"] = best_hit_dict["end_orf"]
                    novel_transcript_map[transcript_id]["tag"] = " ".join(["e_value:" + best_hit_dict["e-value"],
                                                                           "bit_score:" + best_hit_dict["bit_score"],
                                                                           "NOVEL",
                                                                           "biotype:protein_coding"])

    output_filepath: str = os.path.join(argument_dict["out_path"], argument_dict["name"] + "_complete.fasta")

    with open(output_filepath, "w") as f:
        pass

    for transcript_id in novel_transcript_map.keys():
        gene_id: str = novel_transcript_map[transcript_id]["gene_id"]
        tag_list: str = novel_transcript_map[transcript_id]["tag"]
        synonym_list: str = " ".join(novel_transcript_map[transcript_id]["synonyms"])
        fasta_header: str = ">" + gene_id + "|" + transcript_id + "|" + tag_list + "|" + synonym_list
        if novel_transcript_map[transcript_id]["peptide"] == "":
            fasta_entry: str = fasta_header + "\n"
        else:
            fasta_entry: str = fasta_header + "\n" + novel_transcript_map[transcript_id]["peptide"] + "\n"
        with open(output_filepath, "a") as f:
            f.write(fasta_entry)

    total: int = seq_identified_count + no_complete_orf_count + no_diamond_match_count
    print("All sequence saved to:")
    print(output_filepath)

    print("Stats:\n\t",
          total, "transcripts processed.\n\t",
          str(round(seq_identified_count/total * 100, 2)) + "% were assigned a sequence.\n\t",
          str(round(no_complete_orf_count/total * 100,
                    2)) + "% determined as 'non_coding' -> no ORF was identified.\n\t",
          str(round(no_diamond_match_count/total * 100, 2)) + "% determined as 'non_coding' -> no Diamond hit.")


def novlib_mode(argument_dict: Dict[str, Any]):
    origin_lib_info: LibraryInfo = LibraryInfo(os.path.join(argument_dict["library"], "info.yaml"))

    novlib_root_path: str = os.path.join(argument_dict["out_path"], "spice_novlib_" + argument_dict["name"] + "_")
    novlib_root_path += origin_lib_info["info"]["species"] + "_"
    novlib_root_path += origin_lib_info["info"]["release"] + "_"
    novlib_root_path += origin_lib_info["info"]["fas_mode"]

    shutil.copytree(argument_dict["library"], novlib_root_path)

    novlib_info: LibraryInfo = LibraryInfo(os.path.join(novlib_root_path, "info.yaml"))
    del argument_dict["diamond"]
    del argument_dict["expression"]
    del argument_dict["json"]
    del argument_dict["threshold"]
    novlib_info["commandline_args"] = argument_dict

    novlib_info["status"]: Dict[str, bool] = {"01_id_collection": False,
                                              "02_sequence_collection": False,
                                              "03_small_protein_removing": False,
                                              "04_incorrect_entry_removing": False,
                                              "05_implicit_fas_scoring": False,
                                              "06_fasta_generation": False,
                                              "07_pairing_generation": False,
                                              "08_id_tsv_generation": False,
                                              "09_sequence_annotation": False,
                                              "10_fas_scoring": False}
    novlib_info["init_date"] = str(date.today())
    novlib_info["last_edit"] = str(date.today())

    novlib_info.save()

    with open(os.path.join(novlib_root_path, "paths.json"), "r") as f:
        paths_dict = json.load(f)
        paths_dict["root"] = novlib_root_path

    with open(os.path.join(novlib_root_path, "paths.json"), "w") as f:
        json.dump(paths_dict, f, indent=4)

    pass_path: PassPath = PassPath(paths_dict)

    gene_assembler: GeneAssembler = GeneAssembler(novlib_info["info"]["species"],
                                                  str(novlib_info["info"]["taxon_id"]))

    gene_assembler.load(pass_path)

    fasta_iterator: SpiceFastaBoy = SpiceFastaBoy(argument_dict["input"], int(novlib_info["info"]["taxon_id"]))
    fasta_iterator.parse_fasta()
    novel_transcript_dict: Dict[str, List[Transcript]] = fasta_iterator.get_fasta_dict()

    for gene in gene_assembler.get_genes():
        if gene.get_id() in novel_transcript_dict.keys():
            for transcript in novel_transcript_dict[gene.get_id()]:
                gene.add_transcript(transcript, True)

    gene_assembler.save_seq(pass_path)
    gene_assembler.save_info(pass_path)
    gene_assembler.save_fas(pass_path)

    # Update library info after adding everything.
    # remove small proteins.
    # remove incorrect entries
    # do implicit fas scoring (remember to also include non_coding now).
    # generate fasta file (including all protein_coding transcripts)
    # generate pairings. Look at the whole parings thing a bit and consider how long the rework would take.
    #   Maybe only split up Titin into 20 jobs.
    # create the id tsv

    # then annotate
    # then run FAS. Done.


def main():
    argument_parser: ReduxArgParse = ReduxArgParse(["--input", "--out_path", "--expression", "--threshold", "--mode",
                                                    "--name", "--json", "--diamond", "--library"],
                                                   [str, str, str, float, str, str, str, str, str],
                                                   ["store", "store", "store", "store", "store", "store", "store",
                                                    "store", "store"],
                                                   [1, 1, None, "?", 1, 1, "?", "?", "?"],
                                                   ["""Path to the input file. Depends on the mode. 
                                                    'merge': .txt-file containing the paths to all annotation-gtfs
                                                     that shall be merged. One path per line.
                                                    'prep': LongOrf.pep output of TransDecoder.
                                                    'novlib': Fasta-file containing novel transcripts. The file
                                                    requires a header structure like this:
                                                    ><GENE_ID>|<TRANSCRIPT_ID>|<TAG1> ... <TAGn>|<SYN1> ... <SYNn>
                                                    SYN stands for synonyms that shall all be recognised as valid
                                                    identifiers for the transcript. If there are no synonyms the third
                                                     '|'-symbol is still required for parsing the file.
                                                    At least one specific tag must be added:
                                                    biotype:<BIOTYPE>. If a transcript shall be considered non-coding
                                                    give it the biotype 'non_coding'.""",  # INPUT
                                                    """Path to the output directory for <name>.gtf,
                                                    <name>.json, <name>.fasta, <name>_complete.fasta,
                                                     novlib_<species>_<release>_<fas_mode>_<name> etc.""",  # OUT_PATH
                                                    """Only used in 'merge'-mode. Path to a text file containing 
                                                    the paths to gtf files including transcript abundances. Only 
                                                    transcripts will be kept which exceed the float given in 
                                                    the --threshold parameter.""",  # EXPRESSION
                                                    """Expression threshold, which will be 
                                                     used for transcript curation.""",  # THRESHOLD
                                                    """Either 1:'merge', 2:'prep' or 3:'novlib' depending on the
                                                    stage of the workflow.""",  # MODE
                                                    "Name for the output file.",  # NAME
                                                    """Path to the <name>.json file that was output during merge
                                                    mode. This argument is only required for
                                                    'prep' mode.""",  # JSON
                                                    """Path to the .tsv file output by DIAMOND. Only required for 'prep'
                                                    mode.""",  # DIAMOND
                                                    """Path to the Spice library that shall be extended. Only required
                                                    for 'novlib mode."""  # LIBRARY
                                                    ])
    argument_parser.generate_parser()
    argument_parser.execute()
    argument_dict: Dict[str, Any] = argument_parser.get_args()

    argument_dict["mode"] = argument_dict["mode"][0]
    argument_dict["out_path"] = argument_dict["out_path"][0]
    argument_dict["input"] = argument_dict["input"][0]
    argument_dict["name"] = argument_dict["name"][0]

    if argument_dict["mode"] == "merge":
        merge_mode(argument_dict)

    elif argument_dict["mode"] == "prep":
        prep_mode(argument_dict)

    elif argument_dict["mode"] == "novlib":
        novlib_mode(argument_dict)


if __name__ == "__main__":
    main()