import json
import os
import re
from tqdm import tqdm
from typing import Tuple, Any, Optional

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


def _load_entity_or_property_labels_from_json(filepath: str):
    return json.load(open(filepath, 'r'))


class BasicKG:
    def __init__(self,
                 kg_tuple_file_path: str,
                 entity_label_filepath: Optional[str] = None,
                 property_label_filepath: Optional[str] = None):
        self.kg = parse_kg_graph(kg_tuple_file_path)
        print("KG loaded")
        self.namespaces = Namespaces()
        self.entity_labels_dict = self._extract_entity_labels_dict() if entity_label_filepath is None \
            else _load_entity_or_property_labels_from_json(entity_label_filepath)
        print("Entity labels processed")
        self.property_labels_dict = self._extract_property_labels_dict() if property_label_filepath is None \
            else _load_entity_or_property_labels_from_json(property_label_filepath)
        print("Property labels processed")

    def check_if_triple_in_kg(self, triple: Tuple[Any, Any, Any]) -> bool:
        return triple in self.kg

    def check_if_entity_in_kg(self, ent_uri_str: str) -> bool:
        return ((rdflib.URIRef(ent_uri_str), None, None) in self.kg) or \
               (None, None, (rdflib.URIRef(ent_uri_str)) in self.kg)

    def check_if_property_in_kg(self, prop_uri_str: str) -> bool:
        return (None, rdflib.URIRef(prop_uri_str), None) in self.kg

    def _extract_entity_labels_dict(self) -> dict:
        return {
            node.toPython(): self.kg.value(node, self.namespaces.RDFS.label).toPython()
            for node in tqdm(self.kg.all_nodes())
            if (isinstance(node, rdflib.URIRef) and self.kg.value(node, self.namespaces.RDFS.label))
        }

    def _extract_property_labels_dict(self) -> dict:
        return {
            p.toPython(): self.kg.value(p, self.namespaces.RDFS.label).toPython() for _, p, _ in tqdm(self.kg)
            if (isinstance(p, rdflib.URIRef) and self.kg.value(p, self.namespaces.RDFS.label))
        }
