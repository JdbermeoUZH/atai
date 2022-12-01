import json
import os.path
import random
from typing import Optional, Tuple

import numpy as np
from thefuzz import fuzz

from knowledge_graphs.BasicKG import BasicKG
from knowledge_graphs.wikidata.embeddings.WikDataEmbeddings import WikiDataEmbeddings
from knowledge_graphs.wikidata import wikidata_queries


class WikiDataKG(BasicKG):
    def __init__(self,
                 kg_tuple_file_path: str,
                 imdb2movienet_filepath: str,
                 entity_label_filepath: Optional[str],
                 property_label_filepath: Optional[str],
                 property_extended_label_filepath: Optional[str],
                 entity_emb_filepath: str,
                 entity_id_mapping: str,
                 relation_emb: str,
                 relation_id_mapping: str,
                 recomendation_rules_filepath: str
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

        self.recommendation_rules_dict = json.load(open(recomendation_rules_filepath, 'r'))

    def check_if_entity_in_kg(self, wk_ent_id: str) -> bool:
        return str(self.namespaces.WD[wk_ent_id]) in self.entity_labels_dict.keys()

    def check_if_property_in_kg(self, wk_prop_id: str) -> bool:
        return str(self.namespaces.WDT[wk_prop_id]) in self.property_labels_dict.keys()

    def check_in_entity_movie_or_person(self, wk_ent_id: str) -> bool:
        relevant_instace_of_ents = ('Q11424', 'Q5', 'Q24862', 'Q506240', 'Q336144',
                                    'Q20650540', 'Q759853', 'Q110900120', 'Q29168811', 'Q17517379')
        return any([(self.namespaces.WD[wk_ent_id], self.namespaces.WDT.P31, self.namespaces.WD[obj]) in self.kg
                    for obj in relevant_instace_of_ents])

    def get_object_or_objects(self, wk_ent_id: str, wk_prop_id: str) -> list:
        return [obj for obj in self.kg.objects(self.namespaces.WD.wk_ent_id, self.namespaces.WDT.wk_prop_id)]

    def get_imdb_id(self, wk_ent_id: str) -> Optional[str]:
        if self.check_if_entity_in_kg(wk_ent_id):
            query_result = self.kg.query(wikidata_queries.imdb_query, initBindings={"id": self.namespaces.WD[wk_ent_id]})
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
        query = None
        query_result = []
        entity_string_to_match = entity_string_to_match.lower()

        # First try exact lower case match with SPARQL
        if ent_type is None:
            query = wikidata_queries.exact_lowercase_label_match

        elif ent_type == 'person':
            query = wikidata_queries.person_exact_lowercase_label_match

        elif ent_type == 'person or movie':
            query = wikidata_queries.person_or_film_lowercase_label_match_V2

        query_result = self.kg.query(query.format(entity_string_to_match))

        # If search failed, i.e: no items in the queries result, try cleaning the string
        if len([str(wk_ent_id) for wk_ent_id, _ in query_result]) == 0:
            entity_string_to_match = entity_string_to_match.strip('?')
            query_result = self.kg.query(
                query.format(entity_string_to_match))

        detected_wk_entities = [str(wk_ent_id) for wk_ent_id, _ in query_result]

        if len(detected_wk_entities) == 1:
            wk_ent_id = os.path.basename(detected_wk_entities[0])

        else:
            # Try matching the entity based on the edit distance
            matches = np.array(
                [(os.path.basename(wk_id), fuzz.token_sort_ratio(entity_string_to_match, label))
                 for wk_id, label in self.entity_labels_dict.items()
                 if fuzz.token_sort_ratio(entity_string_to_match, label) > 75]
            )

            if matches.shape[0] > 0:
                wk_ent_id = matches[matches[:, 1].astype(float).argmax(), 0]

        return wk_ent_id

    def get_wkdata_propid_based_on_label_match(self, property_str: str) -> Optional[str]:
        # Try matching the entity based on the edit distance
        matches = np.array(
            [(wk_id, max([fuzz.token_sort_ratio(property_str, label) for label in label_list]))
             for wk_id, label_list in self._property_extended_label_set.items()
             if any([fuzz.token_sort_ratio(property_str, label) > 75 for label in label_list])
             ]
        )

        if len(matches) > 0:
            return matches[matches[:, 1].astype(float).argmax(), 0]
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
            top_k: int = 10, ptg_max_diff_top_k: float = 0.2, report_max: int = 4) -> Optional[Tuple[str, ...]]:

        wk_ent_ids = self.kg_embeddings.deduce_object(wk_ent_id, wk_prop_id, top_k, ptg_max_diff_top_k, report_max)

        if wk_ent_ids:
            return tuple([self.get_entity_label(wk_ent_id) for wk_ent_id in wk_ent_ids])
        else:
            return None

    def recommend_similar_movies_and_characateristics(
            self, wk_ent_id_list: list,
            top_k: int = 10,
            num_criteria_to_report: int = 3,
            num_movies_to_report: int = 4,
    ) -> Tuple[dict, list]:

        # Get the list of the closest_movies
        closest_ents = self.kg_embeddings.get_most_similar_entities_to_centroid(wk_ent_id_list, top_k)

        # Check for common property values accross all the closest movies
        one_hop_recs = self._evaluate_recomendation_rule(
            closest_ents,
            rec_rules=self.recommendation_rules_dict['one-hop'],
            query=wikidata_queries.one_hop_prop_count,
            top_k=top_k
        )

        two_hop_recs = self._evaluate_recomendation_rule(
            closest_ents,
            rec_rules=self.recommendation_rules_dict['two-hop'],
            query=wikidata_queries.two_hop_prop_count,
            top_k=top_k
        )

        # Remove criteria that might be redundant
        if 'instance of' in one_hop_recs.keys() and 'genre' in one_hop_recs.keys():
            del one_hop_recs['instance of']

        if 'director' in one_hop_recs.keys() and 'screenwriter' in one_hop_recs.keys():
            del one_hop_recs['screenwriter']

        if 'based on' in one_hop_recs.keys() and 'inspired by' in one_hop_recs.keys():
            del one_hop_recs['inspired by']

        if 'country of origin' in one_hop_recs.keys() and 'narrative location' in one_hop_recs.keys():
            del one_hop_recs['country of origin']

        if 'based on' in one_hop_recs.keys() and 'based on' in two_hop_recs.keys():
            del two_hop_recs['based on']

        if 'inspired by' in one_hop_recs.keys() and 'inspired by' in two_hop_recs.keys():
            del two_hop_recs['inspired by']

        recs = one_hop_recs | two_hop_recs

        # Pick num_criteria elements to report to the user
        if len(recs.keys()) > num_criteria_to_report:
            criteria_to_use = random.sample(list(recs.keys()), num_criteria_to_report)
            recs = {k: v for k, v in recs.items() if k in criteria_to_use}

        # Pick movies to recommend
        # First remove duplicate names
        closest_movies_str_set = set([self.entity_labels_dict[str(self.namespaces.WD[closest_ent])]
                                      for closest_ent in closest_ents])

        # Then remove names that overlap with names of the input
        ref_movie_str = set([(self.entity_labels_dict[str(self.namespaces.WD[wk_ent_id])]).lower()
                             for wk_ent_id in wk_ent_id_list])
        closest_movies_str_list = [closest_movie for closest_movie in closest_movies_str_set if closest_movie.lower() not in ref_movie_str]
        closest_movies_str_list = closest_movies_str_list[0: min(num_movies_to_report, len(closest_movies_str_list))]

        return recs, closest_movies_str_list

    def _evaluate_recomendation_rule(self, closest_ents, rec_rules: dict, query: str, top_k: int):
        criteria_to_recommend = {}
        for wk_prop_id, rule_params in rec_rules.items():
            common_prop = self.kg.query(
                query.format(
                    property_id=wk_prop_id,
                    wk_ent_list=', '.join([f'wd:{wk_ent_id}' for wk_ent_id in closest_ents]))
            )

            # Only add to the list entities of each property that are over the threshold
            #   and exclude labels in rule_params['exclude']
            tuples_meet_rule = [str(triple[1]) for triple in common_prop
                                if int(triple[2]) / top_k > rule_params['threshold'] and
                                str(triple[1]) not in rule_params['exclude']]

            if len(tuples_meet_rule) > 0:
                criteria_to_recommend[rule_params['label']] = tuples_meet_rule

        return criteria_to_recommend


