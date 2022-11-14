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
Created on Tue Aug  2 11:13:06 2022
@author: chrisbl
"""

import plotly.graph_objects as go
import math
from valves.fas_utility import calc_rmsd
    

def scale_list(scale_factor, float_list):
    output_list = []
    for value in float_list:
        output_list.append(value * scale_factor)
    return output_list


def make_graph(fas_lib, gene_id, sample_names, categories, sigma_list, rmsd, filepath):
    fig = go.Figure()
    for i, name in enumerate(sample_names):
        fig.add_trace(go.Scatterpolar(
            r=sigma_list[i] + [sigma_list[i][0]],
            theta=categories + [categories[0]],
            fill="toself",
            name=name
            ))
    fig.add_annotation(x=0, y=-0.2,
                text="RMSD=" + str(rmsd),
                showarrow=False)
    fig.add_annotation(x=0, y=-0.14,
                text=gene_id,
                showarrow=False)
    fig.update_layout(
        autosize=False,
        width=604,
        height=387,
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0,1]
                )),
        showlegend=True,
        paper_bgcolor="LightSteelBlue"
        )
    #fig.show()
    fig.write_image(file=filepath)
    


def prepare_ring_pair_visual(ring_list, gene_id, conditions):
    protein_ids = []
    mean_movs = []
    mean_rel_exprs = []
    min_movs = []
    max_movs = []
    plus_std_movs = []
    minus_std_movs = []
    itersample_rmsd = []

    for prot_ids_list, mean_mov_list, mean_rel_expr_list, min_mov_list, max_mov_list, plus_std_mov_list, minus_std_mov_list, intersample_rmsd_mean in ring_list:
        protein_ids = prot_ids_list
        mean_movs.append(mean_mov_list)
        mean_rel_exprs.append(mean_rel_expr_list)
        min_movs.append(min_mov_list)
        max_movs.append(max_mov_list)
        plus_std_movs.append(plus_std_mov_list)
        minus_std_movs.append(minus_std_mov_list)

    
    delete_list = []
    for i, mean_rel_expr in enumerate(mean_rel_exprs):
        for j, _ in enumerate(mean_rel_expr):
            if all([ entry[j] == 0 for entry in mean_rel_exprs ]):
                delete_list.append(j)
        break
    
    categories = []
    final_mean_movs = []
    final_min_movs = []
    final_max_movs = []
    final_plus_std_movs = []
    final_minus_std_movs = []
    
    for i in range(2):
        final_mean_movs.append([])
        final_min_movs.append([])
        final_max_movs.append([])
        final_plus_std_movs.append([])
        final_minus_std_movs.append([])
    for i, prot_id in enumerate(protein_ids):
        if i not in delete_list:
            categories.append(prot_id)
            for j in range(2):
                final_mean_movs[j].append(mean_movs[j][i])
                final_min_movs[j].append(min_movs[j][i])
                final_max_movs[j].append(max_movs[j][i])
                final_plus_std_movs[j].append(plus_std_movs[j][i])
                final_minus_std_movs[j].append(minus_std_movs[j][i])

    rmsd = calc_rmsd(final_mean_movs)
    
    rmsd_max = calc_rmsd(final_max_movs)
    rmsd_plus_std = calc_rmsd(final_plus_std_movs)

    rmsd_max_smaller_1 = False if rmsd_max < itersample_rmsd[0] else True
    rmsd_mean_plus_std_smaller_1 = False if rmsd_plus_std < itersample_rmsd[0] else True
    rmsd_max_smaller_2 = False if rmsd_max < itersample_rmsd[1] else True
    rmsd_mean_plus_std_smaller_2 = False if rmsd_plus_std < itersample_rmsd[1] else True
       
    
    output_dict = dict()
    output_dict["gene_id"] = gene_id
    output_dict["categories"] = categories
    output_dict["mean_movement"] = final_mean_movs
    output_dict["min_movement"] = final_min_movs
    output_dict["max_movement"] = final_max_movs
    output_dict["plus_std_movement"] = final_plus_std_movs
    output_dict["minus_std_movement"] = final_minus_std_movs
    
    output_dict["rmsd_max_smaller_1"] = str(int(rmsd_max_smaller_1))
    output_dict["rmsd_mean_plus_std_smaller_1"] = str(int(rmsd_mean_plus_std_smaller_1))
    output_dict["rmsd_max_smaller_2"] = str(int(rmsd_max_smaller_2))
    output_dict["rmsd_mean_plus_std_smaller_2"] = str(int(rmsd_mean_plus_std_smaller_2))
        
    output_dict["rmsd"] = rmsd
    
    return output_dict

def main():
    pass


if __name__ == "__main__":
    main()
    