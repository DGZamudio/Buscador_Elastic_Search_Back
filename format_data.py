import json
import os
from tqdm import tqdm
from bs4 import BeautifulSoup

campos = {"Epigrafe", "Year", "Numero", "Tipo", "Entidad", "Sigla-Entidad", "Nombre", "NombreEpigrafe"}

def htm_to_json(path):
    with open(path, encoding="cp1252", errors="ignore") as f:
        soup = BeautifulSoup(f, "lxml")

        data = {}
        data["title"] = soup.title.text if soup.title else None
        data["body"] = soup.body.text if soup.body else None
        data["doc-name"] = path.split("/")[-1]

        metas = soup.find_all("meta")
        for meta in metas:
            if meta.get("name") in campos:
                data[meta.get("name")] = meta.get("content")

        return data

results = []

if __name__ == "__main__":
    archivos = os.listdir("metadatos")
    for file in tqdm(archivos, total=len(archivos)):
        if file.endswith(".htm"):
            results.append(htm_to_json(f"metadatos/{file}"))

    print("Generando JSON...")

    try:
        with open("resultados/datos.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    except FileNotFoundError:
        input("Algo pasoo ingresa otra ruta: ")
    except Exception as e:
        print("Error: ", e)

    print("JSON generado 🐱‍🐉")