INDEX_NAME = "prueba"
INDEX_MAPPING = {
                    "title": {
                        "type": "search_as_you_type"
                    },
                    "body": {
                        "type": "text",
                        "analyzer": "spanish"
                    },
                    "Epigrafe": {
                        "type": "search_as_you_type"
                    },
                    "Nombre": {
                        "type": "text",
                        "analyzer": "spanish"
                    },
                    "Numero": {
                        "type": "keyword",
                    },
                    "Year": {
                        "type": "date",
                        "format": "yyyy"
                    },
                    "Tipo": {
                        "type": "keyword"
                    },
                    "Entidad": {
                        "type": "keyword"
                    },
                    "NombreEpigrafe": {
                        "type": "text",
                        "analyzer": "spanish"
                    },
                    "Sigla-Entidad": {
                        "type": "keyword"
                    },
                    "embedding": {
                        "type": "dense_vector",
                        "dims": 384,
                        "index": True,
                        "similarity": "cosine"
                    }
                }
MIN_SCORE = 1.25
MAX_BULK_SIZE = 5 * 1024 * 1024  # 5 MB / El limite default de transacciones http de elastic es 100mb pero es recomendable enviar chunks mas pequeños para que la conexión no muera