if __name__ == '__main__':
    kg = WikiDataKG(
        kg_tuple_file_path='../setup_data/wikidata_kg/14_graph.nt',
        imdb2movienet_filepath='../setup_data/wikidata_kg/id_mappings/imdb2movienet.json',
        entity_label_filepath='../setup_data/wikidata_kg/id_labels/wkdata_entity_labels_dict.json',
        property_label_filepath='../setup_data/wikidata_kg/id_labels/wkdata_property_labels_dict.json',
        property_extended_label_filepath='../setup_data/wikidata_kg/id_labels/wk_data_names_props_of_interest.json',
        entity_emb_filepath='../setup_data/wikidata_kg/embeddings/entity_embeds.npy',
        entity_id_mapping='../setup_data/wikidata_kg/embeddings/entity_ids.del',
        relation_emb='../setup_data/wikidata_kg/embeddings/relation_embeds.npy',
        relation_id_mapping='../setup_data/wikidata_kg/embeddings/relation_ids.del',
        recomendation_rules_filepath='../setup_data/wikidata_kg/recommendation/rec_rules.json'
    )

    assert kg.get_imdb_id(wk_ent_id='Q40523') == 'nm0000210'
    assert 'nm0000770' in kg.imdb2movienet
    assert kg.imdb2movienet['nm0000770']

    assert kg.get_wkdata_entid_based_on_label_match('Martin Scorsese') == 'Q41148'
    print(kg.recommend_similar_movies_and_characateristics(['Q179673', 'Q36479', 'Q218894']))
    assert kg.get_wkdata_entid_based_on_label_match('Martin Scorsese', ent_type='person') == 'Q41148'
    assert kg.get_wkdata_entid_based_on_label_match('Martin Scorssese') == 'Q41148'




