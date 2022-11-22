from typing import Tuple

from regex_matchers.BasicRegexMatcher import BasicRegexMatcher

media_q_regex = (
    r'(?i)(((show|see|observe|watch|want|wondering)\s?(me|us|to)?\s?)+(a picture|an image|a portrait)?\s?(of|what)?)\s?(the\s)?(great|unique|incredible|outstanding)?\s?((perfomer|actor|actress|director|cast member)\s)?(.*)(looks\s?(like)?)',
    r'(?i)(((show|see|observe|watch|want|wondering)\s?(me|us|to)?\s?)+(a picture|an image|a portrait)?\s?(of|what)?)\s?(the\s)?(great|unique|incredible|outstanding)?\s?((perfomer|actor|actress|director|cast member)\s)?(.*)'
)

media_q_regex_test_sentences = (
    'Show me Leonardo fucking DiCaprio',
    'I want to see a picture of the actor Leonardo fUcking Dicaprio',
    'Please, would you be so kind as to please show what the one and only, unique, Julia Roberts looks like',
    'kjkl  show me a picture of Mrtin Scorssese',
    'I want a picture of Leo Dicpario',
    'I was wondering what leo decaprio looks like',
    'I want to see what Julia roberts looks like',
    'please, I want to see a picture of the Julia Roberts',
    'I want to see an image of Julia roberts',
    'please, I want to see a portrait of the outstanding actress Julia Roberts',
    'show me robert deniro'
)


class MediaQRegexMatcher(BasicRegexMatcher):
    def __init__(self, regex_patterns: Tuple[str, ...] = media_q_regex, group_to_extract: int = 11):
        super(MediaQRegexMatcher, self).__init__(regex_patterns, group_to_extract)


if __name__ == '__main__':
    print("Test media questions regex patterns")
    media_q_regex_matcher = MediaQRegexMatcher()
    media_q_regex_matcher.test(media_q_regex_test_sentences)

