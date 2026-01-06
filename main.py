from config import INDEX_NAME
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from elastic_transport import ObjectApiResponse
from utils import get_es_client

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
    year: str | None = None
):
    try:
        es = get_es_client(max_retries=1, sleep_time=0)
        query = {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": search_query,
                            "fields": ["title", "body", "Epigrafe"],
                        }
                    }
                ]
            }
        }

        # if year:
        #     query["bool"]["filter"] = [
        #         {
        #             "range": {
        #                 "date": {
        #                     "gte": f"{year}-01-01",
        #                     "lte": f"{year}-12-31",
        #                     "format": "yyyy-MM-dd",
        #                 }
        #             }
        #         }
        #     ]

        # index_name = (
        #     INDEX_NAME_DEFAULT if tokenizer == "Standard" else INDEX_NAME_N_GRAM
        # )
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
        return print(e)
    
def get_total_hits(response: ObjectApiResponse) -> int:
    return response["hits"]["total"]["value"]


def calculate_max_pages(total_hits: int, limit: int) -> int:
    return (total_hits + limit - 1) // limit
