import json
from pprint import pprint
from tqdm import tqdm
from embeddings import get_embedding
from utils import get_es_client
from config import INDEX_NAME

def _create_index(es, overwrite: bool):
    # Funcion para crear el indice dentro de elastic search
    print(f"Creando indice {INDEX_NAME}")
    if es.indices.exists(index=INDEX_NAME):
        print("El indice ya existe")
        if overwrite:
            es.indices.delete(index=INDEX_NAME, ignore_unavailable=True)
            print("Sobrescribiendo indice...")
        else:
            return
        

    return es.indices.create(
        index=INDEX_NAME,
        body = {
            "mappings": {
                "properties": {
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
                    "embedding": {
                        "type": "dense_vector",
                        "dims": 384,
                        "index": True,
                        "similarity": "cosine"
                    }
                }
            }
        }
    )

def _insert_documents(file, es, num):
    print("Insertando documentos...")
    operaciones = []
    try:
        data = json.load(open(file, "r", encoding="utf-8"))
        
        num = num if num else len(data)
        
        for documento in tqdm(data[:num], total=num):
            operaciones.append({'index': {'_index':INDEX_NAME}})
            operaciones.append({
                **documento,
                'embedding': get_embedding(documento["body"])
            })
        
        es.bulk(operations=operaciones)
        print("Los documentos fueron insertados")
    except Exception as e:
        if len(operaciones) > 0:
            with open("resultados/procesados.json", "w") as f:
                json.dump(operaciones, f, ensure_ascii=False, indent=2)

        print(f"Error: {e}\n {len(operaciones)} archivos procesados guardados")


def index_data(file, num = None, overwrite: bool = False):
    # Funcion para subir multiples documentos mediante un archivo formato JSON
    es = get_es_client()
    _create_index(es=es, overwrite=overwrite)
    _insert_documents(es=es, num=num, file=file)

if __name__ == "__main__":
     index_data("./resultados/datos.json", 200, overwrite=True)