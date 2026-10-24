"""Agente de análise: organiza o que o aluno digitou e prepara a palavra em inglês.

Roda antes do agente de tradução e pronúncia, usando o mesmo modelo do Ollama. Corrige erros de digitação, identifica o
idioma, extrai a palavra-alvo de frases como "como fala cachorro?" e traduz para o inglês.
O agente recebe a palavra pronta e só precisa cuidar da pronúncia.
"""

import json
import logging
import os
import re

import ollama

log = logging.getLogger(__name__)

PADRAO_INGLES = re.compile(r"^[A-Za-z][A-Za-z' -]{0,39}$")

# Saída estruturada: o Ollama força o modelo a responder neste formato.
ESQUEMA = {
    "type": "object",
    "properties": {
        "valido": {"type": "boolean"},
        "idioma_original": {"type": "string", "enum": ["pt", "en", "outro"]},
        "texto_corrigido": {"type": "string"},
        "ingles": {"type": "string"},
        "portugues": {"type": "string"},
        "classe": {"type": "string"},
        "observacao": {"type": "string"},
    },
    "required": ["valido", "idioma_original", "texto_corrigido", "ingles", "portugues"],
}

PROMPT_ANALISE = """Você analisa o que um aluno brasileiro digitou em um tutor de pronúncia de inglês.

Tarefas:
1. Identifique a palavra ou expressão curta que o aluno quer aprender. Ignore frases em volta, como "como fala", "como se pronuncia", "qual é".
2. Corrija erros de digitação e acentos (ex.: "cachoro" -> "cachorro", "obrigado" continua "obrigado").
3. Diga se o termo está em português ("pt") ou inglês ("en").
4. Prepare o par: "ingles" com a tradução mais comum em inglês (minúsculas, sem pontuação) e "portugues" com o termo em português.
5. "classe": classe gramatical em português (substantivo, verbo, adjetivo, expressão...).
6. "observacao": em português e curta, avise se corrigiu algo ou se há outro sentido comum (ex.: "manga" pode ser "mango" ou "sleeve"). Deixe vazio se não houver nada.
7. "valido": false se não houver palavra para aprender (texto vazio, números, símbolos, frase longa demais). Nesse caso explique em "observacao".

Responda apenas com o JSON."""


def _cliente_ollama() -> ollama.Client:
    headers = {}
    if api_key := os.getenv("OLLAMA_API_KEY"):
        headers["Authorization"] = f"Bearer {api_key}"
    return ollama.Client(host=os.getenv("OLLAMA_HOST"), headers=headers or None)


class Analisador:
    def __init__(self, modelo: str):
        self.modelo = modelo
        self.ollama = _cliente_ollama()
        self.ultimo_erro: str | None = None

    def analisar(self, texto: str) -> dict | None:
        """Devolve a análise organizada, ou None se o modelo falhar (o agente faz sozinho)."""
        self.ultimo_erro = None
        try:
            resp = self.ollama.chat(
                model=self.modelo,
                messages=[
                    {"role": "system", "content": PROMPT_ANALISE},
                    {"role": "user", "content": texto.strip()},
                ],
                format=ESQUEMA,
                options={"temperature": 0},
            )
            analise = json.loads(resp.message.content or "{}")
        except Exception as e:
            log.warning("Análise falhou, o agente seguirá sem ela: %s", e)
            self.ultimo_erro = str(e)
            return None

        analise["ingles"] = analise.get("ingles", "").strip().lower().strip(".,!?\"")
        analise["portugues"] = analise.get("portugues", "").strip()
        # Não confia no "valido" do modelo (modelos pequenos marcam false mesmo acertando a
        # tradução): a palavra é válida se o termo em inglês for algo pronunciável.
        analise["valido"] = bool(PADRAO_INGLES.match(analise["ingles"]))
        if not analise["valido"]:
            analise["observacao"] = analise.get("observacao") or "Não consegui identificar a palavra."
        log.info("Análise: %s", analise)
        return analise
