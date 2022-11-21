from typing import Tuple

import spacy
from spacy.tokens import Doc

from utils.utils import merge_dicts

spacy_model_types = {'sm': 'en_core_web_sm',  'md': 'en_core_web_md', 'lg': 'en_core_web_lg', 'trf': 'en_core_web_trf'}


class EntityParser:
    """
    Use spacy models to identifies named entities and attempt to link tokens to entities in wikidata
    """
    def __init__(self, model_type='trf'):
        self.nlp = spacy.load(spacy_model_types[model_type])
        # Add entity linker models
        self.nlp.add_pipe('entityLinker')
        self.nlp.add_pipe('entityfishing')

    def __call__(self, doc: str):
        return self.nlp(doc)

    def _get_wikidata_entities_from_entity_fishing(self, preprocessed_doc: Doc) -> dict:
        return {
            ent._.kb_qid: {'url': ent._.url_wikidata, 'score': ent._.nerd_score, 'text': ent.text,
                           'ner_type': ent.label_}
            for ent in preprocessed_doc.ents if ent._.kb_qid is not None
        }

    def _get_wikidata_entities_from_entity_linker(self, preprocessed_doc: Doc) -> dict:
        return {
            f'Q{lk_ent.get_id()}': ({'url': lk_ent.get_url(), 'text': lk_ent.span.text,
                                    'description': lk_ent.get_description(), 'ner_type': "NA"}
                                    if len(lk_ent.span.ents) == 0 else
                                    {'url': lk_ent.get_url(), 'text': lk_ent.span.text,
                                    'description': lk_ent.get_description(), 'ner_type': lk_ent.span.ents[0].label_}
                                    )
            for lk_ent in preprocessed_doc._.linkedEntities
        }

    def return_wikidata_entities(
            self,
            doc: str,
            entities_of_interest: Tuple[str, ...] = None):

        proc_doc = self.nlp(doc)
        wkdata_ents_1 = self._get_wikidata_entities_from_entity_linker(proc_doc)
        wkdata_ents_2 = self._get_wikidata_entities_from_entity_fishing(proc_doc)

        wkdata_ents = merge_dicts(wkdata_ents_1, wkdata_ents_2)

        if entities_of_interest:
            return proc_doc, [ent for ent in proc_doc.ents if ent.label_ in entities_of_interest], \
                   {k: v for k, v in wkdata_ents.items() if v['ner_type'] in entities_of_interest}
        else:
            return proc_doc, [ent for ent in proc_doc.ents], wkdata_ents


if __name__ == "__main__":
    entityPaser = EntityParser(model_type='trf')

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
