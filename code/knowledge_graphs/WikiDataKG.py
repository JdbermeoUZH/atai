import json
import os.path

import numpy as np
from typing import Optional

from thefuzz import fuzz

from knowledge_graphs.BasicKG import BasicKG
from knowledge_graphs.wikidata_queries import imdb_query, person_exact_lowercase_label_match, exact_lowercase_label_match


class WikiDataKG(BasicKG):
    def __init__(self,
                 kg_tuple_file_path: str,
                 imdb2movienet_filepath: str,
                 entity_label_filepath: Optional[str] = None,
                 property_label_filepath: Optional[str] = None):
        super().__init__(kg_tuple_file_path, entity_label_filepath, property_label_filepath)
        self.imdb2movienet = json.load(open(imdb2movienet_filepath, 'r'))

    def check_if_entity_in_kg(self, wk_ent_id: str) -> bool:
        return ((self.namespaces.WD[wk_ent_id], None, None) in self.kg) or \
               ((None, None, self.namespaces.WD[wk_ent_id]) in self.kg)

    def check_if_property_in_kg(self, wk_prop_id: str) -> bool:
        return (None, self.namespaces.WD[wk_prop_id], None) in self.kg

    def get_imdb_id(self, wk_ent_id: str) -> Optional[str]:
        if self.check_if_entity_in_kg(wk_ent_id):
            query_result = self.kg.query(imdb_query, initBindings={"id": self.namespaces.WD[wk_ent_id]})
            imdb_ids = [str(imdb[0]) for imdb in query_result]

            if len(imdb_ids) >= 1:
                return imdb_ids[0]

        return None

    def get_wkdata_entid_based_on_label_match(self, entity_string_to_match: str, ent_type: Optional[str] = None) -> str:
        wk_ent_id = None
        query_result = []
        entity_string_to_match = entity_string_to_match.lower()

        # First try exact lower case match with SPARQL
        if ent_type is None:
            query_result = self.kg.query(exact_lowercase_label_match.format(entity_string_to_match))

        elif ent_type == 'person':
            query_result = self.kg.query(person_exact_lowercase_label_match.format(entity_string_to_match))

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
            wk_ent_id = matches[matches[:, 1].argmax(), 0]

        return wk_ent_id

    def get_movinet_id(self, imdb_id: str) -> Optional[str]:
        if imdb_id in self.imdb2movienet.keys():
            return self.imdb2movienet[imdb_id]
        else:
            return None


if __name__ == '__main__':
    kg = WikiDataKG(
        kg_tuple_file_path='../setup_data/14_graph.nt',
        imdb2movienet_filepath='../setup_data/imdb2movienet.json',
        entity_label_filepath='../setup_data/wkdata_entity_labels_dict.json',
        property_label_filepath='../setup_data/wkdata_property_labels_dict.json'
    )

    assert kg.get_imdb_id(wk_ent_id='Q40523') == 'nm0000210'
    assert 'nm0000770' in kg.imdb2movienet
    assert kg.imdb2movienet['nm0000770']

    assert kg.get_wkdata_entid_based_on_label_match('Martin Scorsese') == 'Q41148'
    assert kg.get_wkdata_entid_based_on_label_match('Martin Scorsese', ent_type='person') == 'Q41148'
    assert kg.get_wkdata_entid_based_on_label_match('Martin Scorssese') == 'Q41148'


