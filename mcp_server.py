"""Servidor MCP com tools determinísticas de pronúncia e o histórico do aluno."""

import logging
import os
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import eng_to_ipa
import pronouncing
from mcp.server.fastmcp import FastMCP

# Via stdio o stdout é do protocolo MCP: logs vão para o stderr.
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
log = logging.getLogger("mcp_server")

BASE_DIR = Path(__file__).parent
DB_PATH = Path(os.getenv("DB_PATH", BASE_DIR / "progresso.db"))
ARQUIVO_REGRAS = BASE_DIR / "data" / "regras_pronuncia.txt"
MAX_TAMANHO = 40
PADRAO_PALAVRA = re.compile(r"^[A-Za-zÀ-ÿ' -]+$")

mcp = FastMCP("tutor-pronuncia")


class EntradaInvalida(ValueError):
    pass


def validar(texto: str) -> str:
    """Rejeita texto vazio, muito longo ou com símbolos."""
    texto = (texto or "").strip()
    if not texto:
        raise EntradaInvalida("A palavra está vazia.")
    if len(texto) > MAX_TAMANHO:
        raise EntradaInvalida(f"A palavra tem mais de {MAX_TAMANHO} caracteres.")
    if not PADRAO_PALAVRA.match(texto):
        raise EntradaInvalida("Use apenas letras, espaço, hífen ou apóstrofo.")
    return texto


def _conexao() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS palavras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            portugues TEXT,
            ingles TEXT NOT NULL,
            ipa TEXT,
            criado_em TEXT NOT NULL
        )"""
    )
    return conn


@mcp.tool()
def ipa_da_palavra(palavra: str) -> dict:
    """Retorna a transcrição IPA (inglês americano) de uma palavra ou frase em inglês."""
    try:
        palavra = validar(palavra).lower()
    except EntradaInvalida as e:
        return {"erro": str(e)}
    ipa = eng_to_ipa.convert(palavra)
    if "*" in ipa:
        desconhecidas = [p.rstrip("*") for p in ipa.split() if p.endswith("*")]
        return {
            "erro": "Palavra não encontrada no dicionário CMU.",
            "palavras_desconhecidas": desconhecidas,
        }
    return {"palavra": palavra, "ipa": f"/{ipa}/"}


@mcp.tool()
def contar_silabas(palavra: str) -> dict:
    """Retorna o número de sílabas e a posição da sílaba tônica de uma palavra em inglês."""
    try:
        palavra = validar(palavra).lower()
    except EntradaInvalida as e:
        return {"erro": str(e)}
    fonemas = pronouncing.phones_for_word(palavra)
    if not fonemas:
        return {"erro": "Palavra não encontrada no dicionário CMU."}
    stress = pronouncing.stresses(fonemas[0])
    tonica = stress.index("1") + 1 if "1" in stress else None
    return {
        "palavra": palavra,
        "silabas": pronouncing.syllable_count(fonemas[0]),
        "silaba_tonica": tonica,
        "fonemas_arpabet": fonemas[0],
    }


@mcp.tool()
def rimas_da_palavra(palavra: str) -> dict:
    """Retorna até 10 palavras em inglês que rimam com a palavra informada."""
    try:
        palavra = validar(palavra).lower()
    except EntradaInvalida as e:
        return {"erro": str(e)}
    if not pronouncing.phones_for_word(palavra):
        return {"erro": "Palavra não encontrada no dicionário CMU."}
    return {"palavra": palavra, "rimas": pronouncing.rhymes(palavra)[:10]}


@mcp.tool()
def salvar_palavra(ingles: str, portugues: str = "", ipa: str = "") -> dict:
    """Grava no histórico do aluno a palavra em inglês, a tradução em português e o IPA."""
    try:
        ingles = validar(ingles).lower()
        portugues = validar(portugues).lower() if portugues.strip() else ""
    except EntradaInvalida as e:
        return {"erro": str(e)}
    with _conexao() as conn:
        conn.execute(
            "INSERT INTO palavras (portugues, ingles, ipa, criado_em) VALUES (?, ?, ?, ?)",
            (portugues, ingles, ipa[:80], datetime.now().isoformat(timespec="seconds")),
        )
    log.info("Palavra salva: %s", ingles)
    return {"ok": True, "ingles": ingles}


@mcp.tool()
def listar_palavras() -> dict:
    """Lista as 50 palavras mais recentes do histórico do aluno."""
    with _conexao() as conn:
        linhas = conn.execute(
            "SELECT portugues, ingles, ipa, criado_em FROM palavras "
            "ORDER BY id DESC LIMIT 50"
        ).fetchall()
    return {
        "palavras": [
            {"portugues": p, "ingles": i, "ipa": ipa, "criado_em": c}
            for p, i, ipa, c in linhas
        ]
    }


@mcp.resource("pronuncia://regras/th")
def regras_th() -> str:
    """Regras de pronúncia do TH (/θ/ e /ð/) para brasileiros."""
    texto = ARQUIVO_REGRAS.read_text(encoding="utf-8")
    blocos = [b for b in texto.split("## ") if b.startswith("TH")]
    return "\n\n".join(b.strip() for b in blocos)


@mcp.prompt()
def tutor_pronuncia(palavra: str) -> str:
    """Prompt para explicar a pronúncia de uma palavra a um brasileiro."""
    return (
        f"Explique como um brasileiro deve pronunciar '{palavra}' em inglês. "
        "Use a tool ipa_da_palavra para obter o IPA, dê a pronúncia aportuguesada, "
        "uma dica sobre o som mais difícil e uma frase de exemplo."
    )


if __name__ == "__main__":
    mcp.run()
