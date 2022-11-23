import json
import os.path
from typing import Optional, Tuple

import numpy as np
from thefuzz import fuzz

from knowledge_graphs.BasicKG import BasicKG
from knowledge_graphs.WikDataEmbeddings import WikiDataEmbeddings
from knowledge_graphs.wikidata_queries import imdb_query, person_exact_lowercase_label_match, exact_lowercase_label_match, person_or_film_lowercase_label_match, label_query


class WikiDataKG(BasicKG):
    def __init__(self,
                 kg_tuple_file_path: str,
                 imdb2movienet_filepath: str,
                 entity_label_filepath: Optional[str] = None,
                 property_label_filepath: Optional[str] = None,
                 property_extended_label_filepath: Optional[str] = None,
                 entity_emb_filepath: str = None,
                 entity_id_mapping: str = None,
                 relation_emb: str = None,
                 relation_id_mapping: str = None
                 ):
        super().__init__(kg_tuple_file_path, entity_label_filepath, property_label_filepath)
        self.imdb2movienet = json.load(open(imdb2movienet_filepath, 'r'))
        self._property_extended_label_set = json.load(open(property_extended_label_filepath, 'r')) \
            if property_extended_label_filepath else None

        self.kg_embeddings = WikiDataEmbeddings(
            entity_emb_filepath=entity_emb_filepath,
            entity_id_mapping=entity_id_mapping,
            relation_emb=relation_emb,
            relation_id_mapping=relation_id_mapping
        ) if entity_emb_filepath and entity_id_mapping and relation_emb and relation_id_mapping else None

    def check_if_entity_in_kg(self, wk_ent_id: str) -> bool:
        return str(self.namespaces.WD[wk_ent_id]) in self.entity_labels_dict.keys()

    def check_if_property_in_kg(self, wk_prop_id: str) -> bool:
        return str(self.namespaces.WDT[wk_prop_id]) in self.property_labels_dict.keys()

    def get_object_or_objects(self, wk_ent_id: str, wk_prop_id: str) -> list:
        return [obj for obj in self.kg.objects(self.namespaces.WD.wk_ent_id, self.namespaces.WDT.wk_prop_id)]

    def get_imdb_id(self, wk_ent_id: str) -> Optional[str]:
        if self.check_if_entity_in_kg(wk_ent_id):
            query_result = self.kg.query(imdb_query, initBindings={"id": self.namespaces.WD[wk_ent_id]})
            imdb_ids = [str(imdb[0]) for imdb in query_result]

            if len(imdb_ids) >= 1:
                return imdb_ids[0]

        return None

    def get_entity_label(self, wk_ent_id: str) -> Optional[str]:
        if self.check_if_entity_in_kg(wk_ent_id):
            return self.entity_labels_dict[str(self.namespaces.WD[wk_ent_id])]

        return None

    def get_property_label(self, wk_prop_id: str) -> Optional[str]:
        if self.check_if_property_in_kg(wk_prop_id):
            return self.property_labels_dict[str(self.namespaces.WDT[wk_prop_id])]

        return None

    def get_wkdata_entid_based_on_label_match(self, entity_string_to_match: str, ent_type: Optional[str] = None) \
            -> Optional[str]:
        wk_ent_id = None
        query_result = []
        entity_string_to_match = entity_string_to_match.lower()

        # First try exact lower case match with SPARQL
        if ent_type is None:
            query_result = self.kg.query(exact_lowercase_label_match.format(entity_string_to_match))

        elif ent_type == 'person':
            query_result = self.kg.query(person_exact_lowercase_label_match.format(entity_string_to_match))

        elif ent_type == 'person or movie':
            query_result = self.kg.query(person_or_film_lowercase_label_match.format(entity_string_to_match))

        detected_wk_entities = [str(wk_ent_id) for wk_ent_id, _ in query_result]

        if len(detected_wk_entities) == 1:
            wk_ent_id = os.path.basename(detected_wk_entities[0])

        else:
            # Try matching the entity based on the edit distance
            matches = np.array(
                [(os.path.basename(wk_id), fuzz.token_sort_ratio(entity_string_to_match, label))
                 for wk_id, label in self.entity_labels_dict.items()
                 if fuzz.token_sort_ratio(entity_string_to_match, label) > 75],
            )

            if matches.shape[0] > 0:
                wk_ent_id = matches[matches[:, 1].argmax(), 0]

        return wk_ent_id

    def get_wkdata_propid_based_on_label_match(self, property_str: str) -> Optional[str]:
        # Try matching the entity based on the edit distance
        matches = np.array(
            [wk_id for wk_id, label_list in self._property_extended_label_set.items()
             if any([fuzz.token_sort_ratio(property_str, label) > 75 for label in label_list])],
        )

        if len(matches) > 0:
            return matches[matches.argmax()]
        else:
            return None

    def get_movinet_id(self, imdb_id: str) -> Optional[str]:
        if imdb_id in self.imdb2movienet.keys():
            return self.imdb2movienet[imdb_id]
        else:
            return None

    def deduce_object_using_embeddings(
            self,
            wk_ent_id: str, wk_prop_id: str,
            top_k: int = 10, ptg_max_diff_top_k: float = 0.2, report_max: int = 4) -> Tuple[str, ...]:

        wk_ent_ids = self.kg_embeddings.deduce_object(wk_ent_id, wk_prop_id, top_k, ptg_max_diff_top_k, report_max)
        return tuple([self.get_entity_label(wk_ent_id) for wk_ent_id in wk_ent_ids])


if __name__ == '__main__':
    kg = WikiDataKG(
        kg_tuple_file_path='../setup_data/wikidata_kg/14_graph.nt',
        imdb2movienet_filepath='../setup_data/wikidata_kg/imdb2movienet.json',
        entity_label_filepath='../setup_data/wikidata_kg/wkdata_entity_labels_dict.json',
        property_label_filepath='../setup_data/wikidata_kg/wkdata_property_labels_dict.json',
        property_extended_label_filepath='../setup_data/wikidata_kg/wk_data_names_props_of_interest.json',
        entity_emb_filepath='../setup_data/wikidata_kg/embeddings/entity_embeds.npy',
        entity_id_mapping='../setup_data/wikidata_kg/embeddings/entity_ids.del',
        relation_emb='../setup_data/wikidata_kg/embeddings/relation_embeds.npy',
        relation_id_mapping='../setup_data/wikidata_kg/embeddings/relation_ids.del'
    )

    assert kg.get_imdb_id(wk_ent_id='Q40523') == 'nm0000210'
    assert 'nm0000770' in kg.imdb2movienet
    assert kg.imdb2movienet['nm0000770']

    assert kg.get_wkdata_entid_based_on_label_match('Martin Scorsese') == 'Q41148'
    assert kg.get_wkdata_entid_based_on_label_match('Martin Scorsese', ent_type='person') == 'Q41148'
    assert kg.get_wkdata_entid_based_on_label_match('Martin Scorssese') == 'Q41148'


