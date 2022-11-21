import os
from typing import Tuple, Any

import rdflib


class Namespaces:
    def __init__(self):
        self.WD = rdflib.Namespace('http://www.wikidata.org/entity/')
        self.WDT = rdflib.Namespace('http://www.wikidata.org/prop/direct/')
        self.DDIS = rdflib.Namespace('http://ddis.ch/atai/')
        self.RDFS = rdflib.namespace.RDFS
        self.SCHEMA = rdflib.Namespace('http://schema.org/')


def parse_kg_graph(kg_tuple_file_path: str):
    graph = rdflib.Graph()
    if os.path.basename(kg_tuple_file_path).endswith('.nt'):
        graph.parse(source=kg_tuple_file_path, format='turtle')
    else:
        graph.parse(source=kg_tuple_file_path)

    return graph


class BasicKG:
    def __init__(self, kg_tuple_file_path: str):
        self.kg = parse_kg_graph(kg_tuple_file_path)
        self.namespaces = Namespaces()

    def check_if_triple_in_kg(self, triple: Tuple[Any, Any, Any]) -> bool:
        return triple in self.kg

    def check_if_entity_in_kg(self, ent_uri_str: str) -> bool:
        return ((rdflib.URIRef(ent_uri_str), None, None) in self.kg) or \
               (None, None, (rdflib.URIRef(ent_uri_str)) in self.kg)

    def check_if_property_in_kg(self, prop_uri_str: str) -> bool:
        return (None, rdflib.URIRef(prop_uri_str), None) in self.kg








