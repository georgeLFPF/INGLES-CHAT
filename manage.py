"""Gerencia os containers do Tutor de Pronúncia usando o Docker SDK para Python.

Uso:
    python manage.py start   # baixa as imagens, constrói a aplicação e sobe os containers
    python manage.py stop    # para e remove os containers (volumes são mantidos)
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path

import docker
from docker.errors import APIError, BuildError, DockerException, NotFound
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("manage")

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")
REDE = "tutor-net"
VOLUME_MODELOS = "tutor_ollama_models"
VOLUME_DADOS = "tutor_app_data"
IMAGEM_OLLAMA = "ollama/ollama:latest"
IMAGEM_APP = "tutor-pronuncia-app"
CONTAINER_OLLAMA = "tutor-ollama"
CONTAINER_APP = "tutor-app"

MODELO_CHAT = os.getenv("OLLAMA_MODEL", "llama3.1")
MODELO_ANALISE = os.getenv("OLLAMA_ANALYSIS_MODEL", "llama3.2")
MODELO_EMBEDDING = os.getenv("HF_EMBED_MODEL", "Xenova/paraphrase-multilingual-MiniLM-L12-v2")


def _rede(client: docker.DockerClient):
    try:
        return client.networks.get(REDE)
    except NotFound:
        log.info("Criando rede %s", REDE)
        return client.networks.create(REDE, driver="bridge")


def _volume(client: docker.DockerClient, nome: str) -> None:
    try:
        client.volumes.get(nome)
    except NotFound:
        log.info("Criando volume %s", nome)
        client.volumes.create(nome)


def _container(client: docker.DockerClient, nome: str):
    try:
        return client.containers.get(nome)
    except NotFound:
        return None


def subir_ollama(client: docker.DockerClient):
    container = _container(client, CONTAINER_OLLAMA)
    if container is None:
        log.info("Baixando imagem %s (pode demorar)...", IMAGEM_OLLAMA)
        client.images.pull(IMAGEM_OLLAMA)
        log.info("Criando container %s", CONTAINER_OLLAMA)
        container = client.containers.run(
            IMAGEM_OLLAMA,
            name=CONTAINER_OLLAMA,
            detach=True,
            ports={"11434/tcp": 11434},
            volumes={VOLUME_MODELOS: {"bind": "/root/.ollama", "mode": "rw"}},
            network=REDE,
            restart_policy={"Name": "unless-stopped"},
        )
    else:
        if container.status != "running":
            log.info("Iniciando container %s", CONTAINER_OLLAMA)
            container.start()
        # Um container criado por outro meio (ex.: docker compose) pode estar em outra rede.
        container.reload()
        if REDE not in container.attrs["NetworkSettings"]["Networks"]:
            client.networks.get(REDE).connect(container)
    return container


def esperar_ollama(container, tentativas: int = 30) -> None:
    log.info("Aguardando o Ollama ficar pronto...")
    for _ in range(tentativas):
        if container.exec_run("ollama list").exit_code == 0:
            return
        time.sleep(2)
    raise RuntimeError("O Ollama não respondeu a tempo.")


def baixar_modelos(container) -> None:
    # O modelo de embeddings vem do Hugging Face e é baixado pela própria aplicação.
    for modelo in dict.fromkeys((MODELO_CHAT, MODELO_ANALISE)):
        log.info("Baixando modelo %s (só demora na primeira vez)...", modelo)
        resultado = container.exec_run(f"ollama pull {modelo}")
        if resultado.exit_code != 0:
            raise RuntimeError(
                f"Falha ao baixar {modelo}: {resultado.output.decode(errors='replace')}"
            )


def construir_app(client: docker.DockerClient) -> None:
    log.info("Construindo imagem %s...", IMAGEM_APP)
    try:
        _, logs = client.images.build(path=str(BASE_DIR), tag=IMAGEM_APP, rm=True)
    except BuildError as e:
        for linha in e.build_log:
            if texto := linha.get("stream", "").strip():
                log.info("  %s", texto)
        # Sem isso o container antigo continuaria rodando o código desatualizado.
        raise RuntimeError(f"Falha ao construir a imagem da aplicação: {e.msg}") from e
    for linha in logs:
        if texto := linha.get("stream", "").strip():
            log.info("  %s", texto)


def verificar_app(client: docker.DockerClient, tentativas: int = 60) -> None:
    """Espera o Streamlit responder e confere, de dentro do container, se ele enxerga o Ollama."""
    log.info("Aguardando o Streamlit ficar pronto...")
    container = client.containers.get(CONTAINER_APP)
    for _ in range(tentativas):
        container.reload()
        if container.status in ("exited", "dead"):
            break
        saude = container.exec_run(
            ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health')"]
        )
        if saude.exit_code == 0:
            break
        time.sleep(2)
    else:
        raise RuntimeError("O Streamlit não respondeu a tempo. Veja: docker logs tutor-app")

    if container.status != "running":
        logs = container.logs(tail=40).decode(errors="replace")
        raise RuntimeError(f"O container {CONTAINER_APP} parou ao iniciar. Últimos logs:\n{logs}")

    # Mesma checagem que o agente faz ao abrir a página, mas aqui o erro aparece no terminal.
    teste = container.exec_run(
        ["python", "-c", "from agent import _cliente_ollama, verificar_modelos, MODELO_CHAT; "
         "from analisador import MODELO_ANALISE; "
         "verificar_modelos(_cliente_ollama(), MODELO_CHAT, MODELO_ANALISE)"],
        workdir="/app",
    )
    if teste.exit_code != 0:
        raise RuntimeError(
            f"A aplicação não conseguiu falar com o Ollama:\n{teste.output.decode(errors='replace')}"
        )
    log.info("Streamlit conectado ao Ollama (%s, %s).", MODELO_CHAT, MODELO_ANALISE)


def subir_app(client: docker.DockerClient) -> None:
    # Recria sempre, para usar a imagem recém-construída.
    if antigo := _container(client, CONTAINER_APP):
        antigo.remove(force=True)
    log.info("Criando container %s", CONTAINER_APP)
    client.containers.run(
        IMAGEM_APP,
        name=CONTAINER_APP,
        detach=True,
        ports={"8501/tcp": 8501},
        environment={
            "OLLAMA_HOST": f"http://{CONTAINER_OLLAMA}:11434",
            "OLLAMA_MODEL": MODELO_CHAT,
            "OLLAMA_ANALYSIS_MODEL": MODELO_ANALISE,
            "HF_EMBED_MODEL": MODELO_EMBEDDING,
            "HF_TOKEN": os.getenv("HF_TOKEN", ""),
            "HF_HOME": "/app/storage/huggingface",
            "OLLAMA_API_KEY": os.getenv("OLLAMA_API_KEY", ""),
            "DB_PATH": "/app/storage/progresso.db",
            "CHROMA_DIR": "/app/storage/.chroma",
        },
        volumes={VOLUME_DADOS: {"bind": "/app/storage", "mode": "rw"}},
        network=REDE,
        restart_policy={"Name": "unless-stopped"},
    )


def start(client: docker.DockerClient) -> None:
    _rede(client)
    _volume(client, VOLUME_MODELOS)
    _volume(client, VOLUME_DADOS)
    ollama = subir_ollama(client)
    esperar_ollama(ollama)
    baixar_modelos(ollama)
    construir_app(client)
    subir_app(client)
    verificar_app(client)
    log.info("\nPronto! Acesse http://localhost:8501")


def stop(client: docker.DockerClient) -> None:
    for nome in (CONTAINER_APP, CONTAINER_OLLAMA):
        if container := _container(client, nome):
            log.info("Removendo container %s", nome)
            container.remove(force=True)
    log.info("Containers parados. Os volumes (modelos e histórico) foram mantidos.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Gerencia os containers do Tutor de Pronúncia.")
    comandos = parser.add_subparsers(dest="comando", required=True, metavar="{start,stop}")
    comandos.add_parser("start", help="baixa as imagens, constrói a aplicação e sobe os containers")
    comandos.add_parser("stop", help="para e remove os containers (volumes são mantidos)")
    args = parser.parse_args()

    try:
        client = docker.from_env()
        client.ping()
    except DockerException as e:
        log.error("Não foi possível conectar ao Docker. O Docker Desktop está aberto?\n%s", e)
        return 1

    try:
        {"start": start, "stop": stop}[args.comando](client)
    except (APIError, DockerException, RuntimeError) as e:
        log.error("Erro: %s", e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
