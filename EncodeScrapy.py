#!/bin/env python

#######################################################################
# Copyright (C) 2023 Christian Bluemel
#
# This file is part of Spice.
#
#  EncodeScrapy is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  EncodeScrapy is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Spice.  If not, see <http://www.gnu.org/licenses/>.
#
#######################################################################

from typing import Dict, Any, List
import json
import requests
import os
import shutil
import datetime
from pathlib import Path
from Classes.ReduxArgParse.ReduxArgParse import ReduxArgParse

URL: str = "https://www.encodeproject.org/batch_download/?type=Experiment&@id=/experiments/{0}/&files.processed=true"
EXP_URL: str = "https://www.encodeproject.org/experiments/{0}/"


def extract_id(link: str) -> str:
    split_link: List[str] = link.split("/")
    if split_link[-1] == "":
        return split_link[-2]
    else:
        return split_link[-1]


def extract_experiment_ids_from_links(experiment_file_path: str) -> List[str]:
    return [extract_id(line) for line in open_url_file(experiment_file_path)]


def open_url_file(in_path: str) -> List[str]:
    with open(in_path, "r") as f:
        file = f.read()
    return file.split("\n")


def download(url: str, file_id: str, exp_id: str, out_path: str, suffix: str, log_path: str):
    print("\tDownloading", file_id + suffix)

    response = requests.get(url, stream=True)
    if response.status_code == 200:
        Path(os.path.join(out_path, exp_id)).mkdir(parents=True, exist_ok=True)
        file_path: str = os.path.join(out_path, exp_id, file_id + suffix)
        with open(file_path, 'wb') as f:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, f)
        with open(log_path, "r") as f:
            file_paths: set = set(f.read().split("\n"))
        if len(file_paths) == 1:
            if len(list(file_paths)[0]) == 0:
                file_paths = set()
        file_paths.add(file_path)
        file_paths: str = "\n".join(list(file_paths))

        with open(log_path, "w") as f:
            f.write(file_paths)


def download_filtered_alignment(exp_id, out_path: str, log_path: str):
    url: str = URL.format(exp_id)
    response_files = requests.get(url)
    if response_files.status_code == 200:
        download_link_list: List[str] = response_files.content.decode('utf-8').split("\n")
        download_link_list = [link for link in download_link_list if check_link_meta(link,
                                                                                     "alignment",
                                                                                     "alignments")]
        for download_link in download_link_list:
            file_id: str = download_link.split("@@download/")[1].split(".")[0]
            download(download_link, file_id, exp_id, out_path, ".bam", log_path)

        with open(os.path.join(out_path, exp_id, "info.json"), "r") as f:
            info_dict: Dict[str, Any] = json.load(f)
        info_dict["alignment_urls"] = download_link_list
        info_dict["replicate_count"] = max(len(info_dict["annotation_urls"]), len(info_dict["annotation_urls"]))
        with open(os.path.join(out_path, exp_id, "info.json"), "w") as f:
            json.dump(info_dict, f, indent=4)
    else:
        print(f"Error: {response_files.status_code} - {response_files.text}")


def download_annotation(exp_id: str, out_path: str, log_path: str):
    url: str = URL.format(exp_id)
    response_files = requests.get(url)
    if response_files.status_code == 200:
        download_link_list: List[str] = response_files.content.decode('utf-8').split("\n")
        download_link_list = [link for link in download_link_list if check_link_meta(link,
                                                                                     "annotation",
                                                                                     "transcriptome annotations")]
        for download_link in download_link_list:
            file_id: str = download_link.split("@@download/")[1].split(".")[0]
            download(download_link, file_id, exp_id, out_path, ".gtf.gz", log_path)

        with open(os.path.join(out_path, exp_id, "info.json"), "r") as f:
            info_dict: Dict[str, Any] = json.load(f)
        info_dict["annotation_urls"] = download_link_list
        info_dict["replicate_count"] = max(len(info_dict["annotation_urls"]), len(info_dict["annotation_urls"]))
        with open(os.path.join(out_path, exp_id, "info.json"), "w") as f:
            json.dump(info_dict, f, indent=4)
    else:
        print(f"Error: {response_files.status_code} - {response_files.text}")


def get_experiment_meta(exp_id: str) -> Dict[str, str]:
    meta_url: str = EXP_URL.format(exp_id) + "?format=json"
    response = requests.get(meta_url)
    if response.status_code == 200:
        meta_json = response.json()

        output_dict: Dict[str, str] = dict()
        output_dict["biosample_summary"] = meta_json["biosample_summary"]
        output_dict["assembly"] = meta_json["assembly"][0]
        output_dict["description"] = meta_json["description"]

        return output_dict
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return dict()


