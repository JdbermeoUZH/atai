import json

from knowledge_graphs.BasicKG import BasicKG
from knowledge_graphs.wikidata_queries import imdb_query


class WikiDataKG(BasicKG):
    def __init__(self, kg_tuple_file_path: str, imdb2movienet_filepath: str):
        super().__init__(kg_tuple_file_path)
        self.imdb2movienet = json.load(open(imdb2movienet_filepath, 'r'))

    def check_if_entity_in_kg(self, wk_ent_id: str) -> bool:
        return ((self.namespaces.WD[wk_ent_id], None, None) in self.kg) or \
               ((None, None, self.namespaces.WD[wk_ent_id]) in self.kg)

    def check_if_property_in_kg(self, wk_prop_id: str) -> bool:
        return (None, self.namespaces.WD[wk_prop_id], None) in self.kg

    def get_imdb_id(self, wk_ent_id: str):
        query_result = self.kg.query(imdb_query, initBindings={"id": self.namespaces.WD[wk_ent_id]})
        imdb_ids = [str(imdb[0]) for imdb in query_result]
        if len([str(imdb[0]) for imdb in query_result]) >= 1:
            return [str(imdb[0]) for imdb in query_result][0]
        else:
            return None

    def get_movinet_id(self, imdb_id: str):
        return self.imdb2movienet[imdb_id]


if __name__ == '__main__':
    kg = WikiDataKG(
        kg_tuple_file_path='../../setup_data/14_graph.nt',
        imdb2movienet_filepath='../../setup_data/imdb2movienet.json'
    )

    assert 'nm0000770' in kg.imdb2movienet
    assert kg.imdb2movienet['nm0000770']