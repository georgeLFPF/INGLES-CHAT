"""RAG: indexa as regras de pronúncia no ChromaDB e busca as mais relevantes."""

import logging
import os
import re
from pathlib import Path

import chromadb

from embeddings import EmbeddingsHF

log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
ARQUIVO_REGRAS = BASE_DIR / "data" / "regras_pronuncia.txt"
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", BASE_DIR / ".chroma"))
COLECAO = "regras_pronuncia"


def _carregar_regras() -> list[tuple[str, str]]:
    """Divide o arquivo em blocos (título, texto) separados por '## '."""
    texto = ARQUIVO_REGRAS.read_text(encoding="utf-8")
    blocos = re.split(r"^## ", texto, flags=re.MULTILINE)
    regras = []
    for bloco in blocos:
        bloco = bloco.strip()
        if not bloco:
            continue
        titulo, _, corpo = bloco.partition("\n")
        regras.append((titulo.strip(), f"{titulo.strip()}\n{corpo.strip()}"))
    return regras


class BaseRegras:
    def __init__(self):
        self.embeddings = EmbeddingsHF()
        self.chroma = chromadb.PersistentClient(path=str(CHROMA_DIR))
        # Uma coleção por modelo: modelos diferentes geram vetores de tamanhos diferentes.
        sufixo = re.sub(r"[^A-Za-z0-9]+", "-", self.embeddings.modelo).strip("-").lower()
        self.colecao = self.chroma.get_or_create_collection(
            f"{COLECAO}-{sufixo}"[:63], metadata={"hnsw:space": "cosine"}
        )
        if self.colecao.count() == 0:
            self.indexar()

    def _embed(self, textos: list[str]) -> list[list[float]]:
        return self.embeddings.embed(textos)

    def indexar(self) -> int:
        regras = _carregar_regras()
        ids = [f"regra-{i}" for i in range(len(regras))]
        documentos = [texto for _, texto in regras]
        self.colecao.upsert(
            ids=ids,
            documents=documentos,
            embeddings=self._embed(documentos),
            metadatas=[{"titulo": titulo} for titulo, _ in regras],
        )
        log.info("RAG: %d regras indexadas", len(regras))
        return len(regras)

    def buscar(self, consulta: str, k: int = 3) -> list[str]:
        if not consulta.strip():
            return []
        resultado = self.colecao.query(
            query_embeddings=self._embed([consulta]), n_results=k
        )
        return resultado["documents"][0] if resultado["documents"] else []


if __name__ == "__main__":
    # Reindexa a base: python rag.py
    logging.basicConfig(level=logging.INFO)
    base = BaseRegras()
    print(f"{base.indexar()} regras indexadas.")
    for doc in base.buscar("thought"):
        print("-", doc.splitlines()[0])
