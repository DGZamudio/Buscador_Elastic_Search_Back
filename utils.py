import time
from pprint import pprint
from elasticsearch import Elasticsearch
from config import JERARQUIA_FACETA
from models import SearchFilters

# Devuelve una conexion con elastic
def get_es_client(max_retries: int = 1, sleep_time: int = 5) -> Elasticsearch:
    i = 0
    while i < max_retries:
        try:
            es = Elasticsearch("http://localhost:9200")
            return es
        except Exception:
            pprint("Could not connect to Elasticsearch, retrying...")
            time.sleep(sleep_time)
            i += 1
    raise ConnectionError("Failed to connect to Elasticsearch after multiple attempts.")

# Construye el query de busqueda, agregando filtros
def build_query(
    query         : dict,
    filters       : SearchFilters
) -> dict:
    bool_query = query.setdefault("bool", {})
    
    if filters.title:
        bool_query.setdefault("must", []).append(
            {"match_phrase_prefix": {
                "title": filters.title
            }}
        )
        
    if filters.proximity and filters.proximity.query:
        bool_query.setdefault("filter", []).append(
            {
                "match_phrase": {
                    "body": {
                        "query": filters.proximity.query,
                        "slop": filters.proximity.distance
                    }
                }
            }
        )
    
    if filters.not_include:
        must_not = bool_query.setdefault("must_not", [])
        
        for palabra in filters.not_include:
            if palabra != "":
                must_not.append({"match": { "body": palabra }})
    
    if filters.phrase:
        bool_query.setdefault("filter", []).append(
            {
                "match_phrase": {
                    "body": {
                        "query": filters.phrase
                    }
                }
            }
        )
        
    if filters.document_type:
        bool_query.setdefault("filter", []).append(
            {"term": {"Tipo.keyword": filters.document_type}}
        )
    
    if filters.must:
        must = bool_query.setdefault("must", [])
        
        for palabra in filters.must:
            if palabra != "":
                must.append({"match": {"body": palabra}})

    if filters.should:
        should = bool_query.setdefault("should", [])
        
        for palabra in filters.should:
            if palabra != "":
                should.append({"match": {"body": palabra}})
            
    if filters.entity:
        bool_query.setdefault("filter", []).append(
            {"term": {"Entidad.keyword": filters.entity}}
        )

    if filters.years and filters.years.year_from is not None and filters.years.year_to is not None:
        bool_query.setdefault("filter", []).append(
            {
                "range": {
                    "Year": {
                        "gte": f"{filters.years.year_from}",
                        "lte": f"{filters.years.year_to}",
                        "format": "yyyy",
                    }
                }
            }
        )

    return query

# Construye la Jerarquía de la normativa y jurisprudencia
def build_faceta(aggs: dict) -> dict:
    if not aggs or "tipo" not in aggs:
        return {}

    normativa = []
    jurisprudencia = []
    otros = []

    for tipo_doc in aggs["tipo"]["buckets"]:
        tipo = tipo_doc["key"].lower()
        matched = False

        # Normativa
        for clave in JERARQUIA_FACETA["Normativa"]:
            if tipo.startswith(clave):
                tipo_doc["_orden"] = clave  # <-- guardamos la palabra clave
                normativa.append(tipo_doc)
                matched = True
                break

        if matched:
            continue

        # Jurisprudencia
        for clave in JERARQUIA_FACETA["Jurisprudencia"]:
            if tipo.startswith(clave):
                tipo_doc["_orden"] = clave
                jurisprudencia.append(tipo_doc)
                matched = True
                break

        if not matched:
            otros.append(tipo_doc)

    # Mapa de orden
    orden_normativa = {tipo: idx for idx, tipo in enumerate(JERARQUIA_FACETA["Normativa"])}
    orden_jurisprudencia = {tipo: idx for idx, tipo in enumerate(JERARQUIA_FACETA["Jurisprudencia"])}

    # Sorting usando la palabra clave
    normativa.sort(key=lambda x: orden_normativa.get(x["_orden"], 999))
    jurisprudencia.sort(key=lambda x: orden_jurisprudencia.get(x["_orden"], 999))

    faceta = {
        "tipo": {
            "doc_count_error_upper_bound": aggs["tipo"]["doc_count_error_upper_bound"],
            "sum_other_doc_count": aggs["tipo"]["sum_other_doc_count"],
            "normativa": normativa,
            "jurisprudencia": jurisprudencia,
            "other": otros,
        }
    }

    return faceta