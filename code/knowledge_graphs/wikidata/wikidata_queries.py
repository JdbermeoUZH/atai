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

label_query = """
prefix wdt: <http://www.wikidata.org/prop/direct/>
prefix wd: <http://www.wikidata.org/entity/>
SELECT DISTINCT ?label WHERE {
    ?id rdfs:label ?label .
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

person_or_film_lowercase_label_match = """
prefix wdt: <http://www.wikidata.org/prop/direct/>
prefix wd: <http://www.wikidata.org/entity/>
SELECT DISTINCT ?item ?label 
WHERE {{
        ?item rdfs:label ?label .
        {{ ?item wdt:P31 wd:Q11424}}
        UNION
        {{ ?item wdt:P31 wd:Q5}}
        UNION
        {{ ?item wdt:P31 wd:Q24862}}
        UNION
        {{ ?item wdt:P31 wd:Q506240}}
        UNION
        {{ ?item wdt:P31 wd:Q336144}}
        UNION
        {{ ?item wdt:P31 wd:Q20650540}}
        UNION
        {{ ?item wdt:P31 wd:Q759853}}
        UNION
        {{ ?item wdt:P31 wd:Q110900120}}
        UNION
        {{ ?item wdt:P279 wd:Q11424}}
        UNION
        {{ ?item wdt:P279 wd:Q202866}}
        UNION
        {{ ?item wdt:P279 wd:Q2431196}}
        UNION
        {{ ?item wdt:P279 wd:Q29168811}}
        UNION
        {{ ?item wdt:P279 wd:Q17517379}}
        UNION
        {{ ?item wdt:P279 wd:Q110900120}}
        FILTER (LCASE(STR(?label)) = '{}')
        FILTER(LANG(?label) = "en")
}}
LIMIT 1
"""

person_or_film_lowercase_label_match_V2 = """
prefix wdt: <http://www.wikidata.org/prop/direct/>
prefix wd: <http://www.wikidata.org/entity/>
SELECT DISTINCT ?item ?label 
WHERE {{
        ?item rdfs:label ?label .
        ?item wdt:P31 ?prop_instace_of .
        {{
            FILTER (?prop_instace_of in (wd:Q11424, wd:Q24862, wd:Q5, wd:Q506240, wd:Q336144, wd:Q20650540, wd:Q759853, wd:Q110900120, wd:Q29168811, wd:Q17517379))
        }}
        UNION
        {{
            ?prop_instace_of wdt:P279 ?prop_subclass_of .
            FILTER (?prop_subclass_of in (wd:Q11424, wd:Q202866, wd:Q2431196, wd:Q29168811, wd:Q17517379, wd:Q110900120))
        }}
        FILTER (LCASE(STR(?label)) = '{}')
        FILTER(LANG(?label) = "en")
}}
LIMIT 1
"""

film_lowercase_label_match = """
prefix wdt: <http://www.wikidata.org/prop/direct/>
prefix wd: <http://www.wikidata.org/entity/>
SELECT DISTINCT ?item ?label 
WHERE {{
        ?item rdfs:label ?label .
        ?item wdt:P31 ?prop_instace_of .
        {{
            FILTER (?prop_instace_of in (wd:Q11424, wd:Q24862, wd:Q506240, wd:Q336144, wd:Q20650540, wd:Q759853, wd:Q110900120, wd:Q29168811, wd:Q17517379))
        }}
        UNION
        {{
            ?prop_instace_of wdt:P279 ?prop_subclass_of .
            FILTER (?prop_subclass_of in (wd:Q11424, wd:Q202866, wd:Q2431196, wd:Q29168811, wd:Q17517379, wd:Q110900120))
        }}
        FILTER (LCASE(STR(?label)) = '{}')
        FILTER(LANG(?label) = "en")
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


"""
###############################
Queries for recommendations
###############################

"""
one_hop_prop_count = """
prefix wdt: <http://www.wikidata.org/prop/direct/>
prefix wd: <http://www.wikidata.org/entity/>
SELECT DISTINCT ?prop ?prop_label (COUNT(?prop) AS ?prop_count) 
WHERE {{
    ?id wdt:{property_id} ?prop .
    ?prop rdfs:label ?prop_label .
    FILTER (?id IN ({wk_ent_list}))
    FILTER(LANG(?prop_label) = "en").
}}
GROUP BY ?prop ?prop_label
ORDER BY DESC(?prop_count) 
"""


two_hop_prop_count = """
prefix wdt: <http://www.wikidata.org/prop/direct/>
prefix wd: <http://www.wikidata.org/entity/>
SELECT DISTINCT ?prop_inst ?prop_inst_label (COUNT(?prop) AS ?prop_count) 
WHERE {{
    ?id wdt:{property_id} ?prop .
    ?prop wdt:P31 ?prop_inst .
    ?prop_inst rdfs:label ?prop_inst_label . 
    FILTER (?id IN ({wk_ent_list}))
    FILTER(LANG(?prop_inst_label) = "en").
}}
GROUP BY ?prop_inst ?prop_inst_label
ORDER BY DESC(?prop_count) 
"""
