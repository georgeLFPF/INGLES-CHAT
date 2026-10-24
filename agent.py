"""Loop do agente: modelo (Ollama) + memória + RAG + tools do servidor MCP."""

import asyncio
import json
import logging
import os
import re
import sys
from pathlib import Path

import ollama
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from analisador import Analisador
from memory import MemoriaCurtoPrazo
from rag import BaseRegras

log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
MODELO_CHAT = os.getenv("OLLAMA_MODEL", "llama3.1")
MAX_RODADAS_TOOLS = 6

SERVIDOR_MCP = StdioServerParameters(
    command=sys.executable,
    args=[str(BASE_DIR / "mcp_server.py")],
    cwd=str(BASE_DIR),
)

# Tool local (fora do MCP): deixa o modelo consultar o RAG com a palavra já em inglês.
TOOL_RAG = {
    "type": "function",
    "function": {
        "name": "buscar_regras_pronuncia",
        "description": "Busca na base de regras de pronúncia para brasileiros as regras "
        "relevantes para uma palavra em inglês ou um som (ex.: 'th', '-ed', 'ough').",
        "parameters": {
            "type": "object",
            "properties": {"consulta": {"type": "string"}},
            "required": ["consulta"],
        },
    },
}

PROMPT_SISTEMA = """Você é um tutor de pronúncia de inglês para brasileiros. Responda sempre em português.

Regras:
- NUNCA invente o IPA: use sempre a tool ipa_da_palavra. Se ela devolver erro, avise o usuário que a palavra não foi encontrada.
- Use contar_silabas, rimas_da_palavra e listar_palavras quando o usuário pedir sílabas, rimas ou o histórico.
- Baseie as dicas nas regras de pronúncia fornecidas (use buscar_regras_pronuncia se precisar de mais).
- A pronúncia "aportuguesada" deve ser legível por um brasileiro, entre aspas (ex.: "dóg").
- Perguntas como "e a rima dela?" se referem à última palavra estudada.

{contexto}

Regras de pronúncia relevantes:
{regras}
"""

INSTRUCAO_CARTAO = """O usuário quer aprender a pronunciar: "{palavra}".
1. Se a palavra estiver em português, traduza para o inglês (a tradução mais comum).
2. Chame ipa_da_palavra com a palavra em inglês.
3. Se der certo, chame salvar_palavra com ingles, portugues e ipa.
4. Responda APENAS com um JSON neste formato, sem texto fora dele:
{{"ingles": "...", "portugues": "...", "ipa": "/.../", "pronuncia": "...", "dica": "...", "exemplo": "frase em inglês", "exemplo_pronuncia": "frase aportuguesada"}}
Se a palavra não existir no dicionário, responda {{"erro": "explicação curta"}}."""

# Usada quando o agente de análise já organizou e traduziu a palavra.
INSTRUCAO_CARTAO_ANALISADO = """A etapa de análise já preparou a palavra:
- inglês: "{ingles}"
- português: "{portugues}"
- classe: {classe}
- observação da análise: {observacao}

1. Chame ipa_da_palavra com "{ingles}".
2. Se der certo, chame salvar_palavra com ingles, portugues e ipa.
3. Responda APENAS com um JSON neste formato, sem texto fora dele:
{{"ingles": "{ingles}", "portugues": "{portugues}", "ipa": "/.../", "pronuncia": "...", "dica": "...", "exemplo": "frase em inglês", "exemplo_pronuncia": "frase aportuguesada"}}
Se a palavra não existir no dicionário, responda {{"erro": "explicação curta"}}."""


def _cliente_ollama() -> ollama.Client:
    headers = {}
    if api_key := os.getenv("OLLAMA_API_KEY"):
        headers["Authorization"] = f"Bearer {api_key}"
    return ollama.Client(host=os.getenv("OLLAMA_HOST"), headers=headers or None)


def verificar_modelos(cliente: ollama.Client, *modelos: str) -> None:
    """Falha cedo, com mensagem clara, se o servidor Ollama não tiver os modelos."""
    host = os.getenv("OLLAMA_HOST") or "http://127.0.0.1:11434"
    disponiveis = {m.model for m in cliente.list().models}
    faltando = [m for m in modelos if m not in disponiveis and f"{m}:latest" not in disponiveis]
    if faltando:
        raise RuntimeError(
            f"O Ollama em {host} não tem os modelos {', '.join(faltando)} "
            f"(disponíveis: {', '.join(sorted(disponiveis)) or 'nenhum'}). "
            f"Rode `ollama pull {' '.join(faltando)}` ou ajuste OLLAMA_HOST."
        )


def _texto_resultado(resultado) -> str:
    return "\n".join(c.text for c in resultado.content if getattr(c, "text", None))


def extrair_json(texto: str) -> dict | None:
    texto = re.sub(r"<think>.*?</think>", "", texto, flags=re.DOTALL)
    achado = re.search(r"\{.*\}", texto, flags=re.DOTALL)
    if not achado:
        return None
    try:
        return json.loads(achado.group(0))
    except json.JSONDecodeError:
        return None


