import re
from typing import Tuple, Optional

from regex_matchers.BasicRegexMatcher import BasicRegexMatcher, basic_tokenizing_and_cleaning

fact_q_regex = (
    (r'(?i)((recommend)\s)?((movies|films|a movie|things)\s)?((similar to|like|liked|such as)\s)(.*)?', 7),
)

fact_q_regex_test_sentences = (
    "Recommend movies similar to Hamlet and Othello",
    "Given that I like The Lion King, Pocahontas, and Beauty and the Beast, can you recommend some movies?",
    "Recommend movies like the matrix, blade runner, and children of men ",
    "Could you recommend a movie like Nigthmare on Elm Street and Friday the 13th?",
    "Could you recommend films like Nigthmare on Elm Street and Friday the 13th?",
    "Could you recommend something like Nigthmare on Elm Street and Friday the 13th?",
    "I want a recommendation for films like coco, soul, and up",
    "Could you offer a recommendation for movies simila to toy story?",
    "Could you give me a recommendation of movies like the expendables and terminator 2?",
    "I want to see things like Avengers and Justice League, what movies would you recommend?",
    "I really liked V for Vendetta and Children of men, could you recommend something similar?",
    "The godfather and good fellas rock. Do you know of similar movies?",
    "Are you aware of movies similar to Thor Ragnarok and Guardians of the Galaxy?"
)


class RecQRegexMatcher(BasicRegexMatcher):
    def __init__(self, regex_patterns: Tuple[Tuple[str, int], ...] = fact_q_regex):
        super(RecQRegexMatcher, self).__init__(regex_patterns)

    def match_string(self, document: str) -> Optional[list]:
        for pattern, group_to_extract_movie_list in self.regex_patterns:
            if match := re.search(pattern, document, re.IGNORECASE):
                # Break up the list into groups
                movie_list = match.group(group_to_extract_movie_list).split(',')
                last_two_movies = movie_list.pop(-1).split('and ')
                if len(last_two_movies) > 1:
                    last_movie = last_two_movies[-1]
                    before_last_movie = 'and '.join(last_two_movies[:-1])
                    movie_list += [before_last_movie, last_movie]
                else:
                    movie_list += [last_two_movies[0]]

                movie_list = [movie for movie in movie_list if movie.strip() != '' and movie is not None]

                if len(movie_list) > 0:
                    return movie_list

        return None


if __name__ == '__main__':
    print("Test media questions regex patterns")
    media_q_regex_matcher = RecQRegexMatcher()
    media_q_regex_matcher.test(fact_q_regex_test_sentences)

