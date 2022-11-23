import os
import csv
from typing import Union

import rdflib
import numpy as np
from sklearn.metrics import pairwise_distances

from knowledge_graphs.BasicKG import Namespaces


def _load_id_mappers(id_mapping_filepath: str):
    with open(id_mapping_filepath, 'r') as ifile:
        wk_id2emb_id = {rdflib.term.URIRef(ent): int(idx) for idx, ent in csv.reader(ifile, delimiter='\t')}
        emb_id2wk_id = {v: k for k, v in wk_id2emb_id.items()}

        return wk_id2emb_id, emb_id2wk_id


class WikiDataEmbeddings:
    def __init__(self, entity_emb_filepath: str, entity_id_mapping: str,
                 relation_emb: str, relation_id_mapping: str):
        self.namespaces = Namespaces()

        # load the embeddings
        self.entity_emb = np.load(entity_emb_filepath)
        self.relation_emb = np.load(relation_emb)

        # load dictinoaries to mapa wikidata entity and property id to the embeddings id or index in the array
        self.ent2id, self.id2ent = _load_id_mappers(entity_id_mapping)
        self.rel2id, self.id2rel = _load_id_mappers(relation_id_mapping)

    def deduce_object(self, wk_ent_id: str, wk_prop_id: str) -> Union[str, tuple[str]]:
        # Retrieve the embeddings of the corresponding elements
        subj_emb = self.entity_emb[self.ent2id[self.namespaces.WD[wk_ent_id]]]
        pred_emb = self.relation_emb[self.rel2id[self.namespaces.WDT[wk_prop_id]]]

        # Add vectors according to TransE scoring function.
        pred_obj_emb = subj_emb + pred_emb

        # Compute distance to *any* entity
        dist = pairwise_distances(pred_obj_emb.reshape(1, -1), self.entity_emb).reshape(-1)

        # Find most plausible entities
        most_likely = dist.argsort()

        # Compute ranks of entities
        ranks = dist.argsort().argsort()

        # Calculate difference in distance between 1 and 10th option.
        # All those below 10% of that distance are included as the answer
        large_dist = dist[most_likely[0]] - dist[most_likely[10]]
        plausible_objects = dist[most_likely[0]] - dist[most_likely[0: 10]] < 0.2 * large_dist

        most_likely[plausible_objects]