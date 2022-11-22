from typing import Tuple

from regex_matchers.BasicRegexMatcher import BasicRegexMatcher

media_q_regex = (
    (r'(?i)(((show|see|observe|watch|want|wondering)\s?(me|us|to)?\s?)+(a picture|an image|a portrait)?\s?(of|what)?)\s?(the\s)?(great|unique|incredible|outstanding)?\s?((perfomer|actor|actress|director|cast member)\s)?(.*)(looks\s?(like)?)', 11),
    (r'(?i)(((show|see|observe|watch|want|wondering)\s?(me|us|to)?\s?)+(a picture|an image|a portrait)?\s?(of|what)?)\s?(the\s)?(great|unique|incredible|outstanding)?\s?((perfomer|actor|actress|director|cast member)\s)?(.*)', 11),
    (r'(?i)((what|how) (.*) looks)', 3)
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
    'show me robert deniro',
    'Hey, do you know what Xzibit looks like?'
)


class MediaQRegexMatcher(BasicRegexMatcher):
    def __init__(self, regex_patterns: Tuple[Tuple[str, int], ...] = media_q_regex):
        super(MediaQRegexMatcher, self).__init__(regex_patterns)


if __name__ == '__main__':
    print("Test media questions regex patterns")
    media_q_regex_matcher = MediaQRegexMatcher()
    media_q_regex_matcher.test(media_q_regex_test_sentences)

