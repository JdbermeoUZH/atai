
imdb_query = """
prefix wdt: <http://www.wikidata.org/prop/direct/>
prefix wd: <http://www.wikidata.org/entity/>
SELECT DISTINCT ?imdb WHERE {
    ?id wdt:P345 ?imdb .
}
LIMIT 10
"""

