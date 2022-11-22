"""
Queries when we have the wikidata id
####################################
"""
imdb_query = """
prefix wdt: <http://www.wikidata.org/prop/direct/>
prefix wd: <http://www.wikidata.org/entity/>
SELECT DISTINCT ?imdb WHERE {
    ?id wdt:P345 ?imdb .
}
LIMIT 10
"""

"""
Match entities by label
#######################
"""
exact_lowercase_label_match = """
prefix wdt: <http://www.wikidata.org/prop/direct/>
prefix wd: <http://www.wikidata.org/entity/>
SELECT ?item ?label 
WHERE {{
        ?item rdfs:label ?label .
        FILTER (LCASE(STR(?label)) = '{}')
        FILTER(LANG(?label) = "en").
}}
LIMIT 1
"""

contains_lowercase_label_match = """
prefix wdt: <http://www.wikidata.org/prop/direct/>
prefix wd: <http://www.wikidata.org/entity/>
SELECT ?item ?label 
WHERE {{
        ?item rdfs:label ?label .
        FILTER (CONTAINS(LCASE(STR(?label)), '{}'))
        FILTER(LANG(?label) = "en").
}}
LIMIT 1
"""

person_exact_lowercase_label_match = """
prefix wdt: <http://www.wikidata.org/prop/direct/>
prefix wd: <http://www.wikidata.org/entity/>
SELECT ?item ?label 
WHERE {{
        ?item rdfs:label ?label .
        ?item wdt:P31 wd:Q5 .
        FILTER (LCASE(STR(?label)) = '{}')
        FILTER(LANG(?label) = "en").
}}
LIMIT 1
"""

person_contains_lowercase_label_match = """
prefix wdt: <http://www.wikidata.org/prop/direct/>
prefix wd: <http://www.wikidata.org/entity/>
SELECT ?item ?label 
WHERE {{
        ?item rdfs:label ?label .
        ?item wdt:P31 wd:Q5 .
        FILTER (CONTAINS(LCASE(STR(?label)), '{}'))
        FILTER(LANG(?label) = "en").
}}
LIMIT 1
"""


"""
Match properties by label
#########################
"""


property_exact_lowercase_label_match = """
prefix wdt: <http://www.wikidata.org/prop/direct/>
prefix wd: <http://www.wikidata.org/entity/>
SELECT ?item ?label 
WHERE {{
        ?item rdfs:label ?label .
        ?item wdt:P31 wd:Q5 . 
        FILTER (LCASE(STR(?label)) = '{}')
        FILTER(LANG(?label) = "en").
}}
LIMIT 1
"""

property_contains_lowercase_label_match = """
prefix wdt: <http://www.wikidata.org/prop/direct/>
prefix wd: <http://www.wikidata.org/entity/>
SELECT ?item ?label 
WHERE {{
        ?item rdfs:label ?label .
        ?item wdt:P31 wd:Q5 . 
        FILTER (CONTAINS(LCASE(STR(?label)), '{}'))
        FILTER(LANG(?label) = "en").
}}
LIMIT 1
"""
