import time
from pprint import pprint
from typing import List, Optional

from elasticsearch import Elasticsearch

from config import MIN_SCORE

# Devuelve una conexion con elastic
def get_es_client(max_retries: int = 1, sleep_time: int = 5) -> Elasticsearch:
    i = 0
    while i < max_retries:
        try:
            es = Elasticsearch("http://localhost:9200")
            pprint("Connected to Elasticsearch!")
            return es
        except Exception:
            pprint("Could not connect to Elasticsearch, retrying...")
            time.sleep(sleep_time)
            i += 1
    raise ConnectionError("Failed to connect to Elasticsearch after multiple attempts.")

# Construye el query de busqueda, agregando filtros
def build_query(
    query: dict, 
    must: Optional[List[str]] = None, 
    should: Optional[List[str]] = None,
    year_from: Optional[str] = None,
    year_to: Optional[str] = None
) -> dict:
    if must:
        if not query["bool"].get("must", None):
            query["bool"]["must"] = []

        for palabra in must:
            query["bool"]["must"].append({"match": {"body": palabra}})

    if should:
        if not query["bool"].get("should", None):
            query["bool"]["should"] = []

        for palabra in should:
            query["bool"]["should"].append({"match": {"body": palabra}})

    if year_to and year_from:
        query["bool"]["filter"] = [
            {
                "range": {
                    "Year": {
                        "gte": f"{year_from}",
                        "lte": f"{year_to}",
                        "format": "yyyy",
                    }
                }
            }
        ]

    return query

# Filtra los documentos que devuelve la búsqueda y solo agrega los que superan el mínimo de puntuación, asi evitando resultados alejados
def filter_hits(response):
    hits = response["hits"]["hits"]

    filtered_hits = [
        hit for hit in hits
        if hit["_score"] >= MIN_SCORE
    ]

    return filtered_hits