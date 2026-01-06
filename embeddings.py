from sentence_transformers import SentenceTransformer
import torch
from bs4 import BeautifulSoup

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = SentenceTransformer("all-MiniLM-L6-v2").to(device)

def limpiar_html(texto):
    soup = BeautifulSoup(texto, "html.parser")
    return soup.get_text(separator=" ")

def get_embedding(texto):
    texto_limpio = limpiar_html(texto)

    embedding = model.encode(texto_limpio)
    return embedding.tolist()