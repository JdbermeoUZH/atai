import re
from typing import Tuple, Optional

from regex_matchers.BasicRegexMatcher import BasicRegexMatcher, basic_tokenizing_and_cleaning

fact_q_regex = (
    (r'(?i)(((in|on)\s?)?((who|what|which|where)\s?)?((is|was|which)\s?)?((the)\s?)?(.*)(\s(of|in)\s)(.*))', 10, 13),
    (r'(?i)(((who|what|which|where)\s)((is|was)\s)?)(\S+)(.*)', 6, 7)
)

fact_q_regex_test_sentences = (
    "Who is the director of The Matrix",
    "Who directed the godfather",
    "Do you know who directed Minions?",
    "I bet you don't know who directed triangle of sadness",
    "Who was it that worked as the director of her?",
    "Who was it that worked as director of twelve years as a slave?",
    "I was wondering, who was in charge of directing breaking bad",
    "Sopranos was directed by whom?",
    "Wathcmen was such a great film, who directed it?",
    "I loved rise of gru, by any chance, do you know who directed it?",
    "I loved rise of gru, by any chance, do you know who is the director?",
    "Soul is my favorite movie, who was the director again?",
    "What is the original language of embrace of the serpent?",
    "embrace of the serpent is such a trippy film, what was the original language?",
    "Was embrace of the serpent originally in spanish?",
    "what is the language of the wave?",
    "what is the original language of the wave?",
    "In what language do they speak originally in the wave?",
    "In what language do they speak in the matrix originally?",
    "In what language do they originally speak in drive my car?",
    "What is the language of the original version of la historia oficial ",
    "Who is the director of photography of The Matrix",
    "Who is the screenwriter of fire of love",
    "who is the editor of fire of love",
    "who was the edit of moonlight???",
    "who was the film editor of moonlight?",
    "who edited nosferatu",
    "where is el secreto de sus ojos from?",
    "where was druk filmed?",
    "what is country of origin of Druk?",
    "who is the excutive producer of Law and Order?",
    "who produced the expendables?",
    "which company produced the lord of the rings?",
    "what is the production company of Mortal Kombat?",
    "Which actor plays the voice of Gru in despicable me?",
    "In what book is the godfather based on?",
    "On what is les miserables based on?",
    "What inspired V for Vendetta?",
    "What is the matrix about?",
    "What is the main topic of game of thrones?",
    "do you know what is breaking bad about??",
    "Could you tell me the main topic of the wire?",
    "When does Joan of Arc take place?",
    "in what epoch is gladiator?",
    "In which year is the story of spartacus set? ",
    "What is the time period of the tudors?",
    "Is la sombra del caminante in balck and white?",
    "I cant really remember, is la sombra del caminante a colored film?",
    "What is the aspect ratio of saving privte ryan?",
    "What is the series of old boy?",
    "Is the hobbit part of the lord of the rings trilogy?",
    "What is the defining characteristic of the life of pi?",
    "Who designed the customs of starwars?",
    "who is the costume designer of LOTR?",
    "Who is the production designer of LOTR"
)


class FactQRegexMatcher(BasicRegexMatcher):
    def __init__(self, regex_patterns: Tuple[Tuple[str, int], ...] = fact_q_regex):
        super(FactQRegexMatcher, self).__init__(regex_patterns)

    def match_string(self, document: str) -> Optional[Tuple[str, str]]:
        for pattern, group_to_extract_property, group_to_extract_entity in self.regex_patterns:
            if match := re.search(pattern, document, re.IGNORECASE):
                matched_property = basic_tokenizing_and_cleaning(match.group(group_to_extract_property))
                matched_entity = basic_tokenizing_and_cleaning(match.group(group_to_extract_entity))

                if matched_entity and matched_property:
                    if matched_entity.strip() != '' and matched_property.strip() != '':
                        return matched_entity, matched_property

        return None, None


if __name__ == '__main__':
    print("Test media questions regex patterns")
    media_q_regex_matcher = FactQRegexMatcher()
    media_q_regex_matcher.test(fact_q_regex_test_sentences)

