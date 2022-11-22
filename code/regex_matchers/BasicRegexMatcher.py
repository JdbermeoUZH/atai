import re
from typing import Tuple, Optional

import spacy


nlp = spacy.load('en_core_web_sm')


def basic_tokenizing_and_cleaning(text: str) -> str:
    """
    Lemmatize, remove punctutation, and stopwords of a string
    :return:
    """
    return ' '.join([token.lemma_ for token in nlp(text) if not token.is_punct and not token.is_stop])


class BasicRegexMatcher:
    def __init__(self, regex_patterns: Tuple[Tuple[str, int], ...]):
        self.regex_patterns = regex_patterns

    def match_string(self, document: str) -> Optional[str]:
        for pattern, group_to_extract in self.regex_patterns:
            if match := re.search(pattern, document, re.IGNORECASE):
                return basic_tokenizing_and_cleaning(match.group(group_to_extract))

        return None

    def test(self, documents: Tuple[str, ...]):
        for document in documents:
            matched_string = self.match_string(document)
            print(document, matched_string)
            assert matched_string != ''
