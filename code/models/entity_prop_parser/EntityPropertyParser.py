import json
import os
from typing import Tuple

import spacy
import numpy as np
from spacy.matcher import PhraseMatcher
from spacy.tokens import Doc

from utils.utils import merge_dicts

spacy_model_types = {'sm': 'en_core_web_sm',  'md': 'en_core_web_md', 'lg': 'en_core_web_lg', 'trf': 'en_core_web_trf'}


def _get_wikidata_entities_from_entity_fishing(preprocessed_doc: Doc) -> dict:
    return {
        ent._.kb_qid: {'url': ent._.url_wikidata, 'score': ent._.nerd_score, 'text': ent.text,
                       'ner_type': ent.label_}
        for ent in preprocessed_doc.ents if ent._.kb_qid is not None
    }


def _get_wikidata_entities_from_entity_linker(preprocessed_doc: Doc) -> dict:
    return {
        f'Q{lk_ent.get_id()}': ({'url': lk_ent.get_url(), 'text': lk_ent.span.text,
                                'description': lk_ent.get_description(), 'ner_type': "NA"}
                                if len(lk_ent.span.ents) == 0 else
                                {'url': lk_ent.get_url(), 'text': lk_ent.span.text,
                                'description': lk_ent.get_description(), 'ner_type': lk_ent.span.ents[0].label_}
                                )
        for lk_ent in preprocessed_doc._.linkedEntities
    }


class EntityPropertyParser:
    """
    Use spacy models to identifies named entities and attempt to link tokens to entities in wikidata
    """
    def __init__(self,
                 entity_exact_label_filepath: str,
                 property_extended_label_filepath: str,
                 model_type: str = 'trf'):
        self.nlp = spacy.load(spacy_model_types[model_type])
        # Add entity linker models
        self.nlp.add_pipe('entityLinker')
        self.nlp.add_pipe('entityfishing')
        self.ent_matcher = self._create_property_or_ent_phrase_matcher(entity_exact_label_filepath)
        self.prop_matcher = self._create_property_or_ent_phrase_matcher(property_extended_label_filepath)

    def __call__(self, doc: str):
        return self.nlp(doc)

    def _create_property_or_ent_phrase_matcher(self, property_or_ent_label_filepath: str):
        labels_dict = json.load(open(property_or_ent_label_filepath, 'r'))
        matcher = PhraseMatcher(self.nlp.vocab)

        # Add a pattern for each property id of interest in our KG
        for wk_data_id, possible_labels in labels_dict.items():
            if isinstance(possible_labels, list):
                matcher.add(wk_data_id, [self.nlp.make_doc(text) for text in possible_labels])
            elif isinstance(possible_labels, str):
                matcher.add(wk_data_id, [self.nlp.make_doc(possible_labels)])

        return matcher

    def return_wikidata_entities_w_entity_linkers(
            self,
            doc: str,
            entities_of_interest: Tuple[str, ...] = None,
            entity_filter: callable = None
    ):

        proc_doc = self.nlp(doc)

        # Exact string match in the sentence
        wkdata_ents_v1 = [(self.nlp.vocab.strings[match_id], proc_doc[start: end].text)
                          for match_id, start, end in self.ent_matcher(proc_doc)]

        # Extract using the pretrained entity linkers
        wkdata_ents_1 = _get_wikidata_entities_from_entity_linker(proc_doc)
        wkdata_ents_2 = _get_wikidata_entities_from_entity_fishing(proc_doc)


        wkdata_ents_v2_dict = merge_dicts(wkdata_ents_1, wkdata_ents_2)
        spacy_ents = [ent for ent in proc_doc.ents]

        if entities_of_interest:
            spacy_ents = [ent for ent in spacy_ents if ent.label_ in entities_of_interest]
            wkdata_ents_v2_dict = {k: v for k, v in wkdata_ents_v2_dict.items()
                                   if v['ner_type'] in entities_of_interest}

        wkdata_ents_v2 = [(k, v['text']) for k, v in wkdata_ents_v2_dict.items()]

        # Merge both entity candidates
        wkdata_ents = wkdata_ents_v1 + wkdata_ents_v2

        # Filter entities based on a given filter (i.e: they refer to movies, people, etc.)
        if entity_filter:
            wkdata_ents = [(wkdata_ent_id, wkdata_ent_label) for wkdata_ent_id, wkdata_ent_label in wkdata_ents
                           if entity_filter(wkdata_ent_id)]

        # Remove entities whose text is contained in the others
        wkdata_ents = [
            (wkdata_ent_id, wkdata_ent_text) for wkdata_ent_id, wkdata_ent_text in wkdata_ents
            if not any(
                [wkdata_ent_text in wkdata_ent_text_ for _, wkdata_ent_text_ in wkdata_ents if
                 wkdata_ent_text_ != wkdata_ent_text]
            )
        ]

        # Remove duplicate entity ids
        wkdata_ents = list(set([wkdata_ent_id for wkdata_ent_id, _ in wkdata_ents]))

        return spacy_ents, wkdata_ents

    def return_wikidata_properties(self, doc: str) -> list:
        return [self.nlp.vocab.strings[match_id] for match_id, _, _ in self.prop_matcher(self.nlp(doc))]

    def return_wikidata_entities_exact_match(self, doc: str) -> list:
        return [self.nlp.vocab.strings[match_id] for match_id, _, _ in self.ent_matcher(self.nlp(doc))]


if __name__ == "__main__":
    entityPaser = EntityPropertyParser(
        entity_exact_label_filepath='./entity_prop_parser/wk_data_names_ents_of_interest.json',
        property_extended_label_filepath='./entity_prop_parser/wk_data_names_props_of_interest_2.json',
        model_type='trf')

    prompt_list = [
        ("What is the box office of Princess and the Frog??", None),
        ("I want to see a picture of Julia Roberts nd Keanu Reaves in the city of Pitalito and Bordones", None),
        ("I want to see a picture of Julia Roberts nd Keanu Reaves in the city of Pitalito and Bordones", ('PERSON',)),
        ("I want to see a poster of the movie The Post and a picture of Julia Roberts", ('PERSON', 'WORK_OF_ART')),
        ("I want to see a picture of Michael Jordan", ('PERSON', 'WORK_OF_ART')),
        ("I I I I dont know, ", ('PERSON', 'WORK_OF_ART')),
        ("Show me a picture of Harry Potter and the Philosopher's Stone", ('PERSON', 'WORK_OF_ART')),
        ("Who is the lead actor of Pirates of the caribbean", ('PERSON', 'WORK_OF_ART')),
        ("Who is the lead actor of Pirates of the caribbean", None),
        ("Who is the director of the matrix", ('PERSON', 'WORK_OF_ART')),
        ("Who was the mom of Charlie in Two and a half Men", None),
        ]

    for prompt_text, entities_of_interst in prompt_list:
        ents, wkdata_ents_ = entityPaser.return_wikidata_entities_w_entity_linkers(
            prompt_text, entities_of_interest=entities_of_interst)
        print(f'prompt_text: {prompt_text}')
        print(f'spacy ents: {ents}')
        print(f'wkdata_ents: {wkdata_ents_}')

