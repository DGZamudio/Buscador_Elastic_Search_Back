INDEX_NAME = "prueba" # Nombre del indice en elasticsearch
INDEX_MAPPING = { # Mapeo de campos del indice
                    "title": {
                        "type": "search_as_you_type",
                        "analyzer": "spanish",
                    },
                    "body": {
                        "type": "text",
                        "analyzer": "spanish"
                    },
                    "Epigrafe": {
                        "type": "text",
                        "analyzer": "spanish"
                    },
                    "Nombre": {
                        "type": "text",
                        "analyzer": "spanish"
                    },
                    "Numero": {
                        "type": "keyword",
                        "fields": {
                            "text": {
                                "type": "text",
                                "analyzer": "spanish"
                            }
                        }
                    },
                    "Year": {
                        "type": "date",
                        "format": "yyyy"
                    },
                    "Tipo": {
                        "type": "text",
                        "analyzer": "spanish",
                        "fields": {
                            "keyword": {
                                "type": "keyword"
                            }
                        }
                    },
                    "Entidad": {
                        "type": "text",
                        "analyzer": "spanish",
                        "fields": {
                            "keyword": {
                                "type": "keyword"
                            }
                        }
                    },
                    "NombreEpigrafe": {
                        "type": "text",
                        "analyzer": "spanish"
                    },
                    "Sigla-Entidad": {
                        "type": "keyword"
                    },
                    "doc-name": {
                        "type": "keyword"
                    },
                    "embedding": {
                        "type": "dense_vector",
                        "dims": 384,
                        "index": True,
                        "similarity": "cosine"
                    }
                }
MIN_SCORE = 0.5 # Puntaje minimo para considerar un resultado relevante
MAX_BULK_SIZE = 5 * 1024 * 1024  # 5 MB / El limite default de transacciones http de elastic es 100mb pero es recomendable enviar chunks mas pequeños para que la conexión no muera


# Querys para busquedas
def regular_search_query(search_query):
    return {
        "bool": {
            "should": [
                {
                    "match_phrase": {
                        "title": {
                            "query": search_query,
                            "boost": 10
                        }
                    }
                },
                {
                    "term": {
                        "Numero": {
                            "value": search_query,
                            "boost": 40
                        }
                    }
                },
                {
                    "term": {
                        "Tipo.keyword": {
                            "value": search_query,
                            "boost": 25
                        }
                    }
                },
                {
                    "term": {
                        "Entidad.keyword": {
                            "value": search_query,
                            "boost": 25
                        }
                    }
                },
                {
                    "multi_match": {
                        "query": search_query,
                        "fields": [
                            "title^6",
                            "Nombre^4",
                            "Numero.text^4",
                            "Tipo^4",
                            "Entidad^4",
                            "Epigrafe^2",
                            "body"
                        ],
                        "operator": "or",
                        "type": "cross_fields",
                        "minimum_should_match": "25%"
                    }
                },
                {
                    "multi_match": {
                        "query": search_query,
                        "type": "bool_prefix",
                        "fields": [
                            "title^4",
                            "title._2gram",
                            "title._3gram"
                        ],
                        "fuzziness": "AUTO"
                    }
                }
            ],
            "minimum_should_match": 1
        }
    }

def semantic_search_query(search_query, embedding_vector):
    semantic_query = regular_search_query(search_query)
    
    semantic_query["bool"]["should"].append(
        {
            "knn": {
                "field": "embedding",
                "query_vector": embedding_vector,
                "num_candidates": 150,
                "boost": 0.7
            }
        }
    )
    return semantic_query
    
HIGHLIGHTER_CONFIG = {
                    "pre_tags": ["<mark class='es-highlight'>"],
                    "post_tags": ["</mark>"],
                    "fields": {
                        "Epigrafe": {
                            "fragment_size": 250,
                            "number_of_fragments": 1
                        },
                        "body": {
                            "fragment_size": 250,
                            "number_of_fragments": 1
                        }
                    }
                }

JERARQUIA_FACETA = { # Dejar el contenido de cada una en minúsculas para mejor coincidencia
    "Normativa": [ 
        "constituciones",
        "actos legislativos",
        "leyes",
        "decretos",
        "acuerdos"
    ],
    "Jurisprudencia": [
        "corte constitucional",
        "consejo de estado",
        "comision de regulacion DE DISIPLINA",
        "consejo nacional de la judicaruta",
        "jep"
    ]
}

LOOKUP_FACETA = {# Se usa un set al momento de comparar ya que es mucho mas eficiente que las listas | No se puede usar porque hay matches incompletos :(
    k: set(v) for k, v in JERARQUIA_FACETA.items()
}
