from typing import List, Optional

from fastapi.responses import HTMLResponse
from config import INDEX_NAME
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from elastic_transport import ObjectApiResponse
from embeddings import get_embedding
from utils import build_query, filter_hits, get_es_client

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/api/v1/regular_search/")
async def regular_search(
    search_query: str,
    skip: int = 0,
    limit: int = 10,
    must: Optional[List[str]] = Query(None),
    should: Optional[List[str]] = Query(None),
    year_from: Optional[str] = None,
    year_to: Optional[str] = None
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

        build_query(
            query=query, 
            must=must, 
            should=should, 
            year_from=year_from, 
            year_to=year_to
        )

        response = es.search(
            index=INDEX_NAME,
            body={
                "query": query,
                "from": skip,
                "size": limit,
            },
            filter_path=[
                "hits.hits._source",
                "hits.hits._score",
                "hits.total",
            ],
        )

        total_hits = get_total_hits(response)
        max_pages = calculate_max_pages(total_hits, limit)

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


@app.get("/api/v1/semantic_search")
def semantic_search(
    search_query: str,
    skip: int = 0,
    limit: int = 10,
    must: Optional[List[str]] = Query(None),
    should: Optional[List[str]] = Query(None),
    year_from: Optional[str] = None,
    year_to: Optional[str] = None
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
                        "match": {
                            "body": {
                                "query": search_query,
                                "boost": 0.5,
                            "minimum_should_match": "70%"
                            }
                        }
                    }
                ],
                "must": [
                    {
                        "knn": {
                            "field": "embedding",
                            "query_vector": embedded_query,
                            'num_candidates': 100
                        }
                    }
                ]
            }
        }

        build_query(
            query=query, 
            must=must, 
            should=should, 
            year_from=year_from, 
            year_to=year_to
        )

        response = es.search(
            index=INDEX_NAME,
            body={
                "query": query,
                "from": skip,
                "size": limit,
            },
            filter_path=[
                "hits.hits._source",
                "hits.hits._score",
                "hits.total",
            ],
        )

        hits = filter_hits(response)

        total_hits = get_total_hits(response)
        max_pages = calculate_max_pages(total_hits, limit)

        return {
            "hits": hits,
            "max_pages": max_pages,
        }
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))