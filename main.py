from config import INDEX_NAME
from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from elastic_transport import ObjectApiResponse
from embeddings import get_embedding
from models import SearchBody
from utils import build_query, filter_hits, get_es_client

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.post("/api/v1/regular_search/")
async def regular_search(
    search_query: str = Query(..., min_length=1),
    body: SearchBody = Body(...)
):
    try:
        es = get_es_client(max_retries=1, sleep_time=0)
        query = {
            "bool": {
                "should": [
                    {
                        "multi_match": {
                            "query": search_query,
                            "type": "bool_prefix",
                            "fields": ["title", "title._2gram", "title._3gram", "Epigrafe", "Epigrafe._2gram", "Epigrafe._3gram"],
                            "minimum_should_match": "70%"
                            
                        }
                    },
                    
                    {
                        "match": {
                            "body": {
                                "query": search_query,
                                "boost": 0.5,
                                "minimum_should_match": "70%"
                            }
                        }
                    }
                ],
                "minimum_should_match": 1
            }
        }

        if body.filters:
            build_query(query=query, filters=body.filters)

        skip, limit = body.skip * body.limit, body.limit

        response = es.search(
            index=INDEX_NAME,
            body={
                "query": query,
                "from": skip,
                "size": limit,
                "_source": {
                    "excludes": ["embedding"]
                }
            },
            filter_path=[
                "hits.hits._source",
                "hits.hits._score",
                "hits.total",
            ],
            sort=[
                {"Numero": "asc"}
            ]
        )

        total_hits = get_total_hits(response)
        max_pages = calculate_max_pages(total_hits, body.limit)

        return {
            "hits": response["hits"].get("hits", []),
            "max_pages": max_pages,
        }
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
def get_total_hits(response: ObjectApiResponse) -> int:
    return response["hits"]["total"]["value"]


def calculate_max_pages(total_hits: int, limit: int) -> int:
    return (total_hits + limit - 1) // limit


@app.post("/api/v1/semantic_search")
def semantic_search(
    search_query: str = Query(..., min_length=1),
    body: SearchBody = Body(...)
):
    try:
        es = get_es_client(max_retries=1, sleep_time=0)
        embedded_query = get_embedding(search_query)

        query = {
            "bool": {
                "should": [
                    {
                        "multi_match": {
                            "query": search_query,
                            "type": "bool_prefix",
                            "fields": ["title", "title._2gram", "title._3gram", "Epigrafe", "Epigrafe._2gram", "Epigrafe._3gram"],
                            "minimum_should_match": "70%"
                        }
                    },
                    {
                        "multi_match": {
                            "query": search_query,
                            "fields": ["Numero", "Tipo", "Entidad", "NombreEpigrafe", "Nombre"],
                            "minimum_should_match": "70%"
                        }
                    }
                ],
                "must": [
                    {
                        "knn": {
                            "field": "embedding",
                            "query_vector": embedded_query,
                            'num_candidates': body.limit * (body.skip + 1)
                        }
                    }
                ]
            }
        }

        if body.filters:
            build_query(query=query, filters=body.filters)

        skip, limit = body.skip * body.limit, body.limit

        response = es.search(
            index=INDEX_NAME,
            body={
                "query": query,
                "from": skip,
                "size": limit,
                "_source": {
                    "excludes": ["embedding"]
                },
            },
            filter_path=[
                "hits.hits._source",
                "hits.hits._score",
                "hits.total",
            ],
            sort=[
                {"Numero": "asc"}
            ]
        )

        hits = filter_hits(response)

        total_hits = get_total_hits(response)
        max_pages = calculate_max_pages(total_hits, body.limit)

        return {
            "hits": hits,
            "max_pages": max_pages,
        }
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
@app.post("/api/v1/filter_fragments")
def filter_fragments(
    search_query: str = Query(..., min_length=1),
    body: SearchBody = Body(...)
):
    try:
        es = get_es_client(max_retries=1, sleep_time=0)

        query = {
            "bool": {
                "should": [
                    {
                        "multi_match": {
                            "query": search_query,
                            "type": "bool_prefix",
                            "fields": ["title", "title._2gram", "title._3gram", "Epigrafe", "Epigrafe._2gram", "Epigrafe._3gram"],
                            "minimum_should_match": "70%"
                            
                        }
                    },
                    
                    {
                        "match": {
                            "body": {
                                "query": search_query,
                                "boost": 0.5,
                                "minimum_should_match": "70%"
                            }
                        }
                    }
                ],
                "minimum_should_match": 1
            }
        }

        if body.filters:
            build_query(query=query, filters=body.filters)

        aggs = {
            "tipo": {
                "terms": {
                    "field": "Tipo",
                    "order": {"_key": "asc"},
                    "min_doc_count": 1
                },
                "aggs": {
                    "entidad": {
                        "terms": {
                            "field": "Entidad",
                            "order": {"_key": "asc"},
                            "min_doc_count": 1
                        },
                        "aggs": {
                            "year": {
                                "date_histogram": {
                                    "field": "Year",
                                    "calendar_interval": "year",
                                    "format": "yyyy",
                                    "min_doc_count": 1
                                }
                            }
                        }
                    }
                }
            }
        }

        response = es.search(
            index=INDEX_NAME,
            body={
                "size": 0,
                "query": query,
                "aggs": aggs
            }
        )

        return {
            "filters": response.get("aggregations", {})
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))