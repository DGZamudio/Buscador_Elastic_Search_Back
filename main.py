from config import HIGHLIGHTER_CONFIG, INDEX_NAME, MIN_SCORE_THRESHOLD, regular_search_query, semantic_search_query
from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from elastic_transport import ObjectApiResponse
from embeddings import get_embedding
from models import SearchBody
from utils import build_faceta, build_query, get_es_client

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
        query = regular_search_query(search_query)

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
                "highlight": HIGHLIGHTER_CONFIG
            },
            filter_path=[
                "hits.hits._source",
                "hits.hits._score",
                "hits.hits.highlight",
                "hits.total",
            ]
        )

        total_hits = get_total_hits(response)
        max_pages = calculate_max_pages(total_hits, body.limit)

        return {
            "hits": response["hits"].get("hits", []),
            "max_pages": total_hits,
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

        query = semantic_search_query(search_query, embedded_query)

        if body.filters:
            build_query(query=query, filters=body.filters)

        skip, limit = body.skip * body.limit, body.limit

        response = es.search(
            index=INDEX_NAME,
            body={
                "query": query,
                "from": skip,
                "size": limit,
                "min_score": MIN_SCORE_THRESHOLD,
                "_source": {
                    "excludes": ["embedding"]
                },
                "highlight": HIGHLIGHTER_CONFIG
            },
            filter_path=[
                "hits.hits._source",
                "hits.hits._score",
                "hits.hits.highlight",
                "hits.total",
            ]
        )

        total_hits = get_total_hits(response)
        max_pages = calculate_max_pages(total_hits, body.limit)

        return {
            "hits": response["hits"].get("hits", []),
            "max_pages": total_hits,
        }
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
@app.get("/api/v1/search/filters")
def get_selects():
    try:
        es = get_es_client(max_retries=1, sleep_time=0)
        
        aggs = {
            "tipos": {
                "terms": {
                    "field": "Tipo.keyword",
                    "order": {"_key": "asc"},
                    "min_doc_count": 1
                },
            },
            "entidades": {
                "terms": {
                    "field": "Entidad.keyword",
                    "order": {"_key": "asc"},
                    "min_doc_count": 1
                }
            }
        }
        
        response = es.search(
            index=INDEX_NAME,
            body={
                "size": 0,
                "aggs": aggs
            }
        )

        return {
            "filters": response.get("aggregations", {})
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/api/v1/filter_fragments")
def filter_fragments(
    search_query: str = Query(..., min_length=1),
    body: SearchBody = Body(...)
):
    try:
        es = get_es_client(max_retries=1, sleep_time=0)

        query = regular_search_query(search_query)

        if body.filters:
            build_query(query=query, filters=body.filters)

        aggs = {
            "tipo": {
                "terms": {
                    "field": "Tipo.keyword",
                    "order": {"_key": "asc"},
                    "min_doc_count": 1
                },
                "aggs": {
                    "entidad": {
                        "terms": {
                            "field": "Entidad.keyword",
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

        faceta = build_faceta(response.get("aggregations", {}))

        return {
            "filters": faceta
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))