class Agente:
    def __init__(self, modelo: str = MODELO_CHAT):
        self.modelo = modelo
        self.ollama = _cliente_ollama()
        self.memoria = MemoriaCurtoPrazo()
        self.rag = BaseRegras()
        # O mesmo modelo faz a análise e o chat: só um modelo fica carregado no Ollama.
        self.analisador = Analisador(self.modelo)
        verificar_modelos(self.ollama, self.modelo)

    # ---------- API pública (síncrona, para o Streamlit) ----------

    def pronunciar(self, palavra: str) -> dict:
        """Gera o cartão de pronúncia de uma palavra (português ou inglês).

        Fluxo: agente de análise (organiza e traduz) -> agente (IPA, dica, exemplo).
        """
        analise = self.analisador.analisar(palavra)
        if analise is None:
            # Sem análise, o próprio agente traduz, como antes.
            pedido = INSTRUCAO_CARTAO.format(palavra=palavra.strip())
            consulta_rag = palavra
        elif not analise.get("valido"):
            return {"erro": analise.get("observacao") or "Digite uma palavra para aprender."}
        else:
            pedido = INSTRUCAO_CARTAO_ANALISADO.format(
                ingles=analise["ingles"],
                portugues=analise["portugues"],
                classe=analise.get("classe") or "-",
                observacao=analise.get("observacao") or "nenhuma",
            )
            consulta_rag = analise["ingles"]

        resposta = asyncio.run(self._executar(pedido, consulta_rag=consulta_rag))
        cartao = extrair_json(resposta) or {"erro": "Resposta inesperada do modelo.", "bruto": resposta}
        if analise and "ingles" in cartao:
            cartao["analise"] = analise
        if self.analisador.ultimo_erro:
            cartao["aviso_analise"] = f"A análise falhou: {self.analisador.ultimo_erro}"
        if "ingles" in cartao:
            self.memoria.registrar_palavra(cartao["ingles"])
            self.memoria.adicionar("user", f"Como se pronuncia '{palavra}'?")
            self.memoria.adicionar(
                "assistant",
                f"{cartao['ingles']} {cartao.get('ipa', '')} = {cartao.get('pronuncia', '')}",
            )
        return cartao

    def conversar(self, mensagem: str) -> str:
        """Responde a uma pergunta livre usando a memória da sessão."""
        resposta = asyncio.run(self._executar(mensagem, consulta_rag=mensagem))
        resposta = re.sub(r"<think>.*?</think>", "", resposta, flags=re.DOTALL).strip()
        self.memoria.adicionar("user", mensagem)
        self.memoria.adicionar("assistant", resposta)
        return resposta

    def chamar_tool(self, nome: str, argumentos: dict | None = None) -> dict:
        """Chama uma tool do MCP diretamente, sem passar pelo modelo."""

        async def _chamar():
            async with stdio_client(SERVIDOR_MCP) as (leitura, escrita):
                async with ClientSession(leitura, escrita) as sessao:
                    await sessao.initialize()
                    return await sessao.call_tool(nome, argumentos or {})

        return json.loads(_texto_resultado(asyncio.run(_chamar())) or "{}")

    # ---------- Loop do agente ----------

    async def _executar(self, pedido: str, consulta_rag: str) -> str:
        regras = self.rag.buscar(consulta_rag)
        sistema = PROMPT_SISTEMA.format(
            contexto=self.memoria.contexto(),
            regras="\n\n".join(regras) or "(nenhuma)",
        )
        mensagens = [
            {"role": "system", "content": sistema},
            *self.memoria.historico(),
            {"role": "user", "content": pedido},
        ]

        async with stdio_client(SERVIDOR_MCP) as (leitura, escrita):
            async with ClientSession(leitura, escrita) as sessao:
                await sessao.initialize()
                tools_mcp = (await sessao.list_tools()).tools
                tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": t.name,
                            "description": t.description or "",
                            "parameters": t.inputSchema,
                        },
                    }
                    for t in tools_mcp
                ] + [TOOL_RAG]

                for _ in range(MAX_RODADAS_TOOLS):
                    resp = self.ollama.chat(model=self.modelo, messages=mensagens, tools=tools)
                    mensagens.append(resp.message)
                    if not resp.message.tool_calls:
                        return resp.message.content or ""

                    for chamada in resp.message.tool_calls:
                        nome = chamada.function.name
                        args = dict(chamada.function.arguments or {})
                        log.info("Tool: %s %s", nome, args)
                        if nome == TOOL_RAG["function"]["name"]:
                            saida = "\n\n".join(self.rag.buscar(args.get("consulta", ""))) or "(nada encontrado)"
                        else:
                            try:
                                saida = _texto_resultado(await sessao.call_tool(nome, args))
                            except Exception as e:  # tool inexistente ou argumentos ruins
                                saida = json.dumps({"erro": str(e)}, ensure_ascii=False)
                        mensagens.append({"role": "tool", "content": saida, "tool_name": nome})

        return "Não consegui concluir a resposta (muitas chamadas de tools)."
