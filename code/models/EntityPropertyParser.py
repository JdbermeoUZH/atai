import json
from typing import Tuple

import spacy
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
    def __init__(self, property_extended_label_filepath: str, model_type: str = 'trf'):
        self.nlp = spacy.load(spacy_model_types[model_type])
        # Add entity linker models
        self.nlp.add_pipe('entityLinker')
        self.nlp.add_pipe('entityfishing')
        self.prop_matcher = self._create_property_phrase_matcher(property_extended_label_filepath)

    def __call__(self, doc: str):
        return self.nlp(doc)

    def _create_property_phrase_matcher(self, property_extended_label_filepath: str):
        prop_labels_dict = json.load(open(property_extended_label_filepath, 'r'))
        prop_matcher = PhraseMatcher(self.nlp.vocab)

        # Add a pattern for each property id of interest in our KG
        for prop_id, possible_labels_list in prop_labels_dict.items():
            prop_matcher.add(prop_id, [self.nlp.make_doc(text) for text in possible_labels_list])

        return prop_matcher

    def return_wikidata_entities(
            self,
            doc: str,
            entities_of_interest: Tuple[str, ...] = None):

        proc_doc = self.nlp(doc)
        wkdata_ents_1 = _get_wikidata_entities_from_entity_linker(proc_doc)
        wkdata_ents_2 = _get_wikidata_entities_from_entity_fishing(proc_doc)

        wkdata_ents = merge_dicts(wkdata_ents_1, wkdata_ents_2)

        if entities_of_interest:
            return proc_doc, [ent for ent in proc_doc.ents if ent.label_ in entities_of_interest], \
                   {k: v for k, v in wkdata_ents.items() if v['ner_type'] in entities_of_interest}
        else:
            return proc_doc, [ent for ent in proc_doc.ents], wkdata_ents

    def return_wikidata_properties(self, doc: str) -> list:
        return [self.nlp.vocab.strings[match_id] for match_id, _, _ in self.prop_matcher(self.nlp(doc))]


if __name__ == "__main__":
    entityPaser = EntityPropertyParser(
        property_extended_label_filepath='../../setup_data/wikidata_kg/wk_data_names_props_of_interest.json', model_type='trf')
    doc, ents, wkdata_ents = entityPaser.return_wikidata_entities("I want to see a picture of Julia Roberts nd Keanu Reaves in the city of Pitalito and Bordones")
    print(ents)
    print(wkdata_ents)

    doc, ents, wkdata_ents = entityPaser.return_wikidata_entities(
        "I want to see a picture of Julia Roberts nd Keanu Reaves in the city of Pitalito and Bordones",
        entities_of_interest=('PERSON',))

    print(ents)
    print(wkdata_ents)

    doc, ents, wkdata_ents = entityPaser.return_wikidata_entities("I want to see a poster of the movie The Post and a picture of Julia Roberts",
                                                                  entities_of_interest=('PERSON', 'WORK_OF_ART'))
    print(ents)
    print(wkdata_ents)

    doc, ents, wkdata_ents = entityPaser.return_wikidata_entities(
        "I want to see a picture of Michael Jordan",
        entities_of_interest=('PERSON', 'WORK_OF_ART'))
    print(ents)
    print(wkdata_ents)

    doc, ents, wkdata_ents = entityPaser.return_wikidata_entities(
        "I I I I dont know, ",
        entities_of_interest=('PERSON', 'WORK_OF_ART'))
    print(ents)
    print(wkdata_ents)

    doc, ents, wkdata_ents = entityPaser.return_wikidata_entities(
        "Show me a picture of Harry Potter and the Philosopher's Stone",
        entities_of_interest=('PERSON', 'WORK_OF_ART'))
    print(ents)
    print(wkdata_ents)

    doc, ents, wkdata_ents = entityPaser.return_wikidata_entities(
        "Show me a the poster of Pirates of the caribbean",
        entities_of_interest=('PERSON', 'WORK_OF_ART'))
    print(ents)
    print(wkdata_ents)

    doc, ents, wkdata_ents = entityPaser.return_wikidata_entities(
        "Who is the lead actor of Pirates of the caribbean",
        entities_of_interest=('PERSON', 'WORK_OF_ART'))
    print(ents)
    print(wkdata_ents)
    print(len(wkdata_ents))

    # Test property matching with phrase matcher
    prop_label_dict = json.load(open('../../setup_data/wikidata_kg/wk_data_names_props_of_interest.json', 'r'))

    input_str = "Who is the director of the matrix"
    entity_detected = entityPaser.return_wikidata_properties(input_str)
    print(input_str, entity_detected, prop_label_dict[entity_detected[0]])

    input_str = "Who is the lead actor of Pirates of the caribbean"
    entity_detected = entityPaser.return_wikidata_properties(input_str)
    print(input_str, entity_detected, prop_label_dict[entity_detected[0]])

    input_str = "Who was the mom of Charlie in Two and a half Men"
    entity_detected = entityPaser.return_wikidata_properties(input_str)
    print(input_str, entity_detected)