def get_link_meta(url: str) -> Dict[str, str]:
    if "processed=true" in url or len(url) == 0:
        return dict()
    else:
        meta_url: str = url.split("@@download")[0] + "?format=json"
        response = requests.get(meta_url)
        if response.status_code == 200:
            meta_json = response.json()
            output_dict: Dict[str, str] = dict()
            output_dict["assembly"] = meta_json["assembly"]
            output_dict["genome_annotation"] = meta_json["genome_annotation"]
            output_dict["mapped_run_type"] = meta_json["mapped_run_type"]
            output_dict["output_category"] = meta_json["output_category"]
            output_dict["output_type"] = meta_json["output_type"]
            output_dict["status"] = meta_json["status"]

        else:
            print(f"Error: {response.status_code} - {response.text}")
            return dict()


def check_link_meta(url: str, output_category: str, output_type: str) -> bool:
    if "processed=true" in url or len(url) == 0:
        return False
    else:
        meta_url: str = url.split("@@download")[0] + "?format=json"
        response = requests.get(meta_url)
        if response.status_code == 200:
            meta_json = response.json()
            flag: bool = meta_json["output_category"] == output_category
            flag = flag and meta_json["status"] == "released"
            flag = flag and meta_json["output_type"] == output_type
            if flag:
                return True
            else:
                return False
        else:
            print(f"Error: {response.status_code} - {response.text}")


def make_log_file(exp_id: str, out_path: str):
    experiment_meta: Dict[str, str] = get_experiment_meta(exp_id)

    directory: str = os.path.join(out_path, exp_id)
    info_file: str = os.path.join(directory, "info.json")
    Path(directory).mkdir(parents=True, exist_ok=True)
    if not Path(info_file).exists():
        info_dict: Dict[str, Any] = {
            "experiment_id": exp_id,
            "replicate_count": 0,
            "experiment_url": EXP_URL.format(exp_id),
            "annotation_urls": list(),
            "alignment_urls": list(),
            "description": experiment_meta["description"],
            "biosample_summary": experiment_meta["biosample_summary"],
            "assembly": experiment_meta["assembly"]
        }
        with open(info_file, "w") as f:
            json.dump(info_dict, f, indent=4)


def make_experiment_list_file(experiment_ids: List[str], out_path: str):
    list_path: str = os.path.join(out_path, "experiment_list.txt")
    if not Path(list_path).exists():
        with open(list_path, "w") as f:
            f.write("\n".join(experiment_ids))
    else:
        with open(list_path, "r") as f:
            experiment_ids_old = set(f.read().split("\n"))

        experiment_list: str = "\n".join(list(set(experiment_ids).union(experiment_ids_old)))

        with open(list_path, "w") as f:
            f.write(experiment_list)


def timestamp_print(i: int, id_count: int, exp_id: str, keyword: str):
    time = datetime.datetime.fromtimestamp(datetime.datetime.now().timestamp())
    timestamp = time.strftime('%H:%M:%S')
    print(str(i + 1) + "/" + str(id_count) + ":", "Downloading", keyword, "for", exp_id, "|", timestamp)


def make_alignment_log_file(out_path: str) -> str:
    list_path: str = os.path.join(out_path, "alignment_list.txt")
    if not Path(list_path).exists():
        with open(list_path, "w") as f:
            pass
    return list_path


def make_annotation_log_file(out_path: str) -> str:
    list_path: str = os.path.join(out_path, "annotation_list.txt")
    if not Path(list_path).exists():
        with open(list_path, "w") as f:
            pass
    return list_path


def main():
    argument_parser: ReduxArgParse = ReduxArgParse(["--input", "--outdir"],
                                                   [str, str],
                                                   ["store", "store"],
                                                   [1, 1],
                                                   ["Path to the file containing the encode links.",
                                                    "Path to the directory that shall contain the downloaded files."])
    argument_parser.generate_parser()
    argument_parser.execute()
    argument_dict: Dict[str, Any] = argument_parser.get_args()
    argument_dict["input"] = argument_dict["input"][0]
    argument_dict["outdir"] = argument_dict["outdir"][0]

    experiment_ids: List[str] = extract_experiment_ids_from_links(argument_dict["input"])

    make_experiment_list_file(experiment_ids, argument_dict["outdir"])
    annotation_log_path: str = make_annotation_log_file(argument_dict["outdir"])
    alignment_log_path: str = make_alignment_log_file(argument_dict["outdir"])

    id_count: int = len(experiment_ids)
    for i, exp_id in enumerate(experiment_ids):

        make_log_file(exp_id, argument_dict["outdir"])

        timestamp_print(i, id_count, exp_id, "annotation")
        download_annotation(exp_id, argument_dict["outdir"], annotation_log_path)

        timestamp_print(i, id_count, exp_id, "alignment")
        download_filtered_alignment(exp_id, argument_dict["outdir"], alignment_log_path)

    print("All done!")


if __name__ == "__main__":
    main()
