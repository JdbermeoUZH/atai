import os
import json

import numpy as np
import spacy
import classy_classification

from utils.silencer import silent


def create_few_shot_classifier(train_data: dict):
    nlp = spacy.blank("en")
    nlp.add_pipe(
        "text_categorizer",
        config={
            "data": train_data,
            "model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            "device": "gpu",
            "cat_type": "multi-label"
        }
    )

    return nlp


class InteractionTypeClassifier:
    @silent
    def __init__(self, train_examples_path: str):
        with open(train_examples_path, 'r') as fp:
            train_data = json.load(fp)

        self.classifier = create_few_shot_classifier(train_data=train_data)
        self.classes = list(self.classifier(" ")._.cats.keys())

    @silent
    def __call__(self, doc: str):
        return self.classes[np.array(list(self.classifier(doc)._.cats.values())).argmax()]


if __name__ == '__main__':
    input_cls = InteractionTypeClassifier(
        os.path.join('../..', 'setup_data', 'first_filter_train_examples.json')
    )

    # Verify behaviour on relatively difficult examples
    should_be_conversation = input_cls("Hey man, what's up")
    assert should_be_conversation == 'Conversation'

    should_be_fact_emb_crowd = input_cls("I bet you have absolutely no idea who voices Tanjirou in Kimetsu no Yaiba")
    assert should_be_fact_emb_crowd == 'Factual Question/Embedding/Crowdsourcing'

    should_be_conversation = input_cls("hey would you be so kind to display a picture of Ali G")
    assert should_be_conversation == 'Media Question'

    should_be_recommendation = input_cls(
        "Hey, i am interested in a movie that is as good as The Goonies and Toy Story")
    assert should_be_recommendation == 'Recommendation Questions'


