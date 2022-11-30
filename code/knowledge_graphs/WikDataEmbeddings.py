import os
import csv
from typing import Tuple, Optional

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

    def deduce_object(self, wk_ent_id: str, wk_prop_id: str,
                      top_k: int = 10, ptg_max_diff_top_k: float = 0.2, report_max: int = 4) -> \
            Optional[Tuple[str, ...]]:

        # Retrieve the embeddings of the corresponding elements
        if self.namespaces.WD[wk_ent_id] in self.ent2id.keys() and \
                self.namespaces.WDT[wk_prop_id] in self.rel2id.keys():
            subj_emb = self.entity_emb[self.ent2id[self.namespaces.WD[wk_ent_id]]]
            pred_emb = self.relation_emb[self.rel2id[self.namespaces.WDT[wk_prop_id]]]

            # Add vectors according to TransE scoring function.
            pred_obj_emb = subj_emb + pred_emb

            dist_top_k, top_k_emb_ids = self._return_most_similar_entites(embedding=pred_obj_emb, top_k=top_k)

            # Calculate difference in distance between 1 and 10th option.
            # All those below 10% of that distance are included as the answer
            large_dist = dist_top_k[-1] - dist_top_k[0]
            plausible_objects = dist_top_k - dist_top_k[0] < ptg_max_diff_top_k * large_dist

            object_emb_id_to_report = top_k_emb_ids[plausible_objects]
            object_emb_id_to_report = tuple(object_emb_id_to_report[:min(len(object_emb_id_to_report), report_max)])

            return object_emb_id_to_report

        else:
            return None


    def get_most_similar_entities_to_centroid(self, wk_ent_id_list: list, top_k: int = 10):
        # Get embedding for centroid
        centroid = self._calculate_centroid(wk_ent_id_list)

        # Get the entities most similar to the centroid
        _, closest_entities = self._return_most_similar_entites(centroid, top_k=top_k + len(wk_ent_id_list))

        # Remove the entities that compose the cnentroid
        closest_entities = [entity for entity in closest_entities if entity not in wk_ent_id_list]
        closest_entities = closest_entities[: top_k]

        return closest_entities

    def _return_most_similar_entites(self, embedding: np.ndarray, top_k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        # Compute distance to *any* entity
        dist = pairwise_distances(embedding.reshape(1, -1), self.entity_emb).reshape(-1)

        # Find most plausible entities
        most_likely = dist.argsort()

        # Return the top_k closest entities
        dist_top_k_entities = dist[most_likely[0: top_k]]
        id_top_k_closest_entities = np.array(
            [os.path.basename(str(self.id2ent[object_emb_id])) for object_emb_id in most_likely[0: top_k]])
        return dist_top_k_entities, id_top_k_closest_entities

    def _calculate_centroid(self, wk_ent_id_list: list) -> np.ndarray:
        centroid_emb = None
        for i, wk_ent_id_i in enumerate(wk_ent_id_list):
            if i == 0:
                centroid_emb = self.entity_emb[self.ent2id[self.namespaces.WD[wk_ent_id_i]]]
            else:
                centroid_emb += self.entity_emb[self.ent2id[self.namespaces.WD[wk_ent_id_i]]]

        return centroid_emb/len(wk_ent_id_list)


if __name__ == '__main__':
    # Get the the entity embeddings closest to the lion king
    wk_emb = WikiDataEmbeddings(
        entity_emb_filepath='../../setup_data/wikidata_kg/embeddings/entity_embeds.npy',
        entity_id_mapping='../../setup_data/wikidata_kg/embeddings/entity_ids.del',
        relation_emb='../../setup_data/wikidata_kg/embeddings/relation_embeds.npy',
        relation_id_mapping='../../setup_data/wikidata_kg/embeddings/relation_ids.del'
    )

    a = wk_emb.deduce_object(wk_ent_id='Q36479', wk_prop_id='P495')

    b = wk_emb.get_most_similar_entities_to_centroid(
        ['Q179673', 'Q36479', 'Q179673'], top_k=10
    )
    print(b)


