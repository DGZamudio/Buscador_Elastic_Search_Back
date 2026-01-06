import json
from pprint import pprint
from tqdm import tqdm
from embeddings import get_embedding
from utils import get_es_client
from config import INDEX_NAME

def _create_index(es, overwrite: bool):
    # Funcion para crear el indice dentro de elastic search
    if es.indices.exists(index=INDEX_NAME):
        if overwrite:
            es.indices.delete(index=INDEX_NAME, ignore_unavailable=True)

        return

    return es.indices.create(
        index=INDEX_NAME,
        body={
            "settings":{
                "analysis":{
                    "default" : {
                        "type":"custom",
                        "tokenizer":"n_gram_tokenizer"
                    }
                },
                "tokenizer":{
                    "n_gram_tokenizer":{
                        "type":"edge_ngram",
                        "min_gram":3,
                        "max_gram":45,
                        "token_chars":["letter","digit"]
                    }
                }
            }
        },
        mappings={
            "properties":{
                "embedding": {
                    "type":"dense_vector",
                      'dims': 384,
                      'index': True,
                      'similarity': 'cosine'
                }
            }
        }
    )

def _insert_documents(file, es, num):
    try:
        data = json.load(open(file, "r", encoding="utf-8"))
        
        num = num if num else len(data)

        operaciones = []
        for documento in tqdm(data[:num], total=num):
            operaciones.append({'index': {'_index':INDEX_NAME}})
            operaciones.append({
                **documento,
                'embedding': get_embedding(documento["body"])
            })
        
        es.bulk(operations=operaciones)
        print("Los documentos fueron insertados")
    except Exception as e:
        print(f"Error al abrir el documento: {e}")


def index_data(file, num = None, overwrite: bool = False):
    # Funcion para subir multiples documentos mediante un archivo formato JSON
    es = get_es_client()
    _create_index(es=es, overwrite=overwrite)
    _insert_documents(es=es, num=num, file=file)

if __name__ == "__main__":
     index_data("./resultados/datos.json", 10, overwrite=True)