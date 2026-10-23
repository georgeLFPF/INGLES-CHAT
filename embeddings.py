"""Embeddings locais com modelos Xenova (ONNX) do Hugging Face.

Os modelos Xenova são versões em ONNX dos sentence-transformers. Rodam com onnxruntime +
tokenizers (já instalados pelo chromadb), sem PyTorch e sem depender do Ollama.
"""

import logging
import os

import numpy as np
import onnxruntime as ort
from huggingface_hub import hf_hub_download
from tokenizers import Tokenizer

log = logging.getLogger(__name__)

# Multilíngue: as regras estão em português e as consultas misturam português e inglês.
MODELO = os.getenv("HF_EMBED_MODEL", "Xenova/paraphrase-multilingual-MiniLM-L12-v2")
ARQUIVO_ONNX = os.getenv("HF_EMBED_ONNX", "onnx/model_quantized.onnx")
MAX_TOKENS = 256


class EmbeddingsHF:
    def __init__(self, modelo: str = MODELO, arquivo_onnx: str = ARQUIVO_ONNX):
        self.modelo = modelo
        log.info("Carregando modelo de embeddings %s", modelo)
        # Baixa na primeira vez e depois usa o cache do Hugging Face (HF_HOME).
        caminho_tokenizer = hf_hub_download(modelo, "tokenizer.json")
        caminho_onnx = hf_hub_download(modelo, arquivo_onnx)

        self.tokenizer = Tokenizer.from_file(caminho_tokenizer)
        self.tokenizer.enable_truncation(max_length=MAX_TOKENS)
        self.tokenizer.enable_padding()
        self.sessao = ort.InferenceSession(caminho_onnx, providers=["CPUExecutionProvider"])
        self.entradas = {i.name for i in self.sessao.get_inputs()}

    def embed(self, textos: list[str]) -> list[list[float]]:
        if not textos:
            return []
        lotes = self.tokenizer.encode_batch(textos)
        ids = np.array([c.ids for c in lotes], dtype=np.int64)
        mascara = np.array([c.attention_mask for c in lotes], dtype=np.int64)

        entrada = {"input_ids": ids, "attention_mask": mascara}
        if "token_type_ids" in self.entradas:
            entrada["token_type_ids"] = np.zeros_like(ids)
        tokens = self.sessao.run(None, entrada)[0]

        # Mean pooling (ignora o padding) + normalização L2, como nos sentence-transformers.
        peso = mascara[..., None].astype(np.float32)
        media = (tokens * peso).sum(axis=1) / np.clip(peso.sum(axis=1), 1e-9, None)
        media /= np.clip(np.linalg.norm(media, axis=1, keepdims=True), 1e-9, None)
        return media.tolist()
