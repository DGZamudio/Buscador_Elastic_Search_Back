import json
from pprint import pprint
from tqdm import tqdm
from embeddings import get_embedding
from utils import get_es_client
from config import INDEX_MAPPING, INDEX_NAME, MAX_BULK_SIZE

def sizeof(obj):
    return len(json.dumps(obj, ensure_ascii=False).encode('utf-8'))

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
                "properties": INDEX_MAPPING
            }
        }
    )

def _insert_documents(file, es, num):
    print("Insertando documentos...")

    operaciones = []
    current_bulk_size = 0
    
    try:
        data = json.load(open(file, "r", encoding="utf-8"))
        
        num = num if num else len(data)
        
        for documento in tqdm(data[:num], total=num):
            op_index = {'index': {'_index':INDEX_NAME}}
            op_doc = {**documento, 'embedding': get_embedding(documento["body"])}

            op_size = sizeof(op_index) + sizeof(op_doc) # Tamaño del documento aproximado

            # Si se llega al tamaño máximo, se envía la petición :p
            if current_bulk_size + op_size > MAX_BULK_SIZE and operaciones:
                es.bulk(operations=operaciones)
                operaciones = []
                current_bulk_size = 0
                
            # Se agrega al bulk
            operaciones.append(op_index)
            operaciones.append(op_doc)
            current_bulk_size += op_size

        #Enviar sobrante
        if operaciones:
            es.bulk(operations=operaciones)

        print("Los documentos fueron insertados")
    except Exception as e:
        if operaciones:
            with open("resultados/procesados.json", "w") as f:
                json.dump(operaciones, f, ensure_ascii=False, indent=2)

        print(f"Error: {e}\n {len(operaciones)//2} documentos guardados")


def index_data(file, num = None, overwrite: bool = False):
    # Funcion para subir multiples documentos mediante un archivo formato JSON
    es = get_es_client()
    _create_index(es=es, overwrite=overwrite)
    _insert_documents(es=es, num=num, file=file)

if __name__ == "__main__":
     index_data("./resultados/datos.json", 5000, overwrite=True)