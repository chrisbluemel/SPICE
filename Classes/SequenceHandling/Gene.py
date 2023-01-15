#!/bin/env python

#######################################################################
# Copyright (C) 2023 Christian Bluemel
#
# This file is part of main.
#
#  Gene is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Gene is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with PathwayTrace.  If not, see <http://www.gnu.org/licenses/>.
#
#######################################################################


from typing import Type, List

from Classes.SequenceHandling.Transcript import Transcript
from Classes.SequenceHandling.Protein import Protein


class Gene:

    fasta_template = ">{0}|{1}|{2}\n{3}"

    def __init__(self) -> None:
        self.id_gene: str = ""
        self.id_taxon: str = ""
        self.species: str = ""
        self.expression_value: float = 0
        self.transcripts: List[Transcript] = list()

    def set_id_gene(self, id_gene: str) -> None:
        self.id_gene = id_gene

    def set_id_taxon(self, id_taxon: str) -> None:
        """

        :type id_taxon: str
        """
        self.id_taxon = id_taxon

    def set_species(self, species: str):
        self.species = species

    def set_expression_value(self, expression: float) -> None:
        """

        :type expression: float
        """
        self.expression_value = expression

    # noinspection PyTypeChecker
    def add_transcript(self, transcript: Type[Transcript]) -> None:
        """

        :type transcript: Transcript
        """
        self.transcripts.append(transcript)

    def get_transcripts(self) -> List[Transcript]:
        return self.transcripts

    def get_expression_value(self) -> float:
        return self.expression_value

    def get_id_gene(self) -> str:
        return self.id_gene

    def get_id_taxon(self) -> str:
        return self.id_taxon

    def get_species(self) -> str:
        return self.species

    @property
    def fasta(self) -> str:
        proteins: List[Protein] = [transcript for transcript in self.transcripts if isinstance(transcript, Protein)]
        output: str = "\n".join([self.fasta_template.format(self.get_id_gene(),
                                                            protein.get_id_transcript(),
                                                            protein.get_id_protein(),
                                                            protein.get_sequence()) for protein in proteins])
        return output


def main():
    gene = Gene()
    gene.set_id_gene("standin_gene_id")
    gene.set_species("human")
    gene.set_expression_value(12.9)
    gene.set_id_taxon("9606")

    protein1: Protein = Protein()
    protein1.set_id_protein("p1")
    protein1.set_id_transcript("tp1")
    protein1.set_sequence("AAA")

    protein2: Protein = Protein()
    protein2.set_id_protein("p2")
    protein2.set_id_transcript("tp2")
    protein2.set_sequence("CCC")

    protein3: Protein = Protein()
    protein3.set_id_protein("p3")
    protein3.set_id_transcript("tp3")
    protein3.set_sequence("LLL")

    transcript1: Transcript = Transcript()
    transcript1.set_id_transcript("t1")

    gene.add_transcript(protein1)
    gene.add_transcript(protein2)
    gene.add_transcript(protein3)
    gene.add_transcript(transcript1)

    print(gene.fasta)


if __name__ == "__main__":
    main()